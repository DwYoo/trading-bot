import asyncio
from pydantic import BaseModel
from abc import abstractmethod

class Market:

    @abstractmethod
    async def stream(self):
        pass