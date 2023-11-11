import websockets
import asyncio
import json

from markets.base import Market
from utils.logger import market_logger

class BinanceUsdmMarket(Market):
    def __init__(self, symbols: list, order_book_depth: int):
        """
        Initialize a Binance USDM Market instance.

        :param symbols: List of symbols to track.
        :param order_book_depth: Depth of the order book to track.
        """
        self.symbols = symbols
        self.order_book_depth = order_book_depth
        self.market_data = {symbol: {} for symbol in symbols}

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

    async def _ping(self, websocket):
        """
        Send a ping message to the WebSocket connection at regular intervals.

        :param websocket: The WebSocket connection.
        """
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
