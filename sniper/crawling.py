import requests
from bs4 import BeautifulSoup
import json
import time


def get_binance_articles(script_data):
    json_data = json.loads(script_data.contents[0])
    dynamic_ids = json_data.get('dynamicIds', [])
    app_state = json_data.get('appState', {})
    articles = app_state.get('loader', {}).get('dataByRouteId', {}).get('2a3f', {}).get('catalogs', [])[0].get('articles', [])
    return articles

def binance_article_parser(title: str) -> str:
    tokens = title.split()
    if (tokens[0] == "Binance" and 
        tokens[1] == "Futures" and 
        tokens[2] == "Will" and 
        tokens[3] == "Launch" and 
        tokens[4] == "USDⓈ-M"):
        return tokens[5]
    else:
        return ""

def announce_check(url: str, nth: int=0) -> str:
    script_data = scraped_html(url).find('script', {'id': '__APP_DATA'})
    if(script_data):
        article = get_binance_articles(script_data)[0]
        lastest_title = article['title']
        time_stamp = article['releaseDate']
        if(time_lock(time_stamp)):
            return binance_article_parser(lastest_title)

def scraped_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BeautifulSoup(response.text, 'html.parser')
    else:
        print(response.status_code)

def time_lock(time_stamp: int, lock: int=30, delay: int =0.5) -> bool:
    """
    param: 초단위
    계산식: ms단위
    """
    return time.time()*1000 - time_stamp < (lock + delay) * 1000