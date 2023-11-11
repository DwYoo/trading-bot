import hmac
import time
import hashlib
import asyncio
from aiohttp import ClientSession, ClientTimeout

from utils.logger import account_logger

class BinanceUsdmAccount:
    def __init__(self, api_key: str, secret_key: str):
        # Initialize the Binance USDM account object with API key and secret key.
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_endpoint = "https://fapi.binance.com/fapi/v2/account"
        self.stream_endpoint = "wss://fstream.binance.com/ws/"

    async def connect_stream(self):
        try:
            # Attempt to connect to the Binance WebSocket stream and obtain a listen key.
            response = await self._acall_api("POST", self.stream_endpoint, {})
            return response['listenKey']
        except Exception as e:
            # Handle any errors that occur during the connection and log them.
            message = f"Error while connecting stream: {e}"
            account_logger.error(message)

    async def _get_listen_key(self):
        # Get a listen key for streaming data from the Binance API.
        response = await self._acall_api("POST", f"https://fapi.binance.com/fapi/v1/listenKey")
        return response['listenKey']

    async def _acall_api(self, method: str, endpoint: str, params: dict):
        # Make an asynchronous API call to Binance.
        query_string = self._set_query_string(params)
        signature = self._set_signature(query_string)
        headers = self._set_headers()
        timeout = ClientTimeout(total=1)
        async with ClientSession(timeout=timeout) as session:
            async with session.request(method, f"{endpoint}?{query_string}&signature={signature}", headers=headers) as res:
                return await res.json()

    def _set_query_string(self, params: dict) -> str:
        # Convert the parameters into a query string for the API request.
        query_string = '&'.join(["{}={}".format(key, params[key]) for key in params.keys()])
        return query_string
    
    def _set_signature(self, query_string: dict) -> str:
        # Generate a signature for the API request using the secret key.
        signature = hmac.new(self.secret_key.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return signature

    def _set_headers(self):
        # Set the headers for the API request, including the API key.
        headers = {
            'X-MBX-APIKEY': self.api_key,
        }
        return headers
    
    def _set_timestamp(self):
        # Generate a timestamp for the API request, typically used for request expiration.
        timestamp = int(time.time() * 1000)
        return timestamp
