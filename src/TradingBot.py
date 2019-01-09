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

from Utils import Utils, TradeDirection, MarketSource
from Interfaces.IGInterface import IGInterface
from Interfaces.AVInterface import AVInterface
from Strategies.StrategyFactory import StrategyFactory

class TradingBot:
    """
    Class that initialise and hold references of main components like the
    broker interface, the strategy or the epic_ids list
    """

    def __init__(self):
        # Set timezone
        set(pytz.all_timezones_set)

        # Load configuration
        config = self.load_json_file('../config/config.json')
        self.read_configuration(config)

        # Read credentials file
        credentials = self.load_json_file(self.credentials_filepath)

        # Setup the global logger
        self.setup_logging()

        # Positions container
        self.positions = None

        # Init trade services
        services = self.init_trading_services(config, credentials)

        # Create strategy from the factory class
        self.strategy = StrategyFactory(config, services).make_strategy(
            self.active_strategy)


    def load_json_file(self, filepath):
        """
        Load a JSON formatted file from the given filepath

            - **filepath** The filepath including filename and extension
            - Return a dictionary of the loaded json
        """
        try:
            with open(filepath, 'r') as file:
                return json.load(file)
        except IOError:
            logging.error("File not found ({})".format(filepath))
            exit()


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
        self.market_source = MarketSource(config['general']['market_source']['value'])
        self.watchlist_name = config['general']['watchlist_name']
        # AlphaVantage limits to 5 calls per minute
        self.timeout = 12 if self.use_av_api else 1
        self.active_strategy = config['general']['active_strategy']


    def setup_logging(self):
        """
        Setup the global logging settings
        """
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


    def init_trading_services(self, config, credentials):
        """
        Create instances of the trading services required, such as web interface
        for trading and fetch market data.

            - **config** The configuration json
            - **credentials** The credentials json
        """
        # Create IG interface
        self.IG = IGInterface(config)
        # Init the IG interface
        if not self.IG.authenticate(credentials):
            logging.error("Authentication failed")
            exit()

        # Init AlphaVantage interface
        self.AV = AVInterface(credentials['av_api_key'])

        # Create dict of services
        return {
            "broker": self.IG,
            "alpha_vantage": self.AV
        }


    def load_epic_ids_from_local_file(self, filepath):
        """
        Read a file from filesystem containing a list of epic ids.
        The filepath is defined in config.json file
        Returns a 'list' of strings where each string is a market epic
        """
        # define empty list
        epic_ids = []
        try:
            # open file and read the content in a list
            with open(filepath, 'r') as filehandle:
                filecontents = filehandle.readlines()
                for line in filecontents:
                    # remove linebreak which is the last character of the string
                    current_epic_id = line[:-1]
                    epic_ids.append(current_epic_id)
        except IOError:
            # Create the file empty
            logging.error('{} does not exist!'.format(filepath))
        if len(epic_ids) < 1:
            logging.error("Epic list is empty!")
        return epic_ids


    def start(self, argv):
        """
        Starts the TradingBot
        """
        while True:
            if Utils.is_market_open(self.time_zone):
                # Process open positions
                self.positions = self.IG.get_open_positions()
                self.process_open_positions(self.positions)

                if self.market_source == MarketSource.LIST:
                    self.process_epic_list(
                        self.load_epic_ids_from_local_file(
                            self.epic_ids_filepath))
                elif self.market_source == MarketSource.WATCHLIST:
                    self.process_watchlist(self.watchlist_name)
                elif self.market_source == MarketSource.API:
                    # Calling with empty strings starts market navigation from highest level
                    self.process_market_exploration('180500')

                # Wait for next spin loop as configured in the strategy
                seconds = self.strategy.get_seconds_to_next_spin()
                logging.info("Wait for {0:.2f} seconds before next spin".format(seconds))
                time.sleep(seconds)
            else:
                self.wait_for_next_market_opening()


    def process_watchlist(self, watchlist_name):
        """
        Process the markets included in the given IG watchlist

            - **watchlist_name**: IG watchlist name
        """
        markets = self.IG.get_markets_from_watchlist(self.watchlist_name)
        if markets is None:
            logging.error("Watchlist {} not found!".format(watchlist_name))
            return
        for m in markets:
            if not self.process_market(m['epic']):
                return


    def process_market_exploration(self, node_id):
        """
        Navigate the markets using IG API to fetch markets id dinamically

            - **node_id**: The node id to navigate markets in
        """
        node = self.IG.navigate_market_node(node_id)
        if 'nodes' in node and isinstance(node['nodes'], list):
            for node in node['nodes']:
                self.process_market_exploration(node['id'])
        if 'markets' in node and isinstance(node['markets'], list):
            for market in node['markets']:
                if any(["DFB" in str(market['epic']),
                        "TODAY" in str(market['epic']),
                        "DAILY" in str(market['epic'])]):
                    if not self.process_market(market['epic']):
                        return


    def process_epic_list(self, epic_list):
        """
        Process the given list of epic ids, one by one to find new trades

            - **epic_list**: list of epic ids as strings
        """
        shuffle(epic_list)
        logging.info("Processing epic list of length: {}".format(len(epic_list)))
        for epic in epic_list:
            if not self.process_market(epic):
                return


    def process_market(self, epic):
        """
        Process the givem epic using the defined strategy

            - **epic**: string representing a market epic id
            - Returns **False** if market is closed or if account reach maximum margin, otherwise **True**
        """
        percent_used = self.IG.get_account_used_perc()
        if percent_used >= self.max_account_usable:
            logging.warning("Stop trading because {}% of account is used".format(str(percent_used)))
            return False
        if not Utils.is_market_open(self.time_zone):
            logging.warn("Market is closed: stop processing")
            return False
        self.process_trade(epic)
        return True


    def close_open_positions(self):
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
        seconds = Utils.get_seconds_to_market_opening(dt.datetime.now())
        logging.info("Market is closed! Wait for {0:.2f} hours...".format(seconds / 3600))
        time.sleep(seconds)


    def process_trade(self, epic):
        """
        Process a trade checking if it is a "close position" trade or a new action
        """
        logging.info("Processing {}".format(epic))
        # Use strategy to analyse market
        try:
            trade, limit, stop = self.strategy.find_trade_signal(epic)
        except Exception as e:
            logging.error('Exception: {}'.format(e))
            trade = TradeDirection.NONE

        if trade is not TradeDirection.NONE:
            if self.positions is not None:
                for item in self.positions['positions']:
                    # If a same direction trade already exist, don't trade
                    if item['market']['epic'] == epic and trade.name == item['position']['direction']:
                        logging.info( "There is already an open position for this epic, skip trade")
                    # If a trade in opposite direction exist, close the position
                    elif item['market']['epic'] == epic and trade.name != item['position']['direction']:
                        self.IG.close_position(item)
                self.IG.trade(epic, trade.name, limit, stop)
            else:
                logging.error(
                    "Unable to fetch open positions! Avoid trading this epic")
        # Sleep for the defined timeout
        time.sleep(self.timeout)


    def process_open_positions(self, positions):
        """
        process the open positions to find closing trades

            - **positions**: json object containing open positions
            - Returns **False** if an error occurs otherwise True
        """
        if positions is not None:
            logging.info("Processing open positions.")
            self.process_epic_list([item['market']['epic'] for item in positions['positions']])
            return True
        else:
            logging.warning("Unable to fetch open positions!")
        return False
