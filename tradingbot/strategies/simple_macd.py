import datetime
import logging
from typing import Tuple

import numpy as np
import pandas

from ..components import Configuration, Interval, TradeDirection, Utils
from ..components.broker import Broker
from ..interfaces import Market, MarketMACD
from . import BacktestResult, Strategy, TradeSignal


class SimpleMACD(Strategy):
    """
    Strategy that use the MACD technical indicator of a market to decide whether
    to buy, sell or hold.
    Buy when the MACD cross over the MACD signal.
    Sell when the MACD cross below the MACD signal.
    """

    def __init__(self, config: Configuration, broker: Broker) -> None:
        super().__init__(config, broker)
        logging.info("Simple MACD strategy initialised.")

    def read_configuration(self, config: Configuration) -> None:
        """
        Read the json configuration
        """
        raw = config.get_raw_config()
        self.max_spread_perc = raw["strategies"]["simple_macd"]["max_spread_perc"]
        self.limit_p = raw["strategies"]["simple_macd"]["limit_perc"]
        self.stop_p = raw["strategies"]["simple_macd"]["stop_perc"]

    def initialise(self) -> None:
        """
        Initialise SimpleMACD strategy
        """
        pass

    def fetch_datapoints(self, market: Market) -> MarketMACD:
        """
        Fetch historic MACD data
        """
        return self.broker.get_macd(market, Interval.DAY, 30)

    def find_trade_signal(self, market: Market, datapoints: MarketMACD) -> TradeSignal:
        """
        Calculate the MACD of the previous days and find a cross between MACD
        and MACD signal

            - **market**: Market object
            - **datapoints**: datapoints used to analyse the market
            - Returns TradeDirection, limit_level, stop_level or TradeDirection.NONE, None, None
        """
        limit_perc = self.limit_p
        stop_perc = max(market.stop_distance_min, self.stop_p)

        # Spread constraint
        if market.bid - market.offer > self.max_spread_perc:
            return TradeDirection.NONE, None, None

        # Find where macd and signal cross each other
        macd = datapoints
        px = self.generate_signals_from_dataframe(macd.dataframe)

        # Identify the trade direction looking at the last signal
        tradeDirection = self.get_trade_direction_from_signals(px)
        # Log only tradable epics
        if tradeDirection is not TradeDirection.NONE:
            logging.info(
                "SimpleMACD says: {} {}".format(tradeDirection.name, market.id)
            )
        else:
            return TradeDirection.NONE, None, None

        # Calculate stop and limit distances
        limit, stop = self.calculate_stop_limit(
            tradeDirection, market.offer, market.bid, limit_perc, stop_perc
        )
        return tradeDirection, limit, stop

    def calculate_stop_limit(
        self,
        tradeDirection: TradeDirection,
        current_offer: float,
        current_bid: float,
        limit_perc: float,
        stop_perc: float,
    ) -> Tuple[float, float]:
        """
        Calculate the stop and limit levels from the given percentages
        """
        limit = None
        stop = None
        if tradeDirection == TradeDirection.BUY:
            limit = current_offer + Utils.percentage_of(limit_perc, current_offer)
            stop = current_bid - Utils.percentage_of(stop_perc, current_bid)
        elif tradeDirection == TradeDirection.SELL:
            limit = current_bid - Utils.percentage_of(limit_perc, current_bid)
            stop = current_offer + Utils.percentage_of(stop_perc, current_offer)
        else:
            raise ValueError("Trade direction cannot be NONE")
        return limit, stop

    def generate_signals_from_dataframe(
        self, dataframe: pandas.DataFrame
    ) -> pandas.DataFrame:
        dataframe.loc[:, "positions"] = 0
        dataframe.loc[:, "positions"] = np.where(
            dataframe[MarketMACD.HIST_COLUMN] >= 0, 1, 0
        )
        dataframe.loc[:, "signals"] = dataframe["positions"].diff()
        return dataframe

    def get_trade_direction_from_signals(
        self, dataframe: pandas.DataFrame
    ) -> TradeDirection:
        tradeDirection = TradeDirection.NONE
        if len(dataframe["signals"]) > 0:
            if dataframe["signals"].iloc[1] < 0:
                tradeDirection = TradeDirection.BUY
            elif dataframe["signals"].iloc[1] > 0:
                tradeDirection = TradeDirection.SELL
        return tradeDirection

    def backtest(
        self, market: Market, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> BacktestResult:
        """Backtest the strategy"""
        # TODO
        raise NotImplementedError("Work in progress")
        # Generic initialisations
        trades = []
        # - Get price data for market
        prices = self.broker.get_prices(market, Interval.DAY, None)
        # - Get macd data from broker
        data = self.fetch_datapoints(market)
        # - Simulate time passing by starting with N rows (from the bottom)
        # and adding the next row (on the top) one by one, calling the strategy with
        # the intermediate data and recording its output
        datapoint_used = 26
        while len(data.dataframe) > datapoint_used:
            current_data = data.dataframe.tail(datapoint_used).copy()
            datapoint_used += 1
            # Get trade date
            trade_dt = current_data.index.values[0].astype("M8[ms]").astype("O")
            if start_date <= trade_dt <= end_date:
                trade, limit, stop = self.find_trade_signal(market, current_data)
                if trade is not TradeDirection.NONE:
                    try:
                        price = prices.loc[trade_dt.strftime("%Y-%m-%d"), "4. close"]
                        trades.append(
                            # [trade_dt.strftime("%Y-%m-%d"), trade, float(price)]
                            (trade_dt.strftime("%Y-%m-%d"), trade, float(price))
                        )
                    except Exception as e:
                        logging.debug(e)
                        continue
        if len(trades) < 2:
            raise Exception("Not enough trades for the given date range")
        # Iterate through trades and assess profit loss
        balance = 1000
        previous = trades[0]
        for trade in trades[1:]:
            if previous[1] is trade[1]:
                raise Exception("Error: sequencial trades with same direction")
            diff = trade[2] - previous[2]
            pl = 0
            if previous[1] is TradeDirection.BUY and trade[1] is TradeDirection.SELL:
                pl += diff if diff >= 0 else -diff
                # TODO consider stop and limit levels
            if previous[1] is TradeDirection.SELL and trade[1] is TradeDirection.BUY:
                pl += diff if diff < 0 else -diff
                # TODO consider stop and limit levels
            balance += pl
            previous = trade
        return {"balance": balance, "trades": trades}
