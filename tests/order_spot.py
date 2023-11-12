import asyncio
import sys
import os
current_script_path = os.path.abspath(__file__)
project_root_path = os.path.abspath(os.path.join(current_script_path, '..', '..', 'src'))
sys.path.append(project_root_path)
from binance_spot.broker import BinanceSpotBroker
from base.OrderSheet import OrderSheet
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("BINANCE_API_KEY")
secret_key =  os.getenv("BINANCE_SECRET_KEY")

trader = BinanceSpotBroker(api_key, secret_key)


async def trade_market_by_symbol_qty(symbol:str, side:str, qty:float):
    #symbol: BTC, side: buy or sell, qty: 0.001
    order_sheet = OrderSheet(
        id= 1,
        exchange = 'BinanceSpot',
        symbol = symbol,
        side = side,
        qty = qty,
        order_type = 'market',
    )
    result = await trader.aplace_order(order_sheet)
    print(result)

async def trade_market_by_quote_qty(symbol:str, side:str, qty_by_quote:float):
    #symbol: BTC, side: buy or sell, qty: 0.001
    order_sheet = OrderSheet(
        id= 1,
        exchange = 'BinanceSpot',
        symbol = symbol,
        side = side,
        qty_by_quote = qty_by_quote,
        order_type = 'market',
    )
    result = await trader.aplace_order(order_sheet)
    print(result)


if __name__ == '__main__':
    asyncio.run(trade_market_by_quote_qty('BTC', 'buy', 100))
    # print(time.strftime("%H:%M:%S"))
    #시간 상관없이 시장가로 팔 때: trade_market('BTC', 'sell' 0.001) 실행
    # 특정 시간에 시장가로 팔 때: trade_market_intime('BTC', 'sell', 0.001, '12:00:00') 실행
    # asyncio.run(trade_market_intime('BTC','buy', 0.002, '22:10:00'))