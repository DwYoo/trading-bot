import logging
import os

# Define the directory where log files will be stored.
# Change the 'log_dir' variable to your preferred log directory path.
log_dir = './logs'

# Check if the log directory exists; if not, create it.
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Function to get a logger with a specified name.
def get_logger(name):
    # Create a logger with the given name and set the logging level to INFO.
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create a file handler to write log messages to a log file.
    file_handler = logging.FileHandler(f"./logs/{name}.log")
    
    # Define the log message format.
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Set the formatter for the file handler.
    file_handler.setFormatter(formatter)
    
    # Add the file handler to the logger.
    logger.addHandler(file_handler)
    
    # Return the configured logger.
    return logger

# Create loggers for different components or purposes.
market_logger = get_logger('market')
trade_logger = get_logger('trade')
account_logger = get_logger('account')
signal_logger = get_logger('signal')
real_trade_logger = get_logger('real_trade')
paper_trade_logger = get_logger('paper_trade')
