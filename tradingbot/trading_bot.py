import logging
import traceback
from datetime import datetime as dt
from pathlib import Path
from typing import List, Optional

import pytz

from .components import (
    Backtester,
    Configuration,
    MarketClosedException,
    MarketProvider,
    NotSafeToTradeException,
    TimeAmount,
    TimeProvider,
    TradeDirection,
)
from .components.broker import Broker, BrokerFactory
from .interfaces import Market, Position
from .strategies import StrategyFactory, StrategyImpl


class TradingBot:
    """
    Class that initialise and hold references of main components like the
    broker interface, the strategy or the epic_ids list
    """

    time_provider: TimeProvider
    config: Configuration
    broker: Broker
    strategy: StrategyImpl
    market_provider: MarketProvider

    def __init__(
        self,
        time_provider: Optional[TimeProvider] = None,
        config_filepath: Optional[Path] = None,
    ) -> None:
        # Time manager
        self.time_provider = time_provider if time_provider else TimeProvider()
        # Set timezone
        set(pytz.all_timezones_set)

        # Load configuration
        self.config = Configuration.from_filepath(config_filepath)

        # Setup the global logger
        self.setup_logging()

        # Init trade services and create the broker interface
        # The Factory is used to create the services from the configuration file
        self.broker = Broker(BrokerFactory(self.config))

        # Create strategy from the factory class
        self.strategy = StrategyFactory(
            self.config, self.broker
        ).make_from_configuration()

        # Create the market provider
        self.market_provider = MarketProvider(self.config, self.broker)

    def setup_logging(self) -> None:
        """
        Setup the global logging settings
        """
        # Clean logging handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Define the global logging settings
        debugLevel = (
            logging.DEBUG if self.config.is_logging_debug_enabled() else logging.INFO
        )
        if self.config.is_logging_enabled():
            log_filename = self.config.get_log_filepath()
            Path(log_filename).parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                filename=log_filename,
                level=debugLevel,
                format="[%(asctime)s] %(levelname)s: %(message)s",
            )
        else:
            logging.basicConfig(
                level=debugLevel, format="[%(asctime)s] %(levelname)s: %(message)s"
            )

    def start(self, single_pass=False) -> None:
        """
        Starts the TradingBot main loop
        - process open positions
        - process markets from market source
        - wait for configured wait time
        - start over
        """
        if single_pass:
            logging.info("Performing a single iteration of the market source")
        while True:
            try:
                # Process current open positions
                self.process_open_positions()
                # Now process markets from the configured market source
                self.process_market_source()
                # Wait for the next spin before starting over
                self.time_provider.wait_for(
                    TimeAmount.SECONDS, self.config.get_spin_interval()
                )
                if single_pass:
                    break
            except MarketClosedException:
                logging.warning("Market is closed: stop processing")
                if single_pass:
                    break
                self.time_provider.wait_for(TimeAmount.NEXT_MARKET_OPENING)
            except NotSafeToTradeException:
                if single_pass:
                    break
                self.time_provider.wait_for(
                    TimeAmount.SECONDS, self.config.get_spin_interval()
                )
            except StopIteration:
                if single_pass:
                    break
                self.time_provider.wait_for(
                    TimeAmount.SECONDS, self.config.get_spin_interval()
                )
            except Exception as e:
                logging.error("Generic exception caught: {}".format(e))
                logging.error(traceback.format_exc())
                if single_pass:
                    break

    def process_open_positions(self) -> None:
        """
        Fetch open positions markets and run the strategy against them closing the
        trades if required
        """
        positions = self.broker.get_open_positions()
        # Do not run until we know the current open positions
        if positions is None:
            logging.warning("Unable to fetch open positions! Will try again...")
            raise RuntimeError("Unable to fetch open positions")
        for epic in [item.epic for item in positions]:
            market = self.market_provider.get_market_from_epic(epic)
            self.process_market(market, positions)

    def process_market_source(self) -> None:
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

    def process_market(self, market: Market, open_positions: List[Position]) -> None:
        """Spin the strategy on all the markets"""
        if not self.config.is_paper_trading_enabled():
            self.safety_checks()
        logging.info("Processing {}".format(market.id))
        try:
            self.strategy.set_open_positions(open_positions)
            trade, limit, stop = self.strategy.run(market)
            self.process_trade(market, trade, limit, stop, open_positions)
        except Exception as e:
            logging.error("Strategy exception caught: {}".format(e))
            logging.debug(traceback.format_exc())
            return

    def close_open_positions(self) -> None:
        """
        Closes all the open positions in the account
        """
        logging.info("Closing all the open positions...")
        if self.broker.close_all_positions():
            logging.info("All the posisions have been closed.")
        else:
            logging.error("Impossible to close all open positions, retry.")

    def safety_checks(self) -> None:
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
        if percent_used >= self.config.get_max_account_usable():
            logging.warning(
                "Stop trading because {}% of account is used".format(str(percent_used))
            )
            raise NotSafeToTradeException()
        if not self.time_provider.is_market_open(self.config.get_time_zone()):
            raise MarketClosedException()

    def process_trade(
        self,
        market: Market,
        direction: TradeDirection,
        limit: Optional[float],
        stop: Optional[float],
        open_positions: List[Position],
    ) -> None:
        """
        Process a trade checking if it is a "close position" trade or a new trade
        """
        # Perform trade only if required
        if direction is TradeDirection.NONE or limit is None or stop is None:
            return

        for item in open_positions:
            # If a same direction trade already exist, don't trade
            if item.epic == market.epic and direction is item.direction:
                logging.info(
                    "There is already an open position for this epic, skip trade"
                )
                return
            # If a trade in opposite direction exist, close the position
            elif item.epic == market.epic and direction is not item.direction:
                self.broker.close_position(item)
                return
        self.broker.trade(market.epic, direction, limit, stop)

    def backtest(
        self,
        market_id: str,
        start_date: str,
        end_date: str,
        epic_id: Optional[str] = None,
    ) -> None:
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
                if epic_id is None or epic_id == ""
                else self.market_provider.get_market_from_epic(epic_id)
            )
        except Exception as e:
            logging.error(e)
            exit(1)

        bt.start(market, start, end)
        bt.print_results()
