import logging
import os
import inspect
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Utility.Utils import TradeDirection


class Strategy:
    """
    Generic strategy template to use as a parent class for custom strategies.
    """

    def __init__(self, config, broker):
        self.positions = None
        self.broker = broker
        # Read configuration of derived Strategy
        self.read_configuration(config)
        # Initialise derived Strategy
        self.initialise()

    def set_open_positions(self, positions):
        """
        Set the account open positions
        """
        self.positions = positions

    def run(self, market):
        """
        Run the strategy against the specified market
        """
        datapoints = self.fetch_datapoints(market)
        logging.debug("Strategy datapoints: {}".format(datapoints))
        if datapoints is None:
            logging.debug('Unable to fetch market datapoints')
            return TradeDirection.NONE, None, None
        return self.find_trade_signal(market, datapoints)

    #############################################################
    # OVERRIDE THESE FUNCTIONS IN STRATEGY IMPLEMENTATION
    #############################################################

    def initialise(self):
        """
        Must override
        """
        raise NotImplementedError("Not implemented: initialise")

    def read_configuration(self, config):
        """
        Must override
        """
        raise NotImplementedError("Not implemented: read_configuration")

    def fetch_datapoints(self, market):
        """
        Must override
        """
        raise NotImplementedError("Not implemented: fetch_datapoints")

    def find_trade_signal(self, epic_id, prices):
        """
        Must override
        """
        raise NotImplementedError("Not implemented: find_trade_signal")

    def backtest(self, market, start_date, end_date):
        """
        Must override
        """
        return NotImplementedError("This strategy doe not support backtesting")


##############################################################
##############################################################
