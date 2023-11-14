import jwt
import uuid
import asyncio
from pubsub import pub
from aiohttp import ClientSession, ClientTimeout
import pandas as pd

from base.Account import Account
from base.Events import Events
from utils.logger import account_logger as logger


class UpbitAccount(Account):
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.endpoint = "https://api.upbit.com/v1/accounts"


    async def aupdate_balance(self, order_book:pd.DataFrame=None) :
        try:
            raw_account_data = await self._fetch_account_data()
            balance = self._process_raw_balance_data(raw_account_data, order_book)
            self.balance = balance
        except Exception as e:
            message = f"Failed to fetch upbit balance data: {e}"
            logger.error(message)

    async def aconnect(self):
        while True:
            await self.aupdate_balance()
            await asyncio.sleep(1800)

    async def _fetch_account_data(self) -> dict:
        try: 
            headers = self._set_headers()
            raw_balance_data = await self._acall_api("GET", self.endpoint, "", headers)
            return raw_balance_data
        except Exception as e:
            message = f"Failed to fetch upbit raw balance data: {e}"
            logger.error(message)

    def _get_qty(self, raw_balance:dict) -> float:
        qty = float(raw_balance['balance']) + float(raw_balance['locked'])
        return qty
    
    def _get_market_price(self, raw_balance:dict, order_book:pd.DataFrame) -> dict:
        symbol = raw_balance['currency']
        if symbol == 'KRW':
            market_price = 1
        else:
            try: market_price = order_book.loc[symbol]['bid1']
            except Exception as e: 
                message = f"Failed to fetch market price for {symbol}: {e}"
                logger.error(message)
                market_price = float(raw_balance['avg_buy_price'])
        return market_price
        
    def _process_raw_balance_data(self, raw_data:dict, order_book:pd.DataFrame) -> dict:
        balance_data = {}
        total_balance = 0
        balance_data['positions'] = {}
        for raw_balance in raw_data:
            symbol = raw_balance['currency']
            if symbol =='KRW': 
                balance_data['available_balance'] = float(raw_balance['balance'])
                total_balance += self._get_qty(raw_balance)
            else:
                qty = self._get_qty(raw_balance)
                avg_buy_price = float(raw_balance['avg_buy_price'])
                if avg_buy_price * qty > 5000:
                    balance_data['positions'][symbol] = {
                        'avg_price': float(raw_balance['avg_buy_price']),
                        'qty': qty,
                    }
                    market_price = self._get_market_price(raw_balance, order_book)
                    total_balance += qty * market_price
        balance_data['total_balance'] = total_balance
        return balance_data
    
    async def _acall_api(self, method: str, endpoint: str, params: dict, headers=None, data=None, time=2):
        """
        Make an asynchronous HTTP request to the API endpoint.

        :param method: The HTTP request method (GET, POST, DELETE, etc.).
        :param endpoint: The API endpoint URL.
        :param params: Dictionary of request parameters.
        :param headers: HTTP headers for the request.
        :param data: Request data for POST requests.
        :param time: Timeout for the request.
        :return: JSON response from the API.
        """
        timeout = ClientTimeout(total=time)
        async with ClientSession(timeout=timeout) as session:
            async with session.request(method, f"{endpoint}?{params}", headers=headers, data=data) as res:
                return await res.json()
            
    def _set_headers(self, query_string=None):
        payload = {'access_key': self.api_key, 'nonce': str(uuid.uuid4())}
        if query_string:
            payload['query'] = query_string
        jwt_token = jwt.encode(payload, self.secret_key)
        authorization = 'Bearer {}'.format(jwt_token)
        headers = {'Authorization': authorization}
        return headers
    
