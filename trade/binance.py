
import hmac
import time
import hashlib
import asyncio
import requests
from aiohttp import ClientSession, ClientTimeout

from trade.order_sheet import OrderSheet
from trade.base import Trader
from utils.logger import trade_logger

def fetch_symbols_and_tick_info():
    symbol_data = fetch_symbol_data()
    return _process_symbol_data(symbol_data)

def fetch_symbol_data():
    endpoint  = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    response = requests.get(endpoint)
    symbol_data = response.json()
    return symbol_data

def _process_symbol_data(raw_symbol_data):
    tick_info = {}
    symbols = []
    for information in raw_symbol_data['symbols']:
        if information["quoteAsset"] == "USDT" and information["contractType"] == "PERPETUAL":
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

class BinanceUsdmTrader(Trader):
    def __init__(self, api_key:str, secret_key:str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_endpoint = "https://fapi.binance.com/fapi/v1/order"

    async def aplace_order(self, order_sheet: OrderSheet):
        params = self._set_order_params(order_sheet)
        time1 = time.time()
        trade_logger.info(f"Placing order in Binance USDM:\n"+ str(order_sheet))
        try:
            retries, max_retries =0, 3
            response = await self._acall_api("POST", self.base_endpoint, params)
            while response is None:
                retries += 1
                response = await self._acall_api("POST", self.base_endpoint, params)
                if retries > max_retries:
                    message = f"Failed to place order in Binance USDM: {response}"
                    trade_logger.error(message)
                    order_sheet.is_successful = False
                    return False
            time2 = time.time()
            message = f"Order placed on {time2}. Took {time2-time1}." 
            trade_logger.info(response)
            order_sheet.is_successful = True
            order_sheet.executed_time = time2
            order_sheet.order_id = str(response['orderId'])
        except Exception as e:
            message = f"Error while creating order in Binance USDM: {e}"
            trade_logger.error(message)

    async def acancel_order(self, order_sheet: OrderSheet):
        trade_logger.info(f"Cancelling order in Binance USDM:\n"+ str(order_sheet))
        try:
            params = {
                'symbol': order_sheet.symbol + 'USDT',
                'orderId': order_sheet.order_id,
                'recvWindow': 5000,
                'timestamp': self._set_timestamp(),
            }
            response = await self._acall_api("DELETE", self.base_endpoint, params)
            trade_logger.info(response)
        except Exception as e:
            message = f"Error while cancelling order: {e}"
            trade_logger.error(message)

    async def acancel_order_by_symbol(self, symbol:str):
        trade_logger.info(f"Cancelling orders in Binance USDM for {symbol}")
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


    def _set_order_params(self, order_sheet:OrderSheet) -> dict:
        params = {}
        symbol, side, qty, price, order_type = order_sheet.symbol, order_sheet.side, order_sheet.qty, order_sheet.price, order_sheet.order_type
        min_qty = tick_info[symbol]['min_qty']
        tick_size = tick_info[symbol]['tick_size']
        min_qty_decimal_places = self._get_decimal_places(min_qty)
        tick_size_decimal_places = self._get_decimal_places(tick_size)
        qty = float(format(qty, f".{min_qty_decimal_places}f"))
        price = float(format(price, f".{tick_size_decimal_places}f"))
        params = {'symbol': symbol + 'USDT', 
                  'side': side.upper(), 
                  'type': order_type.upper(), 
                  'quantity': str(qty), 
                  'recvWindow': 5000, 
                  'timestamp': self._set_timestamp(), 
                  'reduceOnly': order_sheet.reduce_only}
        if order_type == 'limit':
            params['timeInForce'] = 'GTC'
            params['price'] = str(price)
        return params

    def _get_decimal_places(self, num):
        if num < 1.0:
            return len(str(num).split('.')[-1])
        else:
            return len(str(num).split('.')[0]) -1
        
    async def _acall_api(self, method:str, endpoint:str, params:dict):
        query_string = self._set_query_string(params)
        signature = self._set_signature(query_string)
        headers = self._set_headers()
        timeout = ClientTimeout(total=1)
        async with ClientSession(timeout=timeout) as session:
            async with session.request(method, f"{endpoint}?{query_string}&signature={signature}", headers=headers) as res:
                return await res.json()

    def _set_signature(self, query_string: dict) -> str:
        signature = hmac.new(self.secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return signature

    def _set_headers(self):
        headers = {
            'X-MBX-APIKEY': self.api_key,
        }
        return headers
    
    def _set_timestamp(self):
        timestamp = int(time.time() * 1000)
        return timestamp
    
