import requests
from bs4 import BeautifulSoup
import json
import time
from utils.logger import signal_logger

class BinanceListingChecker:

    @staticmethod
    def check(url) -> str:
        """
        Checks if there is a new listing announcement. If there is, return the token name.
        """
        try: 
            script_data = BinanceListingChecker.scrap(url).find('script', {'id': '__APP_DATA'})
            latest_article = BinanceListingChecker.get_latest_article(script_data)
            lastest_title = latest_article['title']
            article_release_timestamp = latest_article['releaseDate']
            signal_logger.info(f"Latest announcement: {lastest_title}")
            if BinanceListingChecker.is_new_announcement(article_release_timestamp):
                return BinanceListingChecker.get_listing_symbol(lastest_title)
            
        except Exception as e:
            signal_logger.error(f"Error while checking binance announcement: {e}")
            return ""

    @staticmethod
    def scrap(url) -> BeautifulSoup:
        response = requests.get(url)
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
        else:
            signal_logger.error(f"Error while crwaling binance: {response.status_code}")

    @staticmethod
    def get_script_data(soup):
        return soup.find('script', {'id': '__APP_DATA'})
    
    @staticmethod
    def get_latest_article(script_data):
        latest_article = BinanceListingChecker.get_articles(script_data)[0]
        return latest_article

    @staticmethod
    def get_articles(script_data):
        json_data = json.loads(script_data.contents[0])
        app_state = json_data.get('appState', {})
        articles = app_state.get('loader', {}).get('dataByRouteId', {}).get('2a3f', {}).get('catalogs', [])[0].get('articles', [])
        return articles
    
    @staticmethod
    def is_new_announcement(release_timestamp: int, threshold_time:float=30) -> bool:
        #Checks if there is a new listing announcement. If there is, return the token name.
        if (time.time() - release_timestamp/1000) < threshold_time:
            return True
        else:
            return False
        
    @staticmethod
    def get_listing_symbol(title: str) -> str:
        tokens = title.split()
        if (tokens[0] == "Binance" and 
            tokens[1] == "Futures" and 
            tokens[2] == "Will" and 
            tokens[3] == "Launch" and 
            tokens[4] == "USDⓈ-M"):
            return tokens[5]
        else:
            return ""