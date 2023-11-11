from binance.trader import BinanceUsdmTrader
from base.OrderSheet import OrderSheet
import time
import sys
sys.path.append('../')
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("Binance")['apiKey']
secret_key =  os.getenv("Binance")['secret']
print(api_key, secret_key)


trader = BinanceUsdmTrader(api_key, secret_key)

async def trade_market(symbol:str, side:str, qty:float):
    #symbol: BTC, side: buy or sell, qty: 0.001
    order_sheet = OrderSheet(
        exchange = 'BinanceUsdm',
        symbol = symbol,
        side = side,
        qty = qty,
        order_type = 'market',
    )
    await trader.aplace_order(order_sheet)

async def trade_market_intime(symbol, side, qty, target_time):
    #Ex: symbol: 'BTC', side: 'sell', qty: 0.001, target_time: '12:00:00'
    while True:
        print("Printing money...")
        current_time = time.strftime("%H:%M:%S")
        if current_time == target_time:
            time.sleep(0.1)
            await trade_market(symbol, side, qty)
            break



if __name__ == '__main__':
    pass
    # print(time.strftime("%H:%M:%S"))
    #시간 상관없이 시장가로 팔 때: trade_market('BTC', 'sell' 0.001) 실행
    # 특정 시간에 시장가로 팔 때: trade_market_intime('BTC', 'sell', 0.001, '12:00:00') 실행
    # asyncio.run(trade_market_intime('BTC','buy', 0.002, '22:10:00'))