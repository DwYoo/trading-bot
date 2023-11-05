import asyncio
from abc import abstractmethod

class Market:
    market_data = {}

    async def stream(self):
        task1 = asyncio.create_task(self.aconnect())
        await asyncio.sleep(10)
        task2 = asyncio.create_task(self._aprint_market_data())
        await asyncio.gather(task1, task2)

    @abstractmethod
    async def aconnect(self):
        pass

    async def _aprint_market_data(self, time_interval:int=5):
        while True:
            print(self.market_data)
            await asyncio.sleep(time_interval)

    async def ping(self, websocket, interval:int=1800):
        """
        dafault: 30분마다 ping 보내기 (heartbeat)
        """
        while True:
            await asyncio.sleep(1800)  
            await websocket.ping()