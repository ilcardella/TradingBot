import logging
from abc import ABC, abstractmethod

from Components.Utils import TradeDirection


class Strategy(ABC):
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
            logging.debug("Unable to fetch market datapoints")
            return TradeDirection.NONE, None, None
        return self.find_trade_signal(market, datapoints)

    #############################################################
    # OVERRIDE THESE FUNCTIONS IN STRATEGY IMPLEMENTATION
    #############################################################

    @abstractmethod
    def initialise(self):
        pass

    @abstractmethod
    def read_configuration(self, config):
        pass

    @abstractmethod
    def fetch_datapoints(self, market):
        pass

    @abstractmethod
    def find_trade_signal(self, epic_id, prices):
        pass

    @abstractmethod
    def backtest(self, market, start_date, end_date):
        pass
