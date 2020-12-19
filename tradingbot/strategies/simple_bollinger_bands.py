import logging
from datetime import datetime

# import matplotlib.pyplot as plt
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
        Fetch historic prices
        """
        return self.broker.get_prices(market, Interval.DAY, self.window * 2)

    def find_trade_signal(
        self, market: Market, datapoints: MarketHistory
    ) -> TradeSignal:
        # Copy only the required amount of data
        df = datapoints.dataframe[: self.window * 2].copy()
        indexer = pandas.api.indexers.FixedForwardWindowIndexer(window_size=self.window)
        # Compute the price moving averate
        df["MA"] = df[MarketHistory.CLOSE_COLUMN].rolling(window=indexer).mean()
        # Compute the prices standard deviation
        # set .std(ddof=0) for population std instead of sample
        df["STD"] = df[MarketHistory.CLOSE_COLUMN].rolling(window=indexer).std()
        # Compute upper band
        df["Upper_Band"] = df["MA"] + (df["STD"] * 2)
        # Compute lower band
        df["Lower_Band"] = df["MA"] - (df["STD"] * 2)

        # self._plot(df)

        # Compare the last price with the band boundaries and trigger signals
        cross_lower_band_and_back = (
            df[MarketHistory.CLOSE_COLUMN].iloc[0] > df["Lower_Band"].iloc[0]
        ) and (df[MarketHistory.CLOSE_COLUMN].iloc[1] <= df["Lower_Band"].iloc[1])
        stable_below_ma = (
            df[MarketHistory.CLOSE_COLUMN].iloc[0:5] < df["MA"].iloc[0:5]
        ).all()

        if any([cross_lower_band_and_back, stable_below_ma]):
            return self._buy_signal(market)
        return TradeDirection.NONE, None, None

    def _buy_signal(self, market: Market) -> TradeSignal:
        direction = TradeDirection.BUY
        limit = market.offer + Utils.percentage_of(self.limit_p, market.offer)
        stop = market.bid - Utils.percentage_of(self.stop_p, market.bid)
        return direction, limit, stop

    def _sell_signal(self, market: Market) -> TradeSignal:
        direction = TradeDirection.SELL
        limit = market.bid - Utils.percentage_of(self.limit_p, market.bid)
        stop = market.offer + Utils.percentage_of(self.stop_p, market.offer)
        return direction, limit, stop

    # def _plot(self, dataframe: pandas.DataFrame):
    #     ax = plt.gca()
    #     dataframe.plot(
    #         kind="line",
    #         x=MarketHistory.DATE_COLUMN,
    #         y=MarketHistory.CLOSE_COLUMN,
    #         ax=ax,
    #         color="blue",
    #     )
    #     dataframe.plot(
    #         kind="line", x=MarketHistory.DATE_COLUMN, y="Lower_Band", ax=ax, color="red"
    #     )
    #     dataframe.plot(
    #         kind="line", x=MarketHistory.DATE_COLUMN, y="Upper_Band", ax=ax, color="red"
    #     )
    #     dataframe.plot(
    #         kind="line", x=MarketHistory.DATE_COLUMN, y="MA", ax=ax, color="green"
    #     )
    #     plt.show()

    def backtest(
        self, market: Market, start_date: datetime, end_date: datetime
    ) -> BacktestResult:
        return BacktestResult()
