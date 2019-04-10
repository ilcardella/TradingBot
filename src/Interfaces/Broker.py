import logging
import os
import inspect
import sys
import time

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

# from Interfaces.IGInterface import IGInterface
# from Interfaces.AVInterface import AVInterface

class Broker():
    """
    This class provides a template interface for all those broker related
    actions/tasks wrapping the actual implementation class internally
    """
    def __init__(self, config, services):
        self.read_configuration(config)
        self.ig_index = services['ig_index']
        self.alpha_vantage = services['alpha_vantage']

    def read_configuration(self, config):
        self.use_av_api = config['general']['use_av_api']
        # AlphaVantage limits to 5 calls per minute
        self.trade_timeout = 12 if self.use_av_api else 2

    def wait_after_trade(self):
        """
        Wait for the required amount of time after a trade call. Depends on
        broker API calls restrictions
        """
        time.sleep(self.trade_timeout)

    def get_open_positions(self):
        """
        Returns the current open positions
        """
        return self.ig_index.get_open_positions()

    def get_market_from_watchlist(self, watchlist_name):
        """
        TODO
        """
        return self.ig_index.get_market_from_watchlist(watchlist_name)

    def navigate_market_node(self, node_id):
        """
        TODO
        """
        return self.ig_index.navigate_market_node(node_id)

    def get_account_used_perc(self):
        """
        TODO
        """
        return self.ig_index.get_account_used_perc()

    def close_all_positions(self):
        """
        TODO
        """
        return self.ig_index.close_all_positions()

    def close_position(self, position):
        """
        TODO
        """
        return self.ig_index.close_position(position)

    def trade(self, epic, trade_direction, limit, stop):
        """
        TODO
        """
        return self.ig_index.trade(epic, trade_direction, limit, stop)

    def get_market_info(self, epic):
        """
        TODO
        """
        return self.ig_index.get_market_info(epic)

    def macd_dataframe(self, epic, market_id, interval):
        """
        Return a dataframe containing MACD tech indicator date for the requested
        market with requested interval and range of data
        """
        if self.use_av_api:
            return self.alpha_vantage.macdext(market_id, interval)
        else:
            return self.ig_index.macd_dataframe(epic, None)
        return None

    def get_prices(self, epic, interval, range):
        """
        TODO
        """
        return self.ig_index.get_prices(epic, interval, range)

    def weekly(self, market_id):
        """
        TODO
        """
        return self.alpha_vantage.weekly(market_id)
