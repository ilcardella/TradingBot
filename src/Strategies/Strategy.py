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
        # This can be overwritten in children class
        self.spin_interval = 3600
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
        settings = self.get_price_settings()
        prices = []
        for interval, time_range in settings:
            data = self.broker.get_prices(market.epic, interval, time_range)
            if data is None:
                logging.error(
                    "No historic data available for {} ({})".format(
                        market.epic, market_id
                    )
                )
                return TradeDirection.NONE, None, None
            else:
                prices.append(data)

        if len(prices) < 1:
            logging.error("No price settings defined for active strategy")
            return TradeDirection.NONE, None, None

        return self.find_trade_signal(market, prices)

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

    def get_price_settings(self):
        """
        Must override
        """
        raise NotImplementedError("Not implemented: get_price_settings")

    def find_trade_signal(self, epic_id, prices):
        """
        Must override
        """
        raise NotImplementedError("Not implemented: find_trade_signal")

    def get_seconds_to_next_spin(self):
        """
        Must override
        """
        return self.spin_interval


##############################################################
##############################################################
