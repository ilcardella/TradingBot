import logging
from datetime import datetime

from ..components import Configuration, Interval, TradeDirection
from ..components.broker import Broker
from ..interfaces import Market
from . import BacktestResult, DataPoints, Strategy, TradeSignal


class SimpleBollingerBands(Strategy):
    def __init__(self, config: Configuration, broker: Broker) -> None:
        super().__init__(config, broker)
        logging.info("Simple Bollinger Bands strategy initialised.")

    def read_configuration(self, config: Configuration) -> None:
        """
        Read the json configuration
        """
        raw = config.get_raw_config()
        self.max_spread_perc = raw["strategies"]["simple_boll_bands"]["max_spread_perc"]
        self.limit_p = raw["strategies"]["simple_boll_bands"]["limit_perc"]
        self.stop_p = raw["strategies"]["simple_boll_bands"]["stop_perc"]

    def initialise(self) -> None:
        """
        Initialise the strategy
        """
        pass

    def fetch_datapoints(self, market: Market) -> DataPoints:
        """
        Fetch historic prices up to 20 day in the past
        """
        return self.broker.get_prices(market, Interval.DAY, 20)

    def find_trade_signal(self, market: Market, datapoints: DataPoints) -> TradeSignal:
        return TradeDirection.NONE, None, None

    def backtest(
        self, market: Market, start_date: datetime, end_date: datetime
    ) -> BacktestResult:
        return BacktestResult()
