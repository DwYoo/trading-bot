import websockets
import asyncio
import json

from markets.base import Market
from utils.logger import market_logger  

class UpbitKrwMarket(Market):
    def __init__(self, symbols: list, order_book_depth: int):
        """
        Initialize an Upbit KRW Market instance.

        :param symbols: List of symbols to track.
        :param order_book_depth: Depth of the order book to track.
        """
        self.symbols = symbols
        self.order_book_depth = order_book_depth
        self.market_data = {symbol: {} for symbol in symbols}

    async def aconnect(self):       
        """
        Connect to the Upbit KRW market and start streaming data for multiple symbols.
        """
        message = "Starting Upbit KRW market stream"
        market_logger.info(message)
        if len(self.symbols) < 5:
            tasks = [self.aconnect_to_symbols(self.symbols)]
        else:
            tasks = []
            batch_size = (len(self.symbols) // 4) + 1
            for i in range(3):
                tasks.append(self.aconnect_to_symbols(self.symbols[batch_size*i:batch_size*(i+1)]))
            tasks.append(self.aconnect_to_symbols(self.symbols[batch_size*3:]))
        await asyncio.gather(*tasks)

    async def aconnect_to_symbols(self, symbols: list[str]):
        """
        Connect to a specific set of symbols on the Upbit KRW market and stream their data.

        :param symbols: List of symbols to connect to.
        """
        endpoint = "wss://api.upbit.com/websocket/v1"
        try:
            async with websockets.connect(endpoint) as websocket:
                subscribe_data = json.dumps([
                    {"ticket": "con"},
                    {
                        "type": "orderbook",
                        "codes": [f"KRW-{symbol}.{self.order_book_depth}" for symbol in symbols],
                        "isOnlySnapshot": "false",
                        "isOnlyRealtime": "true"
                    },
                    {"format": "SIMPLE"}
                ])
                await websocket.send(subscribe_data)
                async for response in websocket:
                    raw_data = json.loads(response)
                    symbol = raw_data['cd'].replace('KRW-', '')
                    self.market_data[symbol] = self._process_data(raw_data)
        except Exception as e:
            message = f"Failed to stream Upbit order book: {e}. Reconnecting..."
            market_logger.error(message)
            await asyncio.sleep(1)  # Wait for a moment and then retry
            await self.aconnect_to_symbols(symbols)

    async def _ping(self, websocket):
        """
        Send a ping message to the WebSocket connection at regular intervals.

        :param websocket: The WebSocket connection.
        """
        while True:
            await asyncio.sleep(1800)  # Send a ping message every 30 minutes.
            await websocket.ping()

    def _process_data(self, raw_data: json) -> dict:
        """
        Process raw data received from the Upbit WebSocket into a structured format.

        :param raw_data: Raw data received from the WebSocket.
        :return: Processed symbol data.
        """
        symbol_data = {}
        try:
            update_time = float(raw_data['tms']) / 1000
            symbol_data['update_time'] = update_time
            for i in range(self.order_book_depth):
                obu = raw_data['obu'][i]
                symbol_data[f"ask{i+1}"] = float(obu['ap'])
                symbol_data[f"bid{i+1}"] = float(obu['bp'])
                symbol_data[f"ask{i+1}_qty"] = float(obu['as'])
                symbol_data[f"bid{i+1}_qty"] = float(obu['bs'])
            return symbol_data
        except Exception as e:
            return {}
