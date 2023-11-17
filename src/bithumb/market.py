import websockets
import asyncio
import json
import requests
import time
import uuid
import jwt
from aiohttp import ClientSession, ClientTimeout

from base.Market import Market
from utils.logger import market_logger  

def fetch_symbols():
    pass
    
BITHUMB_SYMBOLS = fetch_symbols()

class BithumbKrwMarket(Market):
    non_working_symbols = []

    def __init__(self, symbols: list, order_book_depth: int):
        """
        Initialize an Bithumb KRW Market instance.

        :param symbols: List of symbols to track.
        :param order_book_depth: Depth of the order book to track.
        """
        self.symbols = symbols
        self.order_book_depth = order_book_depth
        self.order_book = {symbol: {} for symbol in symbols}
    
    def get_non_working_symbols(self) -> list:
        """
        Get the list of non working symbols.

        :return: The list of non working symbols.
        """
        return self.non_working_symbols
    
    async def aconnect(self):       
        """
        Connect to the Bithumb KRW market and start streaming data for multiple symbols.
        """
        message = "Starting Bithumb KRW market stream"
        market_logger.info(message)
        tasks = []
        for symbol in self.symbols:
                tasks.append(self.aconnect_to_symbols([symbol]))
        # tasks.append(self.afetch_non_working_symbols())
        await asyncio.gather(*tasks)

    async def aconnect_to_symbols(self, symbols: list[str]):
        """
        Connect to a specific set of symbols on the Bithumb KRW market and stream their data.

        :param symbols: List of symbols to connect to.
        """
        endpoint = "wss://pubwss.bithumb.com/pub/ws"
        try:
            
            async with websockets.connect(endpoint) as websocket:
                subscribe_data = json.dumps(
                    {
                        "type": "orderbooksnapshot",
                        "symbols": [f"{symbol}_KRW" for symbol in symbols],
                    },
                )
                await websocket.send(subscribe_data)
                async for response in websocket:
                    json_response = json.loads(response)
                    print(json_response)
                    raw_data = json_response['content']
                    symbol = raw_data['symbol'].replace('_KRW', '')
                    self.order_book[symbol] = self._process_data(raw_data)
        except Exception as e:
            message = f"Failed to stream Bithumb order book: {e}. Reconnecting..."
            market_logger.error(message)
            await asyncio.sleep(1)  # Wait for a moment and then retry
            await self.aconnect_to_symbols(symbols)

    def _process_data(self, raw_data: json) -> dict:
        """
        Process raw data received from the Bithumb WebSocket into a structured format.

        :param raw_data: Raw data received from the WebSocket.
        :return: Processed symbol data.
        """
        symbol_data = {}
        try:
            symbol_data['update_time'] = float(raw_data['datetime']) / 1000
            asks = raw_data['asks']
            bids = raw_data['bids']
            for i in range(self.order_book_depth):
                symbol_data[f"ask_{i+1}"] = float(asks[i][0])
                symbol_data[f"bid_{i+1}"] = float(bids[i][0])
                symbol_data[f"ask_{i+1}_qty"] = float(asks[i][1])
                symbol_data[f"bid_{i+1}_qty"] = float(bids[i][1])
            return symbol_data
        except Exception as e:
            return {}

    async def aprint_data(self, time_interval: int = 5):
        """
        Asynchronously print market data periodically.

        :param time_interval: Time interval in seconds between prints.
        """
        while True:
            print(self.order_book)
            print(self.non_working_symbols)
            await asyncio.sleep(time_interval)

    async def afetch_non_working_symbols(self) -> list:
        """
        미완성
        """
        try: 
            headers = self._set_headers()
            timeout = ClientTimeout(total=3)
            async with ClientSession(timeout=timeout) as session:
                async with session.request("GET", "https://api.bithumb.com/public/assetsstatus/ALL", headers=headers) as res:
                    symbol_status =  await res.json()
            non_working_symbols = [item['currency'] for item in symbol_status if item['wallet_state'] not in ['working', 'withdraw_only'] or item['block_state'] == 'inactive']
            self.non_working_symbols = non_working_symbols
            await asyncio.sleep(60)
        except Exception as e:
            message = f"Failed to fetch Bithumb non working symbols{e}"
            market_logger.error(message)

    def _set_headers(self):
        return {"accept": "application/json"}
