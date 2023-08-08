import websockets
import asyncio
import json

from markets.base import Market
from utils.logger import market_logger  



class UpbitKrwMarket(Market):
    def __init__(self, symbols:list, order_book_depth:int):
        self.symbols = symbols
        self.order_book_depth = order_book_depth
        self.market_stream = {symbol: {} for symbol in symbols}
        
    async def stream(self):       
        message = f"Starting Upbit KRW market stream"
        market_logger.info(message)
        if len(self.symbols) < 5:
            tasks = [self.stream_symbols(self.symbols)]
        else:
            tasks = []
            batch_size = (len(self.symbols) // 4) + 1
            for i in range(3):
                tasks.append(self.stream_symbols(self.symbols[batch_size*i:batch_size*(i+1)]))
            tasks.append(self.stream_symbols(self.symbols[batch_size*3:]))
        await asyncio.gather(*tasks)

    async def stream_symbols(self, symbols:list[str]):
        endpoint = "wss://api.upbit.com/websocket/v1"
        try:
            async with websockets.connect(endpoint) as websocket:
                subscribe_data = json.dumps([
                    {"ticket": "con"},
                    {
                        "type": "orderbook",
                        "codes": [f"KRW-{symbol}.{self.order_book_depth}"for symbol in symbols],
                        "isOnlySnapshot": "false",
                        "isOnlyRealtime": "true"
                    },
                    {"format": "SIMPLE"}
                ])
                await websocket.send(subscribe_data)
                async for response in websocket:
                    raw_data = json.loads(response)
                    symbol = raw_data['cd'].replace('KRW-', '')
                    symbol_data = self._process_data(raw_data)
                    self.market_stream[symbol] = symbol_data
        except Exception as e:
            message = f"Failed to stream upbit order book : {e}. Reconnecting..."
            market_logger.error(message)
            self.sleep()  # 잠시 대기 후 재시도
            await self.stream_symbols(symbols)

    async def _ping(self, websocket):
        while True:
            await asyncio.sleep(1800)  # 여기서는 30분마다 ping을 보냅니다.
            await websocket.ping()

    def _process_data(self, raw_data:json) -> dict:
        #업비트 웹소켓에서 받은 데이터를 변환
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