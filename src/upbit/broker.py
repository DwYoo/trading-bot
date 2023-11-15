import time
import uuid
import jwt
from aiohttp import ClientSession, ClientTimeout

from base.OrderSheet import OrderSheet
from base.Broker import Broker
from utils.logger import trade_logger

# Create a Broker subclass specific to UpbitKrw
class UpbitKrwBroker(Broker):
    def __init__(self, api_key: str, secret_key: str):
        """
        Initialize the UpbitKrwBroker.

        :param api_key: API key for authentication.
        :param secret_key: Secret key for authentication.
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_endpoint = "https://api.upbit.com/v1/orders"

    async def aplace_order(self, order_sheet: OrderSheet):
        """
        Place an order using the provided OrderSheet.

        :param order_sheet: An instance of the OrderSheet to use for placing the order.
        """
        # Create and send an order request
        time1 = time.time()
        params = self._set_order_params(order_sheet)
        query_string = self._set_query_string(params)
        headers = self._set_headers(query_string)
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        try:
            response = await self._acall_api("POST", self.base_endpoint, query_string, headers, data=params)
            time2 = time.time()
            message = f"Order placed on {time2}. Took {time2 - time1} seconds."
            trade_logger.info(message)
            trade_logger.info(response)
            order_sheet.is_successful = True
            order_sheet.timestamp = time2
            order_sheet.exchange_order_id = str(response['uuid'])
            return order_sheet
        except Exception as e:
            message = f"Error in creating order in Upbit Krw: {e}"
            trade_logger.error(message)
            return order_sheet

    async def acancel_order_by_id(self, order_id:str) -> dict:
        query_string = f'uuid={order_id}'
        headers = self._set_headers(query_string)
        try:
            response = await self._acall_api("DELETE",  "https://api.upbit.com/v1/order", query_string, headers)
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
        price_dict = {
            2000000: 1000,
            1000000: 500,
            500000: 100,
            100000: 50,
            10000: 10,
            1000: 5,
            100: 1,
            10: 0.1,
            1: 0.01,
            0.1: 0.001
        }
        for key in sorted(price_dict.keys(), reverse=True):
            if price >= key:
                return price_dict[key]
        return 0.0001

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

    def _set_headers(self, query_string=None) -> dict:
        """
        Set the HTTP headers for the API request.

        :param query_string: The query string to include in the headers.
        :return: HTTP headers.
        """
        payload = {'access_key': self.api_key, 'nonce': str(uuid.uuid4())}
        if query_string:
            payload['query'] = query_string
        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {'Authorization': authorization}
        return headers
