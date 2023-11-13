import time
import copy
import pandas as pd
import numpy as np

from utils.logging import market_logger


class OrderBookCalculator:
    def __init__(self, order_book_df_1:pd.DataFrame, order_book_df_2:pd.DataFrame, fx_rate:float=None) -> None:
        self.order_book_1 = order_book_df_1
        self.order_book_2 = order_book_df_2
        self.fx_rate = fx_rate

    @staticmethod
    def calculate_bid_ask_spread(order_book_df:pd.DataFrame) -> pd.Series:
        #Returns bid ask spread for one symbol
        try:
            bid = copy.deepcopy(order_book_df)
            ask = copy.deepcopy(order_book_df)
            return (ask - bid) / bid
        except:
            message = f"Error while calculating bid ask spread"
            market_logger.error(message)
            return None

    @staticmethod
    def calculate_exchange_premium(order_book_df_1:pd.DataFrame, order_book_df_2:pd.DataFrame, fx_rate:float=1, type:tuple=('ask1','bid1')) -> pd.Series:
        #exchange2 대비 exchange1 에서의 상대적인 프리미엄 계산 
        try:
            exchange1_price = copy.deepcopy(order_book_df_1[type[0]])
            exchange2_price = copy.deepcopy(order_book_df_2[type[1]])
            exchange2_price = exchange2_price * fx_rate
            exchange_premium = (exchange1_price - exchange2_price) /exchange2_price
            return exchange_premium.astype("float")
        except Exception as e:
            message = f"Error while calculating exchange premium: {e}"
            market_logger.error(message)
            return None

    @staticmethod
    def calculate_symbol_premium_respect_to_standard(exchange_premium:pd.Series, standard_premium:float) -> pd.Series:
        symbol_premium = (exchange_premium - standard_premium)
        return symbol_premium.astype("float")
    
    @staticmethod
    def calculate_max_qty(order_book_df_1, order_book_df_2, type:tuple=('ask1_qty','bid1_qty')) -> pd.Series:
        qty1 = copy.deepcopy(order_book_df_1[type[0]]).fillna(0)
        qty2 = copy.deepcopy(order_book_df_2[type[1]]).fillna(0)
        max_qty = np.minimum(qty1, qty2)
        return max_qty.astype("float")

    @staticmethod
    def calculate_max_cap(order_book_df_1, max_qty:pd.Series):
        bid = copy.deepcopy(order_book_df_1['bid1'])
        ask = copy.deepcopy(order_book_df_1['ask1'])
        try: max_cap = max_qty * bid
        except: max_cap = max_qty * ask
        return max_cap.astype("float")
    
    @staticmethod
    def is_valid(self, valid_threshold:tuple=(0.4,0.2)):
        delay_time1 = self.calculate_delay_time(self.exchange1_name)
        delay_time2 = self.calculate_delay_time(self.exchange2_name)
        return (delay_time1 < valid_threshold[0]) & (delay_time2 < valid_threshold[1])
    
    def calculate_delay_time(self, order_book_df_1:str) -> pd.Series:
        #Returns delay time for one symbol
        update_time = copy.deepcopy(self.order_book_data[exchange_name]['update_time'])
        try:
            current_time = time.time()
            delay_time = current_time - update_time
            return delay_time.astype("float")
        except Exception as e:
            message = f"Error while calculating delay time for {exchange_name}: {e}"
            market_logger.error(message)
            return None
        