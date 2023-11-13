import asyncio
from abc import abstractmethod
import logging

class Market:
    order_book = {}

    def get_order_book(self) -> dict:
        """
        Get the order book for all symbols.

        :return: The order book for all symbols.
        """
        return self.order_book

    async def stream(self):
        """
        Asynchronously start streaming market data.
        This method creates tasks for connecting to the market and printing market data periodically.
        """
        task1 = asyncio.create_task(self.aconnect())
        await asyncio.sleep(10)
        task2 = asyncio.create_task(self.aprint_data())
        await asyncio.gather(task1, task2)

    @abstractmethod
    async def aconnect(self):
        """
        An abstract method for connecting to the market. Subclasses should implement this method to connect to a specific market.
        """
        pass

    async def aprint_data(self, time_interval: int = 5):
        """
        Asynchronously print market data periodically.

        :param time_interval: Time interval in seconds between prints.
        """
        while True:
            print(self.order_book)
            await asyncio.sleep(time_interval)

    async def ping(self, websocket, interval:int=1800):
        """
        Send a ping message to the WebSocket connection at regular intervals.

        :param websocket: The WebSocket connection.
        :param interval: Interval in seconds between ping messages. (default: 30 minutes)
        """
        while True:
            await asyncio.sleep(1800)  
            await websocket.ping()
