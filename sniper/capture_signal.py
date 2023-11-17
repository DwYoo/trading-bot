import time
import os
import sys
import asyncio
from pubsub import pub
current_script_path = os.path.abspath(__file__)
project_root_path = os.path.abspath(os.path.join(current_script_path, '..', '..', 'src'))
sys.path.append(project_root_path)
from listing_checker import BinanceListingChecker
from sniping_events import SNIPING_EVENTS
from utils import logger, telegram

BINANCE_URL = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"
CRWALING_INTERVAL = 10

telegram.sniper_alert.subscribe_event(SNIPING_EVENTS.SIGNAL_DETECTED.value)

async def capture_signal():
    while(True):
        new_symbol = BinanceListingChecker.check(BINANCE_URL)
        if new_symbol:
            pub.sendMessage(SNIPING_EVENTS.SIGNAL_DETECTED.value, message= f"Open Signal: \n {new_symbol.upper()} will be listed on Binance Futures.")
            logger.signal_logger.info(f"Open Signal: \n {new_symbol.upper()} will be listed on Binance Futures.") 
            print(f"Open Signal: \n {new_symbol.upper()} will be listed on Binance Futures.")
        await asyncio.sleep(CRWALING_INTERVAL)

asyncio.run(capture_signal())
