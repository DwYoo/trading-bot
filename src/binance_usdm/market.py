import websockets
import asyncio
import json
import requests 

from base.Market import Market
from utils.logging import market_logger

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
    endpoint = "https://fapi.binance.com/fapi/v1/exchangeInfo"
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

BINANCE_USDM_SYMBOLS, BINANCE_USDM_TICK_INFO = fetch_symbols_and_tick_info()

class BinanceUsdmMarket(Market):
    def __init__(self, symbols: list, order_book_depth: int):
        """
        Initialize a Binance USDM Market instance.

        :param symbols: List of symbols to track.
        :param order_book_depth: Depth of the order book to track.
        """
        self.symbols = symbols
        self.order_book_depth = order_book_depth
        self.order_book = {symbol: {} for symbol in symbols}
    
    def get_order_book(self) -> dict:
        """
        Get the order book for all symbols.

        :return: The order book for all symbols.
        """
        return self.order_book

    async def aconnect(self):
        """
        Connect to the Binance USDM market and start streaming data for multiple symbols.
        """
        market_logger.info("Starting Binance USDM market stream")
        await asyncio.gather(*[self.aconnect_to_symbol(symbol) for symbol in self.symbols])

    async def aconnect_to_symbol(self, symbol: str):
        """
        Connect to a specific symbol on the Binance USDM market and stream its data.

        :param symbol: The symbol to connect to.
        """
        endpoint = f"wss://fstream.binance.com/ws/{symbol.lower()}usdt@depth5@100ms"
        try:
            async with websockets.connect(endpoint) as websocket:
            # Ping 메시지를 보내는 작업을 백그라운드에서 실행합니다.
                asyncio.create_task(self.ping(websocket))
                # Run the ping message in the background.
                asyncio.create_task(self._ping(websocket))
                await websocket.send(json.dumps({
                    "method": "SUBSCRIBE",
                    "params": [
                        f"{symbol.upper()}USDT@depth5@100ms"
                    ],
                    "id": 1
                }))
                async for message in websocket:
                    data = json.loads(message)
                    symbol_data = self._process_data(data)
                    self.market_data[symbol] = symbol_data
        except Exception as e:
            message = f"Error while connecting to {symbol}: {e}"
            market_logger.error(message)

    def _process_data(self, raw_data) -> dict:
        """
        웹소켓에서 받은 데이터를 변환
        """
    async def _ping(self, websocket):
        
        while True:
            await asyncio.sleep(1800)  # Send a ping message every 30 minutes.
            await websocket.ping()

    def _process_data(self, raw_data:json) -> dict:
        """
        Process raw data received from Binance WebSocket into a structured format.
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
