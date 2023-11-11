from pydantic import BaseModel
from typing import Optional, Literal

class OrderSheet(BaseModel):
    id : Optional[float] = 0
    exchange : str
    symbol : str
    side : str
    price : Optional[float] = 0
    qty : float
    order_type : Literal["limit", "market"] = 'limit'
    reduce_only : Optional[str] = False
    created_time : Optional[float] = 0
    is_successful : Optional[bool] = False
    order_id: Optional[float] = 0
    executed_time : Optional[float] = 0


    def __str__(self):
        return (f"order_id: {self.order_id}\n"
                f"exchange_name: {self.exchange}\n"
                f"symbol: {self.symbol}\n"
                f"side: {self.side}\n"
                f"price: {self.price}\n"
                f"qty: {self.qty}\n"
                f"order_type: {self.order_type}\n"
                f"reduce_only: {self.reduce_only}\n"
                f"result: {self.is_successful}\n")