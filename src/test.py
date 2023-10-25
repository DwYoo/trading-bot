from markets.binance import BinanceUsdmMarket
from markets.upbit import UpbitKrwMarket
import asyncio
import time


upbit_market = BinanceUsdmMarket(symbols=['BTC', 'ETH'], order_book_depth=2)    
asyncio.run(upbit_market.stream())
