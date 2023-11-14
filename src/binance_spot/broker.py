import hmac
import time
import hashlib
import requests
from aiohttp import ClientSession, ClientTimeout

from base.OrderSheet import OrderSheet
from base.Broker import Broker
from utils.logger import trade_logger

def fetch_symbols_and_tick_info() -> tuple[list[str], dict]:
    """
    Fetch symbols and tick size information from the Binance API.

    :return: A tuple containing the list of symbols and a dictionary of tick size information.
    """
    symbol_data = fetch_symbol_data()
    return _process_symbol_data(symbol_data)

def fetch_symbol_data():
    """
    Fetch symbol data from the Binance API.

    :return: Raw symbol data from the Binance API.
    """
    endpoint = "https://api4.binance.com/api/v3/exchangeInfo"
    response = requests.get(endpoint)
    symbol_data = response.json()
    return symbol_data

def _process_symbol_data(raw_symbol_data):
    """
    Process raw symbol data and extract symbols and tick size information.

    :param raw_symbol_data: Raw symbol data from the Binance API.
    :return: A tuple containing the list of symbols and a dictionary of tick size information.
    """
    tick_info = {}
    symbols = []
    for information in raw_symbol_data['symbols']:
        if information["quoteAsset"] == "USDT":
            symbol = information['baseAsset']
            symbols.append(symbol)
            filters = information['filters']
            min_qty = None
            tick_size = None
            for f in filters:
                if f['filterType'] == 'LOT_SIZE':
                    min_qty = float(f['minQty'])
                elif f['filterType'] == 'PRICE_FILTER':
                    tick_size = float(f['tickSize'])
                tick_info[symbol] = {
                    'min_qty': min_qty,
                    'tick_size': tick_size
                }
    return symbols, tick_info

all_symbols, tick_info = fetch_symbols_and_tick_info()

