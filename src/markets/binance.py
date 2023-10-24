import websockets
import asyncio
import json

from markets.base import Market
from utils.logger import market_logger

class BinanceUsdmMarket(Market):
    def __init__(self, symbols:list, order_book_depth:int):
        self.symbols = symbols
        self.order_book_depth = order_book_depth
        self.market_data = {symbol: {} for symbol in symbols}

    async def aconnect(self):
        market_logger.info("Starting Binance USDM market stream")
        await asyncio.gather(*[self.aconnect_to_symbol(symbol) for symbol in self.symbols])

    async def aconnect_to_symbol(self, symbol:str):
        endpoint = f"wss://fstream.binance.com/ws/{symbol.lower()}usdt@depth5@100ms"
        try:
            async with websockets.connect(endpoint) as websocket:
            # Ping 메시지를 보내는 작업을 백그라운드에서 실행합니다.
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
        while True:
            await asyncio.sleep(1800)  # 여기서는 30분마다 ping을 보냅니다.
            await websocket.ping()

    def _process_data(self, raw_data) -> dict:
        #바이낸스 웹소켓에서 받은 데이터를 변환
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