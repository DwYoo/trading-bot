import asyncio
from abc import abstractmethod
from trade.order_sheet import OrderSheet

class Trader:
    @abstractmethod
    async def aplace_order(order_sheet:OrderSheet):
        pass