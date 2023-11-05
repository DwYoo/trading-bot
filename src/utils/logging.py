import logging
import os

# log_dir = '/home/ubuntu/logs'
log_dir = './logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
        
def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(f"./logs/{name}.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

market_logger = get_logger('market')
trade_logger = get_logger('trade')
account_logger = get_logger('account')
signal_logger = get_logger('signal')
real_trade_logger = get_logger('real_trade')
paper_trade_logger = get_logger('paper_trade')