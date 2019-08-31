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
import traceback
import argparse
import numpy

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Utility.Utils import Utils, TradeDirection, NotSafeToTradeException, MarketClosedException
from Interfaces.IGInterface import IGInterface
from Interfaces.AVInterface import AVInterface
from Strategies.StrategyFactory import StrategyFactory
from Interfaces.Broker import Broker
from Interfaces.MarketProvider import MarketProvider, MarketSource


class TradingBot:
    """
    Class that initialise and hold references of main components like the
    broker interface, the strategy or the epic_ids list
    """

    def __init__(self):
        # Set timezone
        set(pytz.all_timezones_set)

        # Load configuration
        home_path = os.path.expanduser("~")
        config_filepath = "{}/.TradingBot/config/config.json".format(home_path)
        config = self.load_json_file(config_filepath)
        self.read_configuration(config)

        # Read credentials file
        credentials = self.load_json_file(self.credentials_filepath)

        # Setup the global logger
        self.setup_logging()

        # Positions container
        self.positions = None

        # Init trade services and create the broker interface
        self.broker = self.init_trading_services(config, credentials)

        # Create strategy from the factory class
        self.strategy = StrategyFactory(config, self.broker).make_strategy(
            self.active_strategy
        )

        # Create the market provider
        self.market_provider = MarketProvider(config, self.broker)

    def load_json_file(self, filepath):
        """
        Load a JSON formatted file from the given filepath

            - **filepath** The filepath including filename and extension
            - Return a dictionary of the loaded json
        """
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except IOError:
            logging.error("File not found ({})".format(filepath))
            exit()

    def read_configuration(self, config):
        """
        Read the configuration from the config json
        """
        home = os.path.expanduser("~")
        self.epic_ids_filepath = config["general"]["epic_ids_filepath"].replace(
            "{home}", home
        )
        self.credentials_filepath = config["general"]["credentials_filepath"].replace(
            "{home}", home
        )
        self.debug_log = config["general"]["debug_log"]
        self.enable_log = config["general"]["enable_log"]
        self.log_file = config["general"]["log_file"].replace("{home}", home)
        self.time_zone = config["general"]["time_zone"]
        self.max_account_usable = config["general"]["max_account_usable"]
        self.active_strategy = config["general"]["active_strategy"]

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
            time_suffix = time_str.replace(":", "_").replace(".", "_")
            log_filename = log_filename.replace("{timestamp}", time_suffix)
            os.makedirs(os.path.dirname(log_filename), exist_ok=True)
            logging.basicConfig(
                filename=log_filename,
                level=debugLevel,
                format="[%(asctime)s] %(levelname)s: %(message)s",
            )
        else:
            logging.basicConfig(
                level=debugLevel, format="[%(asctime)s] %(levelname)s: %(message)s"
            )

    def init_trading_services(self, config, credentials):
        """
        Create instances of the trading services required, such as web interface
        for trading and fetch market data.

            - **config** The configuration json
            - **credentials** The credentials json
            - return: An instance of Broker class initialised
        """
        services = {
            "ig_index": IGInterface(config, credentials),
            "alpha_vantage": AVInterface(credentials["av_api_key"], config),
        }
        return Broker(config, services)

    def start(self):
        """
        Starts the TradingBot main loop
        - process open positions
        - process markets from market source
        - wait for configured wait time
        - start over
        """
        while True:
            try:
                # Process current open positions
                self.process_open_positions()
                # Now process markets from the configured market source
                self.process_market_source()
            except MarketClosedException:
                self.wait_for_next_market_opening()
            except NotSafeToTradeException:
                self.wait_for_strategy_spin_period()
            except StopIteration:
                self.wait_for_strategy_spin_period()
            except Exception as e:
                logging.error("Generic exception caught: {}".format(e))
                logging.debug(traceback.format_exc())
                logging.debug(sys.exc_info()[0])
                continue

    def process_open_positions(self):
        """
        Fetch open positions markets and run the strategy against them closing the
        trades if required
        """
        self.positions = self.broker.get_open_positions()
        # Do not run until we know the current open positions
        if self.positions is None:
            logging.warning("Unable to fetch open positions! Will try again...")
            raise RuntimeError("Unable to fetch open positions")
        for epic in [item["market"]["epic"] for item in positions["positions"]]:
            market = self.market_provider.get_market_from_epic(epic)
            self.process_market(market)

    def process_market_source(self):
        """
        Process markets from the configured market source
        """
        while True:
            market = self.market_provider.next()
            self.process_market(market)

    def process_market(self, market):
        """Spin the strategy on all the markets"""
        self.safety_checks()
        logging.info("Processing {}".format(market.id))
        try:
            # TODO pass also open positions
            trade, limit, stop = self.strategy.run(market)
        except Exception as e:
            logging.error("Strategy exception caught: {}".format(e))
            logging.debug(traceback.format_exc())
            logging.debug(sys.exc_info()[0])
            return
        self.process_trade(market, trade, limit, stop)

    def close_open_positions(self):
        """
        Closes all the open positions in the account
        """
        logging.info("Closing all the open positions...")
        if self.broker.close_all_positions():
            logging.info("All the posisions have been closed.")
        else:
            logging.error("Impossible to close all open positions, retry.")

    def wait_for_next_market_opening(self):
        """
        Sleep until the next market opening. Takes into account weekends
        and bank holidays in UK
        """
        seconds = Utils.get_seconds_to_market_opening(dt.datetime.now())
        logging.info(
            "Market is closed! Wait for {0:.2f} hours...".format(seconds / 3600)
        )
        time.sleep(seconds)

    def wait_for_strategy_spin_period(self):
        """
        Sleep for the amount of time configured in the active strategy between each spin
        """
        # Wait for next spin loop as configured in the strategy
        seconds = self.strategy.get_seconds_to_next_spin()
        logging.info(
            "Wait for {0:.2f} seconds before next spin".format(seconds)
        )
        time.sleep(seconds)

    def safety_checks(self):
        """
        Perform some safety checks before running the strategy against the next market

        Return True if the trade can proceed, False otherwise
        """
        percent_used = self.broker.get_account_used_perc()
        if percent_used is None:
            logging.warning(
                "Stop trading because can't fetch percentage of account used"
            )
            raise NotSafeToTradeException()
        if percent_used >= self.max_account_usable:
            logging.warning(
                "Stop trading because {}% of account is used".format(str(percent_used))
            )
            raise NotSafeToTradeException()
        if not Utils.is_market_open(self.time_zone):
            logging.warning("Market is closed: stop processing")
            raise MarketClosedException()

    def process_trade(self, market, direction, limit, stop):
        """
        Process a trade checking if it is a "close position" trade or a new action
        """
        # TODO double check if there are pieces to remove
        # Perform trade only if required
        if direction is not TradeDirection.NONE:
            if self.positions is not None:
                for item in self.positions["positions"]:
                    # If a same direction trade already exist, don't trade
                    if (
                        item["market"]["epic"] == market.epic
                        and direction.name == item["position"]["direction"]
                    ):
                        logging.info(
                            "There is already an open position for this epic, skip trade"
                        )
                    # If a trade in opposite direction exist, close the position
                    elif (
                        item["market"]["epic"] == market.epic
                        and direction.name != item["position"]["direction"]
                    ):
                        self.broker.close_position(item)
                self.broker.trade(market.epic, direction.name, limit, stop)
            else:
                logging.error("Unable to fetch open positions! Avoid trading this epic")


if __name__ == "__main__":
    # Argument management
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--close_positions",
        help="Close all the open positions",
        action="store_true",
    )
    args = parser.parse_args()

    if args.close_positions:
        TradingBot().close_open_positions()
    else:
        TradingBot().start()
