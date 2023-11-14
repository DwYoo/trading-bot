import sys
import os
current_script_path = os.path.abspath(__file__)
project_root_path = os.path.abspath(os.path.join(current_script_path, '..', '..', 'src'))
sys.path.append(project_root_path)

import asyncio
from binance_usdm.account import BinanceUsdmAccount
from utils.telegram import telegram_alert

from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
secret_key =  os.getenv("BINANCE_SECRET_KEY")

account = BinanceUsdmAccount(api_key, secret_key)


asyncio.run(account.alisten())
