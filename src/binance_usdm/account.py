import hmac
import time
import hashlib
import asyncio
import websockets
import json
from pubsub import pub
from aiohttp import ClientSession, ClientTimeout

from base.Account import Account
from base.Events import Events
from utils.logger import account_logger

class BinanceUsdmAccount(Account):

    def __init__(self, api_key:str, secret_key:str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.account_endpoint = "https://fapi.binance.com/fapi/v2/account"
        self.stream_endpoint = "wss://fstream.binance.com/ws"
        pub.subscribe(self._on_account_event_from_client, Events.ACCOUNT_EVENT_FROM_CLIENT.value)

    async def aupdate_balance(self):
        #updates balance and positions and publishes the event
        raw_account_data = await self._fetch_account_data()
        balance = self._process_raw_account_data(raw_account_data)
        self.balance = balance
        
    async def aconnect(self):
        try:
            listen_key = await self._get_listen_key()
            async with websockets.connect(f"{self.stream_endpoint}/{listen_key}") as websocket:
                while True:
                    try:
                        response = await websocket.recv()
                        pub.sendMessage(Events.ACCOUNT_EVENT_FROM_CLIENT.value, message="Account event from client")
                    except Exception as e:
                        print(f"Error in receiving message: {e}")
        except Exception as e:
            message = f"Error while connecting stream: {e}"
            account_logger.error(message)

    def _on_account_event_from_client(self, message):
        asyncio.create_task(self.aupdate_balance())

    async def _fetch_account_data(self):
        try:
            params = {
                    'recvWindow': 5000,
                    'timestamp': self._set_timestamp()
                }
            raw_account_data = await self._acall_api("GET", self.account_endpoint, params)
            return raw_account_data
        except Exception as e:
            message = f"Error while fetching account data from binance: {e}"
            account_logger.error(message)

    def _process_raw_account_data(self, raw_account_data:dict) -> dict:
        account_data = {}
        account_data['available_balance'] = float(raw_account_data['availableBalance'])
        account_data['total_balance'] = float(raw_account_data['totalWalletBalance'])
        account_data['positions'] = self._process_positions(raw_account_data)
        return account_data

    def _process_positions(self, raw_account_data) -> dict:
        #Get positions from raw_account_data
        positions = {}
        for position in raw_account_data['positions']:
            if 'USDT' in position['symbol'] and abs(float(position['notional'])) > 1:
                symbol = position['symbol'].replace('USDT', '')
                positions[symbol] = {
                    'avg_price': float(position['entryPrice']),
                    'qty': float(position['positionAmt']),
                }
        return positions

    async def _get_listen_key(self):
        try:
            params = {
                'recvWindow': 5000,
                'timestamp': self._set_timestamp()
            }
            response = await self._acall_api("POST", f"https://fapi.binance.com/fapi/v1/listenKey", params)
            return response['listenKey']

        except Exception as e:
            message = f"Error while getting listen key: {e}"
            account_logger.error(message)

    async def _acall_api(self, method:str, endpoint:str, params:dict):
        query_string = self._set_query_string(params)
        signature = self._set_signature(query_string)
        headers = self._set_headers()
        timeout = ClientTimeout(total=1)
        async with ClientSession(timeout=timeout) as session:
            async with session.request(method, f"{endpoint}?{query_string}&signature={signature}", headers=headers) as res:
                return await res.json()

    def _set_query_string(self, params: dict) -> str:
        query_string = '&'.join(["{}={}".format(key, params[key]) for key in params.keys()])
        return query_string
    
    def _set_signature(self, query_string: dict) -> str:
        signature = hmac.new(self.secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return signature

    def _set_headers(self):
        headers = {
            'X-MBX-APIKEY': self.api_key,
        }
        return headers
    
    def _set_timestamp(self):
        timestamp = int(time.time() * 1000)
        return timestamp