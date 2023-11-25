import websockets
import asyncio
import json
import requests 

from base.Market import Market
from utils.logger import market_logger

def fetch_symbols_and_tick_info() -> tuple[list[str], dict]:
    """
    Fetch symbols and tick size information from the Phemex API.

    :return: A tuple containing the list of symbols and a dictionary of tick size information.
    """
    symbol_data = fetch_symbol_data()
    return _process_symbol_data(symbol_data)

def fetch_symbol_data():
    """
    Fetch symbol data from the Phemex API.

    :return: Raw symbol data from the Phemex API.
    """
    endpoint = "https://api.phemex.com/public/products"
    response = requests.get(endpoint)
    symbol_data_list = response.json()['data']['products']
    futures = [symbol_data for symbol_data in symbol_data_list if symbol_data['type'] == 'Perpetual']
    return futures

def _process_symbol_data(raw_symbol_data):
    """
    Process raw symbol data and extract symbols and tick size information.

    :param raw_symbol_data: Raw symbol data from the Phemex API.
    :return: A tuple containing the list of symbols and a dictionary of tick size information.
    """
    tick_info = {}
    symbols = []
    for information in raw_symbol_data['symbol']:
        if information["quoteCurrency"] == "USD":
            symbol = information['symbol'].replace('USD', '')
            symbols.append(symbol)
            tick_size = information['tickSize']
            tick_info[symbol] = {'tick_size': tick_size}
    return symbols, tick_info

Phemex_Perpetual_SYMBOLS, Phemex_Perpetual_TICK_INFO = fetch_symbols_and_tick_info()

class PhemexPerpetualMarket(Market):
    def __init__(self, symbols: list, order_book_depth: int):
        """
        Initialize a Phemex Perpetual Market instance.

        :param symbols: List of symbols to track.
        :param order_book_depth: Depth of the order book to track.
        """
        self.symbols = symbols
        self.order_book_depth = order_book_depth
        self.order_book = {symbol: {} for symbol in symbols}

    async def aconnect(self):
        """
        Connect to the Phemex Perpetual market and start streaming data for multiple symbols.
        """
        market_logger.info("Starting Phemex Perpetual market stream")
        await asyncio.gather(*[self.aconnect_to_symbol(symbol) for symbol in self.symbols])

    async def aconnect_to_symbol(self, symbol: str):
        """
        Connect to a specific symbol on the Phemex Perpetual market and stream its data.

        :param symbol: The symbol to connect to.
        """
        endpoint = f"wss://ws.phemex.com"
        try:
            async with websockets.connect(endpoint) as websocket:
                # Ping 메시지를 보내는 작업을 백그라운드에서 실행합니다.
                asyncio.create_task(self._ping(websocket))
                await websocket.send(json.dumps({
                    "id": 0,
                    "method": "orderbook.subscribe",
                    "params": [
                        symbol.upper() + 'USD'
                    ]
                }))
                async for message in websocket:
                    data = json.loads(message)
                    symbol_data = self._process_data(data)
                    self.order_book[symbol] = symbol_data
        except Exception as e:
            message = f"Error while connecting to {symbol}: {e}"
            market_logger.error(message)

    async def _ping(self, websocket):
        while True:
            await asyncio.sleep(5)  # Send a ping message every 30 minutes.
            await websocket.ping()

    def _process_data(self, raw_data:json) -> dict:
        """
        Process raw data received from Phemex WebSocket into a structured format.
        :param raw_data: Raw data received from the WebSocket.
        :return: Processed symbol data.
        """
        symbol_data = {}
        asks = raw_data.get('a', [])
        bids = raw_data.get('b', [])
        update_time = raw_data.get('E', None)
        if asks and bids and update_time:
            symbol_data['update_time'] = float(update_time) / 1000
            for i in range(self.order_book_depth):
                symbol_data[f"ask_{i+1}"] = float(asks[i][0])
                symbol_data[f"bid_{i+1}"] = float(bids[i][0])
                symbol_data[f"ask_{i+1}_qty"] = float(asks[i][1])
                symbol_data[f"bid_{i+1}_qty"] = float(bids[i][1])
            return symbol_data
        else:
            return {}
