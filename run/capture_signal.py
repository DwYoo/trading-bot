import src.utils.crawling as crawl
import time

BINANCE_URL = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"

while(True):
    time.sleep(30)
    if announce_check(BINANCE_URL):
        pass