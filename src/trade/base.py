import asyncio
from abc import abstractmethod
from trade.order_sheet import OrderSheet

class Trader:
    @abstractmethod
    async def aplace_order(order_sheet: OrderSheet):
        """
        Abstract method for placing an order using an OrderSheet.

        :param order_sheet: An instance of the OrderSheet to use for placing the order.
        """
        pass

    def _set_query_string(self, params: dict) -> str:
        """
        Generate a query string from a dictionary of parameters.

        :param params: A dictionary of parameters to be included in the query string.
        :return: A query string with the formatted parameters.
        """
        query_string = '&'.join(["{}={}".format(key, params[key]) for key in params.keys()])
        return query_string
