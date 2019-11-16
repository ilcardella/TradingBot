import logging
import json
import pytz
import time
from datetime import datetime as dt
import os
import sys
import inspect
import traceback
import argparse
import numpy

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Utility.Utils import (
    Utils,
    TradeDirection,
    NotSafeToTradeException,
    MarketClosedException,
)
from Components.IGInterface import IGInterface
from Components.AVInterface import AVInterface
from Strategies.StrategyFactory import StrategyFactory
from Components.Broker import Broker
from Components.MarketProvider import MarketProvider, MarketSource
from Components.Backtester import Backtester
from Components.TimeProvider import TimeProvider, TimeAmount


class TradingBot:
    """
    Class that initialise and hold references of main components like the
    broker interface, the strategy or the epic_ids list
    """

    def __init__(self, time_provider=None, config_filepath=None):
        # Time manager
        self.time_provider = time_provider if time_provider else TimeProvider()
        # Set timezone
        set(pytz.all_timezones_set)

        # Load configuration
        if config_filepath is None:
            home_path = os.path.expanduser("~")
            config_filepath = "{}/.TradingBot/config/config.json".format(home_path)
        config = self.load_json_file(config_filepath)
        self.read_configuration(config)

        # Read credentials file
        credentials = self.load_json_file(self.credentials_filepath)

        # Setup the global logger
        self.setup_logging()

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
            exit(1)

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
        self.spin_interval = config["general"]["spin_interval"]

    def setup_logging(self):
        """
        Setup the global logging settings
        """
        # Clean logging handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Define the global logging settings
        debugLevel = logging.DEBUG if self.debug_log else logging.INFO
        # If enabled define log file filename with current timestamp
        if self.enable_log:
            log_filename = self.log_file
            time_str = dt.now().isoformat()
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
                # Wait for the next spin before starting over
                self.time_provider.wait_for(TimeAmount.SECONDS, self.spin_interval)
            except MarketClosedException:
                logging.warning("Market is closed: stop processing")
                self.time_provider.wait_for(TimeAmount.NEXT_MARKET_OPENING)
            except NotSafeToTradeException:
                self.time_provider.wait_for(TimeAmount.SECONDS, self.spin_interval)
            except StopIteration:
                self.time_provider.wait_for(TimeAmount.SECONDS, self.spin_interval)
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
        positions = self.broker.get_open_positions()
        # Do not run until we know the current open positions
        if positions is None:
            logging.warning("Unable to fetch open positions! Will try again...")
            raise RuntimeError("Unable to fetch open positions")
        for epic in [item["market"]["epic"] for item in positions["positions"]]:
            market = self.market_provider.get_market_from_epic(epic)
            self.process_market(market, positions)

    def process_market_source(self):
        """
        Process markets from the configured market source
        """
        while True:
            market = self.market_provider.next()
            positions = self.broker.get_open_positions()
            if positions is None:
                logging.warning("Unable to fetch open positions! Will try again...")
                raise RuntimeError("Unable to fetch open positions")
            self.process_market(market, positions)

    def process_market(self, market, open_positions):
        """Spin the strategy on all the markets"""
        self.safety_checks()
        logging.info("Processing {}".format(market.id))
        try:
            self.strategy.set_open_positions(open_positions)
            trade, limit, stop = self.strategy.run(market)
            self.process_trade(market, trade, limit, stop, open_positions)
        except Exception as e:
            logging.error("Strategy exception caught: {}".format(e))
            logging.debug(traceback.format_exc())
            logging.debug(sys.exc_info()[0])
            return

    def close_open_positions(self):
        """
        Closes all the open positions in the account
        """
        logging.info("Closing all the open positions...")
        if self.broker.close_all_positions():
            logging.info("All the posisions have been closed.")
        else:
            logging.error("Impossible to close all open positions, retry.")

    def safety_checks(self):
        """
        Perform some safety checks before running the strategy against the next market

        Raise exceptions if not safe to trade
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
        if not self.time_provider.is_market_open(self.time_zone):
            raise MarketClosedException()

    def process_trade(self, market, direction, limit, stop, open_positions):
        """
        Process a trade checking if it is a "close position" trade or a new trade
        """
        # Perform trade only if required
        if direction is not TradeDirection.NONE:
            if open_positions is not None:
                for item in open_positions["positions"]:
                    # If a same direction trade already exist, don't trade
                    if (
                        item["market"]["epic"] == market.epic
                        and direction.name == item["position"]["direction"]
                    ):
                        logging.info(
                            "There is already an open position for this epic, skip trade"
                        )
                        return
                    # If a trade in opposite direction exist, close the position
                    elif (
                        item["market"]["epic"] == market.epic
                        and direction.name != item["position"]["direction"]
                    ):
                        self.broker.close_position(item)
                        return
                self.broker.trade(market.epic, direction.name, limit, stop)
            else:
                logging.error("Unable to fetch open positions! Avoid trading this epic")

    def backtest(self, market_id, start_date, end_date, epic_id=None):
        """
        Backtest a market using the configured strategy
        """
        try:
            start = dt.strptime(start_date, "%Y-%m-%d")
            end = dt.strptime(end_date, "%Y-%m-%d")
        except ValueError as e:
            logging.error("Wrong date format! Must be YYYY-MM-DD")
            logging.debug(e)
            exit(1)

        bt = Backtester(self.broker, self.strategy)

        try:
            market = (
                self.market_provider.search_market(market_id)
                if epic_id is None or epic_id is ""
                else self.market_provider.get_market_from_epic(epic_id)
            )
        except Exception as e:
            logging.error(e)
            exit(1)

        bt.start(market, start, end)
        bt.print_results()


def get_menu_parser():
    VERSION = "1.2.0"
    parser = argparse.ArgumentParser(prog="TradingBot")
    main_group = parser.add_mutually_exclusive_group()
    main_group.add_argument(
        "-v", "--version", action="version", version="%(prog)s {}".format(VERSION)
    )
    main_group.add_argument(
        "-c",
        "--close_positions",
        help="Close all the open positions",
        action="store_true",
    )
    backtest_group = parser.add_argument_group("Backtesting")
    backtest_group.add_argument(
        "--backtest",
        help="Backtest the market related to the specified id",
        nargs=1,
        metavar="MARKET_ID",
    )
    backtest_group.add_argument(
        "--epic",
        help="IG epic of the market to backtest. MARKET_ID will be ignored",
        nargs=1,
        metavar="EPIC_ID",
        default=None,
    )
    backtest_group.add_argument(
        "--start",
        help="Start date for the strategy backtest",
        nargs=1,
        metavar="YYYY-MM-DD",
        required="--backtest" in sys.argv,
    )
    backtest_group.add_argument(
        "--end",
        help="End date for the strategy backtest",
        nargs=1,
        metavar="YYYY-MM-DD",
        required="--backtest" in sys.argv,
    )
    return parser.parse_args()


def main():
    tp = TimeProvider()
    args = get_menu_parser()
    if args.close_positions:
        TradingBot(tp).close_open_positions()
    elif args.backtest and args.start and args.end:
        epic = args.epic[0] if args.epic else None
        TradingBot(tp).backtest(args.backtest[0], args.start[0], args.end[0], epic)
    else:
        TradingBot(tp).start()

if __name__ == "__main__":
    main()
