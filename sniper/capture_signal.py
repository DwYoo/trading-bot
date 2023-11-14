import time
import os
import sys
current_script_path = os.path.abspath(__file__)
project_root_path = os.path.abspath(os.path.join(current_script_path, '..', '..', 'src'))
sys.path.append(project_root_path)
from utils import crawling

BINANCE_URL = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"

while(True):
    signal = crawling.announce_check(BINANCE_URL, 1)
    print(signal)
    if signal:
        pass
    time.sleep(30)