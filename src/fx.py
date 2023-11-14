import aiohttp
import asyncio
from utils.logger import market_logger

class FxMarket:
    def __init__(self):
        #Initializes usd_krw_rate
        self.usd_krw_rate = 1320

    def get_usd_krw_rate(self):
        #Returns usd_krw_rate
        return self.usd_krw_rate

    async def stream(self):
        """
        Asynchronously start streaming market data.
        This method creates tasks for connecting to the market and printing market data periodically.
        """
        task1 = asyncio.create_task(self.aconnect())
        await asyncio.sleep(10)
        task2 = asyncio.create_task(self._aprint_usd_krw_rate())
        await asyncio.gather(task1, task2)

    async def aconnect(self, time_interval:int = 300) -> None:
        #Updates self.usd_krw_rate
        headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        }
        url = 'https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD'
        timeout = aiohttp.ClientTimeout(total=1)
        while True:
            try: 
                async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                    async with session.get(url) as response:
                        data = await response.json()
                        self.usd_krw_rate = float(data[0]['basePrice'])   
                await asyncio.sleep(time_interval) # 5분마다 업데이트
            except Exception as e:
                message = f"Error while updating usd krw rate: {e}"
                market_logger.error(message)
                await asyncio.sleep(0.5)
                continue

    async def _aprint_usd_krw_rate(self, time_interval: int = 5):
        """
        Asynchronously print market data periodically.

        :param time_interval: Time interval in seconds between prints.
        """
        while True:
            print(self.usd_krw_rate)
            await asyncio.sleep(time_interval)