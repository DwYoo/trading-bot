import hmac
import time
import hashlib
import asyncio
import websockets
import json
from pubsub import pub
from aiohttp import ClientSession, ClientTimeout

from base.Topics import Topics
from utils.logger import account_logger

class BinanceUsdmAccount:
    def __init__(self, api_key:str, secret_key:str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_endpoint = "https://fapi.binance.com/fapi/v2/account"
        self.stream_endpoint = "wss://fstream.binance.com/ws"

    async def aconnect(self):
        try:
            listen_key = await self._get_listen_key()
            print(listen_key)
            async with websockets.connect(f"{self.stream_endpoint}/{listen_key}") as websocket:
                while True:
                    try:
                        response = await websocket.recv()
                        pub.sendMessage(Topics.ACCOUNT_UPDATE.value, data="Account updated")
                    except Exception as e:
                        print(f"Error in receiving message: {e}")
        except Exception as e:
            message = f"Error while connecting stream: {e}"
            account_logger.error(message)

    def _process_account_update_event(self, data:dict):
        #아직 안 씀
        timestamp = data['T']
        usdt_balance = data['a']['B'][0]['wb']
        try:
            updated_position = data['a']['P'][0]
            self._process_position_data(updated_position)
        except:
            pass

    
    def _process_position_data(self, data:dict):
        symbol = data['s'].strip('USDT')
        amount = data['pa']
        entry_price = data['ep']
        return symbol, amount, entry_price

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