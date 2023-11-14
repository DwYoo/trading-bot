import sys
import os
# Get the absolute path of the current script
current_script_path = os.path.abspath(__file__)
# Get the absolute path of the project root by going to the parent directory and then to 'src'
project_root_path = os.path.abspath(os.path.join(current_script_path, '..', '..', 'src'))
# Add the project root path to the sys.path
sys.path.append(project_root_path)
from binance_usdm.market import BinanceUsdmMarket
from upbit.market import UpbitKrwMarket
import asyncio


upbit_market = UpbitKrwMarket(symbols=['BTC', 'ETH'], order_book_depth=2)    
asyncio.run(upbit_market.stream())