class BinanceSpotBroker(Broker):
    def __init__(self, api_key: str, secret_key: str):
        """
        Initialize a Binance Spot Broker with API keys.

        :param api_key: The Binance API key.
        :param secret_key: The Binance API secret key.
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_endpoint = "https://api4.binance.com/api/v3/order"

    async def aplace_order(self, order_sheet: OrderSheet):
        """
        Place an order using the provided OrderSheet.

        :param order_sheet: An instance of the OrderSheet to use for placing the order.
        """
        params = self._set_order_params(order_sheet)
        time1 = time.time()
        trade_logger.info(f"Placing order in Binance Spot:\n" + str(order_sheet))
        try:
            retries, max_retries = 0, 3
            response = await self._acall_api("POST", self.base_endpoint, params)
            while response is None:
                retries += 1
                response = await self._acall_api("POST", self.base_endpoint, params)
                if retries > max_retries:
                    message = f"Failed to place order in Binance Spot: {response}"
                    trade_logger.error(message)
                    order_sheet.is_successful = False
                    return False
            time2 = time.time()
            message = f"Order placed on {time2}. Took {time2 - time1}."
            trade_logger.info(response)
            order_sheet.is_successful = True
            order_sheet.timestamp = time2
            order_sheet.exchange_order_id = str(response['orderId'])
            return order_sheet
        except Exception as e:
            message = f"Error while creating order in Binance Spot: {e}"
            trade_logger.error(message)
            return order_sheet

    async def acancel_order(self, order_sheet: OrderSheet):
        """
        Cancel an order using the provided OrderSheet.

        :param order_sheet: An instance of the OrderSheet to use for cancelling the order.
        """
        trade_logger.info(f"Cancelling order in Binance Spot:\n" + str(order_sheet))
        try:
            params = {
                'symbol': order_sheet.symbol + 'USDT',
                'orderId': order_sheet.id,
                'recvWindow': 5000,
                'timestamp': self._set_timestamp(),
            }
            response = await self._acall_api("DELETE", self.base_endpoint, params)
            trade_logger.info(response)
        except Exception as e:
            message = f"Error while cancelling order: {e}"
            trade_logger.error(message)

    async def acancel_order_by_symbol(self, symbol: str):
        """
        Cancel all open orders for a specific symbol.

        :param symbol: The symbol for which to cancel all open orders.
        """
        trade_logger.info(f"Cancelling orders in Binance Spot for {symbol}")
        endpoint = f"{self.base_endpoint}/allOpenOrders"
        params = {
            'symbol': symbol + 'USDT',
            'recvWindow': 5000,
            'timestamp': self._set_timestamp(),
        }
        try:
            response = await self._acall_api("DELETE", endpoint, params)
            message = f"All orders cancelled for {symbol}: {response}"
            trade_logger.info(message)
        except Exception as e:
            message = f"Error while cancelling all open orders for {symbol}: {e}"
            trade_logger.error(message)
        

    def _set_order_params(self, order_sheet: OrderSheet) -> dict:
        """
        Generate order parameters for placing an order.

        :param order_sheet: An instance of the OrderSheet to use for placing the order.
        :return: A dictionary of order parameters.
        """
        params = {}
        symbol, side, qty, qty_by_quote, price, order_type = order_sheet.symbol, order_sheet.side, order_sheet.qty, order_sheet.qty_by_quote, order_sheet.price, order_sheet.order_type
        min_qty = tick_info[symbol]['min_qty']
        tick_size = tick_info[symbol]['tick_size']
        min_qty_decimal_places = self._get_decimal_places(min_qty)
        tick_size_decimal_places = self._get_decimal_places(tick_size)
        price = float(format(price, f".{tick_size_decimal_places}f"))
        timestamp = self._set_timestamp()
        if qty != 0:
            qty = float(format(qty, f".{min_qty_decimal_places}f"))
            params = {'symbol': symbol + 'USDT',
                  'side': side.upper(),
                  'type': order_type.upper(),
                  'quantity': str(qty),
                  'recvWindow': 5000,
                  'timestamp': timestamp
                  }
        else: 
            qty_by_quote = float(format(qty_by_quote, f".1f"))
            params = {'symbol': symbol + 'USDT',
                  'side': side.upper(),
                  'type': order_type.upper(),
                  'quoteOrderQty': str(qty_by_quote),
                  'recvWindow': 5000,
                  'timestamp': timestamp
                  }

        if order_type == 'limit':
            params['timeInForce'] = 'GTC'
            params['price'] = str(price)
        return params


    def _get_decimal_places(self, num) -> int:
        """
        Determine the number of decimal places in a given number.

        :param num: The number for which to calculate the decimal places.
        :return: The number of decimal places.
        """
        if num < 1.0:
            return len(str(num).split('.')[-1])
        else:
            return len(str(num).split('.')[0]) - 1
        
    async def _acall_api(self, method: str, endpoint: str, params: dict):
        """
        Make an asynchronous API call to the specified endpoint.

        :param method: The HTTP method to use for the API call (e.g., "GET" or "POST").
        :param endpoint: The URL endpoint to call.
        :param params: The parameters to include in the API call.
        :return: The JSON response from the API call.
        """
        query_string = self._set_query_string(params)
        signature = self._set_signature(query_string)
        headers = self._set_headers()
        timeout = ClientTimeout(total=1)
        async with ClientSession(timeout=timeout) as session:
            async with session.request(method, f"{endpoint}?{query_string}&signature={signature}", headers=headers) as res:
                return await res.json()

    def _set_signature(self, query_string: str) -> str:
        """
        Generate an API signature for the given query string.

        :param query_string: The query string to be signed.
        :return: The generated API signature.
        """
        signature = hmac.new(self.secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return signature

    def _set_headers(self) -> dict:
        """
        Set the HTTP headers for the API request.

        :return: A dictionary containing the API headers.
        """
        headers = {
            'X-MBX-APIKEY': self.api_key,
        }
        return headers
    
    def _set_timestamp(self) -> int:
        """
        Generate a timestamp for the API request.

        :return: The generated timestamp.
        :rtype: int
        """
        timestamp = int(time.time() * 1000)
        return timestamp
