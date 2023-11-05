import websockets
import asyncio
import json

from base.market import Market
from utils.logging import market_logger  

class UpbitKrwMarket(Market):
    def __init__(self, symbols:list, order_book_depth:int):
        self.symbols = symbols
        self.order_book_depth = order_book_depth
        self.market_data = {symbol: {} for symbol in symbols}

    async def aconnect(self):       
        market_logger.info(f"Starting Upbit KRW market stream")
        if len(self.symbols) < 5:
            tasks = [self.aconnect_to_symbols(self.symbols)]
        else:
            tasks = []
            batch_size = (len(self.symbols) // 4) + 1
            for i in range(3):
                tasks.append(self.aconnect_to_symbols(self.symbols[batch_size*i:batch_size*(i+1)]))
            tasks.append(self.aconnect_to_symbols(self.symbols[batch_size*3:]))
        await asyncio.gather(*tasks)

    async def aconnect_to_symbols(self, symbols:list[str]):
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
                    self.market_data[symbol] = self._process_data(raw_data)
        except Exception as e:
            market_logger.error(f"Failed to stream upbit order book : {e}. Reconnecting...")
            await asyncio.sleep()  # 잠시 대기 후 재시도
            await self.aconnect_to_symbols(symbols)

    def _process_data(self, raw_data:json) -> dict:
        #업비트 웹소켓에서 받은 데이터를 변환
        symbol_data = {}
        try:
            update_time = float(raw_data['tms'])/1000
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