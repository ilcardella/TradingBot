import logging
import json
from pathlib import Path
import pytz
import time
import datetime as dt
import os
import sys
import inspect
from random import shuffle

currentdir = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Utils import Utils, TradeDirection
from Interfaces.IGInterface import IGInterface
from Interfaces.AVInterface import AVInterface
from Strategies.SimpleMACD import SimpleMACD

class StocksAutoTrader:
    """
    Class that initialise and hold references of main components like the
    broker interface, the strategy or the epic_ids list
    """
    def __init__(self):
        # Set timezone
        set(pytz.all_timezones_set)

        # Read configuration file
        try:
            with open('../config/config.json', 'r') as file:
                config = json.load(file)
        except IOError:
            logging.error("Configuration file not found!")
            exit()
        self.read_configuration(config)

        # Read credentials file
        try:
            with open(self.credentials_filepath, 'r') as file:
                credentials = json.load(file)
        except IOError:
            logging.error("Credentials file not found!")
            exit()

        # Define the global logging settings
        debugLevel = logging.DEBUG if self.debug_log else logging.INFO
        # If enabled define log file filename with current timestamp
        if self.enable_log:
            log_filename = self.log_file
            time_str = dt.datetime.now().isoformat()
            time_suffix = time_str.replace(':', '_').replace('.', '_')
            home = str(Path.home())
            log_filename = log_filename.replace('{timestamp}', time_suffix).replace('{home}', home)
            os.makedirs(os.path.dirname(log_filename), exist_ok=True)
            logging.basicConfig(filename=log_filename,
                            level=debugLevel,
                            format="[%(asctime)s] %(levelname)s: %(message)s")
        else:
            logging.basicConfig(level=debugLevel,
                            format="[%(asctime)s] %(levelname)s: %(message)s")
        # Positions container
        self.positions = None
        # Create IG interface
        self.IG = IGInterface(config)
        # Init the IG interface
        if not self.IG.authenticate(credentials):
            logging.error("Authentication failed")
            exit()

        # Init AlphaVantage interface
        self.AV = AVInterface(credentials['av_api_key'])

        # Create dict of services
        services = {
            "broker": self.IG,
            "alpha_vantage": self.AV
        }

        # Define the strategy to use here
        self.strategy = SimpleMACD(config, services)

    def read_configuration(self, config):
        """
        Read the configuration from the config json
        """
        self.epic_ids_filepath = config['general']['epic_ids_filepath']
        self.credentials_filepath = config['general']['credentials_filepath']
        self.debug_log = config['general']['debug_log']
        self.enable_log = config['general']['enable_log']
        self.log_file = config['general']['log_file']
        self.time_zone = config['general']['time_zone']
        self.max_account_usable = config['general']['max_account_usable']
        self.use_av_api = config['general']['use_av_api']
        # AlphaVantage limits to 5 calls per minute
        self.timeout = 12 if self.use_av_api else 1

    def get_epic_ids(self):
        """
        Read a file from filesystem containing a list of epic ids.
        The filepath is defined in config.json file
        Returns a 'list' of strings where each string is a market epic
        """
        # define empty list
        epic_ids = []
        try:
            # open file and read the content in a list
            with open(self.epic_ids_filepath, 'r') as filehandle:
                filecontents = filehandle.readlines()
                for line in filecontents:
                    # remove linebreak which is the last character of the string
                    current_epic_id = line[:-1]
                    epic_ids.append(current_epic_id)
        except IOError:
            # Create the file empty
            logging.error('{} does not exist!'.format(self.epic_ids_filepath))
        if len(epic_ids) < 1:
            logging.error("Epic list is empty!")
        return epic_ids

    def start(self, argv):
        """
        Starts the strategy
        """
        epicList = self.get_epic_ids()
        shuffle(epicList)

        while True:
            if Utils.is_market_open(self.time_zone):

                # Process open positions
                self.positions = self.IG.get_open_positions()
                self.process_open_positions(self.positions)

                logging.info("Processing epic list of length: {}".format(len(epicList)))
                for epic in epicList:
                    percent_used = self.IG.get_account_used_perc()
                    if percent_used >= self.max_account_usable:
                        logging.warning("Stop trading because {}% of account is used".format(str(percent_used)))
                        break
                    if not Utils.is_market_open(self.time_zone):
                        logging.warn("Market is closed: stop processing")
                        break
                    logging.info("Processing {}".format(epic))
                    trade, limit, stop = self.strategy.find_trade_signal(epic)
                    self.process_trade(epic, trade, limit, stop)
                    time.sleep(self.timeout)
                # Wait for next spin loop as configured in the strategy
                seconds = self.strategy.get_seconds_to_next_spin()
                logging.info("Epics analysis complete. Wait for {0:.2f} seconds before next spin".format(seconds/3600))
                time.sleep(seconds)
            else:
                self.wait_for_next_market_opening()

    def close_open_posistions(self):
        """
        Closes all the open positions in the account
        """
        logging.info("Closing all the open positions...")
        if self.IG.close_all_positions():
            logging.info("All the posisions have been closed.")
        else:
            logging.error("Impossible to close all open positions, retry.")

    def wait_for_next_market_opening(self):
        """
        Sleep until the next market opening. Takes into account weekends
        and bank holidays in UK
        """
        seconds = Utils.get_seconds_to_market_opening()
        logging.info("Market is closed! Wait for {0:.2f} hours...".format(seconds / 3600))
        time.sleep(seconds)

    def process_trade(self, epic, trade, limit, stop):
        """
        Process a trade checking if it is a "close position" trade or a new action
        """
        if trade is not TradeDirection.NONE:
            if self.positions is not None:
                for item in self.positions['positions']:
                    # If a same direction trade already exist, don't trade
                    if item['market']['epic'] == epic and trade.name == item['position']['direction']:
                        logging.info( "There is already an open position for this epic, skip trade")
                        return False
                    # If a trade in opposite direction exist, close the position
                    elif item['market']['epic'] == epic and trade.name != item['position']['direction']:
                        return self.IG.close_position(item)
                return self.IG.trade(epic, trade.name, limit, stop)
            else:
                logging.error(
                    "Unable to fetch open positions! Avoid trading this epic")
        return False

    def process_open_positions(self, positions):
        """
        process the open positions to find closing trades

            - **positions**: json object containing open positions
            - Returns **False** if an error occurs otherwise True
        """
        if positions is not None:
            logging.info("Processing open positions.")
            for item in positions['positions']:
                epic = item['market']['epic']
                trade, limit, stop = self.strategy.find_trade_signal(epic)
                self.process_trade(epic, trade, limit, stop)
                time.sleep(self.timeout)
            return True
        else:
            logging.warning("Unable to fetch open positions!")
        return False
