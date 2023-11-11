from binance.market import BinanceUsdmMarket
from upbit.market import UpbitKrwMarket
import asyncio


upbit_market = BinanceUsdmMarket(symbols=['BTC', 'ETH'], order_book_depth=2)    
asyncio.run(upbit_market.stream())
