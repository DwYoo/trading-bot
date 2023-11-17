import time
import os
import sys
import asyncio
from pubsub import pub
current_script_path = os.path.abspath(__file__)
project_root_path = os.path.abspath(os.path.join(current_script_path, '..', '..', 'src'))
sys.path.append(project_root_path)
from listing_checker import BinanceListingChecker


def test_scrap():
    url = "https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48"
    soup = BinanceListingChecker.scrap(url)
    script_data = BinanceListingChecker.get_script_data(soup)
    first_article = BinanceListingChecker.get_first_article(script_data)
    print(first_article)

test_scrap()