from markets.binance import BinanceUsdmMarket
from markets.upbit import UpbitKrwMarket
import asyncio



upbit_market = UpbitKrwMarket(symbols=['BTC', 'ETH'], order_book_depth=2)    
asyncio.run(upbit_market.stream())
