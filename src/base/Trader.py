import asyncio
from abc import abstractmethod
from base.OrderSheet import OrderSheet

class Trader:
    @abstractmethod
    async def aplace_order(order_sheet:OrderSheet):
        pass

    def _set_query_string(self, params: dict) -> str:
        query_string = '&'.join(["{}={}".format(key, params[key]) for key in params.keys()])
        return query_string