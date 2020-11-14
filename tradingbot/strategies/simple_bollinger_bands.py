import logging
from datetime import datetime

import pandas

from ..components import Configuration, Interval, TradeDirection, Utils
from ..components.broker import Broker
from ..interfaces import Market, MarketHistory
from . import BacktestResult, Strategy, TradeSignal


class SimpleBollingerBands(Strategy):
    """Simple strategy that calculate the Bollinger Bands of the given market using
    the price moving average and triggering BUY or SELL signals when the last closed
    price crosses the upper or lower bands
    """

    def __init__(self, config: Configuration, broker: Broker) -> None:
        super().__init__(config, broker)
        logging.info("Simple Bollinger Bands strategy created")

    def read_configuration(self, config: Configuration) -> None:
        """
        Read the json configuration
        """
        raw = config.get_raw_config()
        self.window = raw["strategies"]["simple_boll_bands"]["window"]
        self.limit_p = raw["strategies"]["simple_boll_bands"]["limit_perc"]
        self.stop_p = raw["strategies"]["simple_boll_bands"]["stop_perc"]

    def initialise(self) -> None:
        """
        Initialise the strategy
        """
        logging.info("Simple Bollinger Bands strategy initialised")

    def fetch_datapoints(self, market: Market) -> MarketHistory:
        """
        Fetch historic prices up to 20 day in the past
        """
        return self.broker.get_prices(market, Interval.DAY, self.window)

    def find_trade_signal(
        self, market: Market, datapoints: MarketHistory
    ) -> TradeSignal:
        df = datapoints.dataframe[: self.window * 2].copy()
        indexer = pandas.api.indexers.FixedForwardWindowIndexer(window_size=self.window)
        # 1. Compute the price moving averate
        df["MA"] = df[MarketHistory.CLOSE_COLUMN].rolling(window=indexer).mean()
        # 2. Compute the prices standard deviation
        # set .std(ddof=0) for population std instead of sample
        df["STD"] = df[MarketHistory.CLOSE_COLUMN].rolling(window=indexer).std()
        # 1. Compute upper band
        df["Upper_Band"] = df["MA"] + (df["STD"] * 2)
        # 2. Compute lower band
        df["Lower_Band"] = df["MA"] - (df["STD"] * 2)
        # 3. Compare the last price with the band boundaries and trigger signals
        if df[MarketHistory.CLOSE_COLUMN].iloc[1] < df["Lower_Band"].iloc[1]:
            return self._buy(market.offer, market.bid)
        # elif df[MarketHistory.CLOSE_COLUMN].iloc[1] > df["Upper_Band"].iloc[1]:
        #     return self._buy(market.offer, market.bid)
        return TradeDirection.NONE, None, None

    def _buy(self, offer: float, bid: float) -> TradeSignal:
        direction = TradeDirection.BUY
        limit = offer + Utils.percentage_of(self.limit_p, offer)
        stop = bid - Utils.percentage_of(self.stop_p, bid)
        return direction, limit, stop

    def _sell(self, offer: float, bid: float) -> TradeSignal:
        direction = TradeDirection.SELL
        limit = bid - Utils.percentage_of(self.limit_p, bid)
        stop = offer + Utils.percentage_of(self.stop_p, offer)
        return direction, limit, stop

    def backtest(
        self, market: Market, start_date: datetime, end_date: datetime
    ) -> BacktestResult:
        return BacktestResult()
