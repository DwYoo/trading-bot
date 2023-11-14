from pydantic import BaseModel
from typing import Optional, Literal

class OrderSheet(BaseModel):
    id : Optional[int] = 0
    exchange : str
    symbol : str
    side : str
    price : Optional[float] = 0
    qty : Optional[float] = 0
    qty_by_quote : Optional[float] = 0
    order_type : Literal["limit", "market"] = 'limit'
    reduce_only : Optional[str] = False
    timestamp : Optional[float] = 0
    is_successful : Optional[bool] = False
    exchange_order_id: Optional[float] = 0


    def __str__(self):
        return (f"id: {self.id}\n"
                f"exchange_name: {self.exchange}\n"
                f"symbol: {self.symbol}\n"
                f"side: {self.side}\n"
                f"price: {self.price}\n"
                f"qty: {self.qty}\n"
                f"qty_by_quote: {self.qty_by_quote}\n"
                f"order_type: {self.order_type}\n"
                f"reduce_only: {self.reduce_only}\n"
                f"timestamp: {self.timestamp}\n"
                f"result: {self.is_successful}\n"
                f"exchange_order_id: {self.exchange_order_id}\n")