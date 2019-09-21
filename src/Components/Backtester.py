import logging
import os
import inspect
import sys
from collections import deque
from enum import Enum
from random import shuffle

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)


class Backtester:
    """
    Provides capability to backtest markets on a defined range of time
    """

    def __init__(self, broker, strategy):
        logging.info("Backtester created")
        self.broker = broker
        self.strategy = strategy
        self.result = None

    def start(self, market, start_dt, end_dt):
        """Backtest the given market within the specified range
        """
        logging.info(
            "Backtester started for market id {} from {} to {}".format(
                market.id, start_dt.date(), end_dt.date()
            )
        )
        self.result = self.strategy.backtest(market, start_dt, end_dt)

    def print_results(self):
        """Print backtest result in log file
        """
        logging.info("Backtest result:")
        logging.info(self.result)

