import logging
import time
import traceback
import pytz
import datetime
from random import shuffle
import os
import inspect
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from Utils import Utils, TradeDirection

class Strategy:
    """
    Generic strategy template to use as a parent class for custom strategies.
    Provide safety checks for new trades and handling of open positions.
    """
    def __init__(self, config, services):
        self.positions = {}
        self.broker = services['broker']
        self.AV = services['alpha_vantage']

        self.time_zone = config['general']['time_zone']
        self.order_size = config['ig_interface']['order_size']
        self.max_account_usable = config['general']['max_account_usable']
        self.spin_interval = config['strategies']['spin_interval'] # This can be overwritten in children class
        self.timeout = 1 # Delay between each find_trade_signal() call

        # This must be the last operation of this function to override possible values in children class
        self.read_configuration(config)


#############################################################
# OVERRIDE THESE FUNCTIONS IN STRATEGY IMPLEMENTATION
#############################################################

    def read_configuration(self, config):
        """
        Must override
        """
        raise NotImplementedError('Not implemented: read_configuration')

    def find_trade_signal(self, epic_id):
        """
        Must override
        """
        raise NotImplementedError('Not implemented: find_trade_signal')

    def get_seconds_to_next_spin(self):
        """
        Must override
        """
        raise NotImplementedError('Not implemented: get_seconds_to_next_spin')

##############################################################
##############################################################


    def start(self, epic_list):
        """
        Start the strategy processing the given list of epic ids. Wait until the
        market is open to start processing.

            - **epic_list**: list of epic ids
        """
        while True:
            if not self.isMarketOpen(self.time_zone):
                self.spin(epic_list)
            else:
                logging.info("Market is closed! Wait 60 seconds...")
                time.sleep(60)
                continue


    def spin(self, epic_list):
        """
        Process the epic list one by one handling new trades and closing
        open positions if necessary

            - **epic_list**: list of epic ids
        """
        logging.info("Strategy started to spin.")
        try:
            # Fetch open positions and process them first
            logging.info("Processing open positions.")
            self.positions = self.broker.get_open_positions()
            if self.positions is not None:
                for item in self.positions['positions']:
                    self.process_epic(item['market']['epic'])
                    time.sleep(self.timeout)
            else:
                logging.warn("Unable to retrieve open positions!")

            # Check if the account has enough cash available to open new positions
            percent_used = self.get_account_used_perc()
            if percent_used < self.max_account_usable:
                logging.info("Ok to trade, {}% of account is used".format(str(percent_used)))
                if len(epic_list) < 1:
                    logging.warn("Epic list is empty!")
                else:
                    logging.info("Started processing epic list of length: {}".format(len(epic_list)))
                    shuffle(epic_list)
                    for epic in epic_list:
                        try:
                            if self.process_epic(epic):
                                # If there has been a trade check again account usage
                                percent_used = self.get_account_used_perc()
                                if percent_used > self.max_account_usable:
                                    logging.warn("Stop trading because {}% of account is used".format(str(percent_used)))
                                    break
                            time.sleep(self.timeout)
                        except Exception as e:
                            logging.error(e)
                            logging.error(traceback.format_exc())
                            logging.error(sys.exc_info()[0])
                            time.sleep(self.timeout)
                            continue
            else:
                logging.warn("Will not trade, {}% of account balance is used."
                                .format(str(percent_used)))

            # If interval is set to -1 in config file then the strategy should provide its own interval
            seconds = self.get_seconds_to_next_spin() if self.spin_interval < 0 else self.spin_interval
            logging.info("Epics analysis complete. Wait for {} seconds".format(seconds))
            time.sleep(seconds)
        except Exception as e:
                logging.error(e)
                logging.error(traceback.format_exc())
                logging.error(sys.exc_info()[0])
                logging.error("Something fucked up.")
                time.sleep(self.timeout)


    def process_epic(self, epic):
        """
        process the given epic

            - **epic**: market epic as string
            - Returns **False** if an error occurs otherwise True
        """
        logging.info("Processing {}".format(epic))
        # Process the epic and find if we want to trade
        trade, limit, stop = self.find_trade_signal(epic)
        # In case of no trade don't do anything
        if trade is not TradeDirection.NONE:
            if self.positions is not None:
                for item in self.positions['positions']:
                    # If a same direction trade already exist, don't trade
                    if item['market']['epic'] == epic and trade.name == item['position']['direction']:
                        logging.warn("There is already an open position for this epic, skip trade")
                        return False
                    # If a trade in opposite direction exist, close the position
                    elif item['market']['epic'] == epic and trade.name != item['position']['direction']:
                        return self.broker.close_position(item)
                return self.broker.trade(epic, trade.name, limit, stop)
            else:
                logging.error("Unable to retrieve open positions! Avoid trading this epic")
        return False


    def get_account_used_perc(self):
        """
        Fetch the percentage of available balance is currently used

            - Returns the percentage of account used over total value available
        """
        balance, deposit = self.broker.get_account_balances()
        if balance is None or deposit is None:
            return 9999999 # This will block the trading
        return Utils.percentage(deposit, balance)


    def isMarketOpen(self, timezone):
        """
        Return True if the market is open, false otherwise

            - **timezone**: string representing the timezone
        """
        tz = pytz.timezone(timezone)
        now_time = datetime.datetime.now(tz=tz).strftime('%H:%M')
        return Utils.is_between(str(now_time), ("07:55", "16:35"))
