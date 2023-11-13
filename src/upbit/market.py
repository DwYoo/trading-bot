import websockets
import asyncio
import json
import requests
import time
import uuid
import jwt
from aiohttp import ClientSession, ClientTimeout
import os


from base.Market import Market
from utils.logging import market_logger  

from dotenv import load_dotenv

load_dotenv()

UPBIT_API_KEY = os.getenv("UPBIT_API_KEY")
UPBIT_SECRET_KEY =  os.getenv("UPBIT_SECRET_KEY")


def fetch_symbols():
    try: 
        upbit_markets = fetch_markets()
        upbit_krw_symbols = [market["market"] for market in upbit_markets if "KRW" in market["market"]]
        upbit_krw_base_symbols = [symbol[4:] for symbol in upbit_krw_symbols]
        market_logger.info(f"Upbit KRW symbols: {upbit_krw_base_symbols}")
        return upbit_krw_base_symbols
    except Exception as e:
        message = f"Failed to fetch upbit symbols{e}"
        market_logger.error(message)
        time.sleep(0.5)
        return fetch_symbols()
    
def fetch_markets():
    endpoint = "https://api.upbit.com/v1/market/all"
    response = requests.get(endpoint)
    upbit_markets = json.loads(response.text)
    return upbit_markets        

UPBIT_SYMBOLS = fetch_symbols()

class UpbitKrwMarket(Market):
    non_working_symbols = []

    def __init__(self, symbols: list, order_book_depth: int):
        """
        Initialize an Upbit KRW Market instance.

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
        Connect to the Upbit KRW market and start streaming data for multiple symbols.
        """
        message = "Starting Upbit KRW market stream"
        market_logger.info(message)
        if len(self.symbols) < 5:
            tasks = [self.aconnect_to_symbols(self.symbols)]
        else:
            tasks = []
            batch_size = (len(self.symbols) // 4) + 1
            for i in range(3):
                tasks.append(self.aconnect_to_symbols(self.symbols[batch_size*i:batch_size*(i+1)]))
            tasks.append(self.aconnect_to_symbols(self.symbols[batch_size*3:]))
        tasks.append(self.afetch_non_working_symbols())
        await asyncio.gather(*tasks)

    async def aconnect_to_symbols(self, symbols: list[str]):
        """
        Connect to a specific set of symbols on the Upbit KRW market and stream their data.

        :param symbols: List of symbols to connect to.
        """
        endpoint = "wss://api.upbit.com/websocket/v1"
        try:
            async with websockets.connect(endpoint) as websocket:
                subscribe_data = json.dumps([
                    {"ticket": "con"},
                    {
                        "type": "orderbook",
                        "codes": [f"KRW-{symbol}.{self.order_book_depth}" for symbol in symbols],
                        "isOnlySnapshot": "false",
                        "isOnlyRealtime": "true"
                    },
                    {"format": "SIMPLE"}
                ])
                await websocket.send(subscribe_data)
                async for response in websocket:
                    raw_data = json.loads(response)
                    symbol = raw_data['cd'].replace('KRW-', '')
                    self.order_book[symbol] = self._process_data(raw_data)
        except Exception as e:
            message = f"Failed to stream Upbit order book: {e}. Reconnecting..."
            market_logger.error(message)
            await asyncio.sleep(1)  # Wait for a moment and then retry
            await self.aconnect_to_symbols(symbols)

    def _process_data(self, raw_data: json) -> dict:
        """
        Process raw data received from the Upbit WebSocket into a structured format.

        :param raw_data: Raw data received from the WebSocket.
        :return: Processed symbol data.
        """
        symbol_data = {}
        try:
            update_time = float(raw_data['tms']) / 1000
            symbol_data['update_time'] = update_time
            for i in range(self.order_book_depth):
                obu = raw_data['obu'][i]
                symbol_data[f"ask{i+1}"] = float(obu['ap'])
                symbol_data[f"bid{i+1}"] = float(obu['bp'])
                symbol_data[f"ask{i+1}_qty"] = float(obu['as'])
                symbol_data[f"bid{i+1}_qty"] = float(obu['bs'])
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
        try: 
            headers = self._set_headers()
            timeout = ClientTimeout(total=3)
            async with ClientSession(timeout=timeout) as session:
                async with session.request("GET", f"https://api.upbit.com/v1/status/wallet", headers=headers) as res:
                    symbol_status =  await res.json()
            non_working_symbols = [item['currency'] for item in symbol_status if item['wallet_state'] not in ['working', 'withdraw_only'] or item['block_state'] == 'inactive']
            self.non_working_symbols = non_working_symbols
            print(self.non_working_symbols)
            await asyncio.sleep(60)
        except Exception as e:
            message = f"Failed to fetch upbit non working symbols{e}"
            market_logger.error(message)

    def _set_headers(self, query_string=None):
        payload = {'access_key': UPBIT_API_KEY, 'nonce': str(uuid.uuid4())}
        if query_string:
            payload['query'] = query_string
        jwt_token = jwt.encode(payload, UPBIT_SECRET_KEY)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {'Authorization': authorization}
        return headers

