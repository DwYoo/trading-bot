import time
import uuid
import base64
import hashlib
import jwt
import hmac
import urllib
from aiohttp import ClientSession, ClientTimeout
from pybithumb import Bithumb
import math

from base.OrderSheet import OrderSheet
from base.Broker import Broker
from utils.logger import trade_logger

# Create a Broker subclass specific to BithumbKrw
class BithumbKrwBroker(Broker):
    def __init__(self, api_key: str, secret_key: str):
        """
        Initialize the BithumbKrwBroker.

        :param api_key: API key for authentication.
        :param secret_key: Secret key for authentication.
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_endpoint = "https://api.bithumb.com/trade"

    async def aplace_order(self, order_sheet: OrderSheet) -> OrderSheet:
        """
        Place an order using the provided OrderSheet.

        :param order_sheet: An instance of the OrderSheet to use for placing the order.
        """
        # Create and send an order request
        # Params: OrderSheet
        # Returns: OrderSheet
        time1 = time.time()
        params = self._set_order_params(order_sheet)
        query_string = self._set_query_string(params)
        headers = self._set_headers(query_string)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        try:
            response = await self._acall_api("POST", self.base_endpoint, query_string, headers, data=params)
            time2 = time.time()
            order_sheet.is_successful = True
            order_sheet.exchange_order_id = str(response['uuid'])
            order_sheet.timestamp = time2
            order_sheet.time_took = time2 - time1
            return order_sheet
        except Exception as e:
            message = f"Error in creating order in Bithumb Krw: {e}"
            trade_logger.error(message)
            return order_sheet

    async def acancel_order_by_id(self, order_id:str) -> dict:
        query_string = f'uuid={order_id}'
        headers = self._set_headers(query_string)
        try:
            response = await self._acall_api("DELETE",  "https://api.Bithumb.com/v1/order", query_string, headers)
            message = f"Order cancelled for {order_id} : {response}"
            trade_logger.info(message)
            trade_logger.info(response)
            return response
        except Exception as e:
            message = f"Error while cancelling order: {e}"
            trade_logger.error(message)
            
    async def acancel_order_by_symbol(self, symbol) -> list:
        #특정 심볼에 대한 미체결 주문 취소
        responses = []
        orders = await self.afetch_open_orders_by_symbol(symbol)
        if orders != [] and orders != None:
            for order in orders:
                response = await self.acancel_order_by_id(order['uuid'])
                responses.append(response)
        trade_logger.info(f"Orders cancelled for {symbol}")
        trade_logger.info(responses)
        return responses
    
    async def afetch_open_orders_by_symbol(self, symbol:str) -> list:
        #특정 심볼에 대한 미체결 주문 조회
        params = {
            'market': 'KRW-'+symbol,  # 주문을 조회하려는 마켓 아이디
            'state': 'wait',  # 미체결 주문
        }
        query_string = self._set_query_string(params)
        headers = self._set_headers(query_string)
        try:
            response = await self._acall_api("GET", self.base_endpoint, query_string, headers)
            orders = []
            for order in response:
                orders.append(order)
            message = f"Order fetched for {symbol}: {response}"
            trade_logger.info(message)
            trade_logger.info(orders)
            return orders
        except Exception as e:
            message = f"Error in fetching order: {e}"
            trade_logger.error(message)

    def _set_order_params(self, order_sheet: OrderSheet) -> dict:
        """
        Set the parameters for creating an order based on the provided OrderSheet.

        :param order_sheet: An instance of the OrderSheet with order details.
        :return: A dictionary of order parameters.
        """
        symbol, side, qty, price, order_type = order_sheet.symbol, order_sheet.side, order_sheet.qty, order_sheet.price, order_sheet.order_type
        params = {
            'ord_type': order_type,
            'market': 'KRW-' + symbol,
            'side': 'bid' if side == 'buy' else 'ask'
        }
        if order_type == 'market':
            # Handle market orders
            if side == 'bid':
                order_type = 'price'
                price = float(round(price / self._set_price_unit(price)) * self._set_price_unit(price)) * qty
                params['price'] = str(price)
            if side == 'ask':
                params['volume'] = str(qty)
        elif order_type == 'limit':
            # Handle limit orders
            price = float(round(price / self._set_price_unit(price)) * self._set_price_unit(price))
            params['price'] = str(price)
            params['volume'] = str(qty)
        return params

    def _set_price_unit(self, price: float):
        """
        Determine the price unit based on the price value.

        :param price: The price value.
        :return: The price unit.
        """
        pass

    def _set_qty_unit(self, qty: float):
        try:
            unit = math.floor(unit * 10000) / 10000
            return unit
        except:
            return 0

    async def _acall_api(self, method: str, endpoint: str, params: dict, headers=None, data=None, time=2):
        """
        Make an asynchronous HTTP request to the API endpoint.

        :param method: The HTTP request method (GET, POST, DELETE, etc.).
        :param endpoint: The API endpoint URL.
        :param params: Dictionary of request parameters.
        :param headers: HTTP headers for the request.
        :param data: Request data for POST requests.
        :param time: Timeout for the request.
        :return: JSON response from the API.
        """
        timeout = ClientTimeout(total=time)
        async with ClientSession(timeout=timeout) as session:
            async with session.request(method, f"{endpoint}?{params}", headers=headers, data=data) as res:
                return await res.json()

    def _set_headers(self, path, **kwargs) -> dict:
        """
        Set the HTTP headers for the API request.

        :param query_string: The query string to include in the headers.
        :return: HTTP headers.
        """
        kwargs['endpoint'] = path
        nonce = str(int(time.time() * 1000))
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "Api-Key": self.api_key,
            "Api-Nonce": nonce,
            "Api-Sign": self._set_signature(path, nonce, **kwargs),
        }

        return headers

    def _set_signature(self, path, nonce, **kwargs):
        query_string = path + chr(0) + urllib.parse.urlencode(kwargs) + \
                       chr(0) + nonce
        h = hmac.new(self.secret_key, query_string.encode('utf-8'),
                     hashlib.sha512)
        return base64.b64encode(h.hexdigest().encode('utf-8'))