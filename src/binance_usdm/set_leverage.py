import ccxt
import os
from dotenv import load_dotenv
load_dotenv()

binance = ccxt.binanceusdm({
    "options": {"defaultType": "future"},
    "timeout": 30000,
    "apiKey":os.getenv("BINANCE_API_KEY"),
    "secret": os.getenv("BINANCE_SECRET_KEY"),
    "enableRateLimit": True,
})

binance.load_markets()  # load markets to get the market id from a unified symbol
print(binance.markets)
for market in binance.markets.values():
    binance.set_leverage(
        leverage=4, 
        symbol=market['id'],  # convert a unified CCXT symbol to an exchange-specific market id
)