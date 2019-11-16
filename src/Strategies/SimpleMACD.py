import logging
import numpy as np
import os
import inspect
import sys
from datetime import datetime as dt

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from Components.Broker import Interval
from .Strategy import Strategy
from Utility.Utils import Utils, TradeDirection


class SimpleMACD(Strategy):
    """
    Strategy that use the MACD technical indicator of a market to decide whether
    to buy, sell or hold.
    Buy when the MACD cross over the MACD signal.
    Sell when the MACD cross below the MACD signal.
    """

    def __init__(self, config, broker):
        super().__init__(config, broker)
        logging.info("Simple MACD strategy initialised.")

    def read_configuration(self, config):
        """
        Read the json configuration
        """
        self.max_spread_perc = config["strategies"]["simple_macd"]["max_spread_perc"]
        self.limit_p = config["strategies"]["simple_macd"]["limit_perc"]
        self.stop_p = config["strategies"]["simple_macd"]["stop_perc"]

    def initialise(self):
        """
        Initialise SimpleMACD strategy
        """
        pass

    def fetch_datapoints(self, market):
        """
        Fetch historic MACD data
        """
        return self.broker.macd_dataframe(market.epic, market.id, Interval.DAY)

    def find_trade_signal(self, market, datapoints):
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
        px = datapoints
        px = self.generate_signals_from_dataframe(px)

        # Identify the trade direction looking at the last signal
        tradeDirection = self.get_trade_direction_from_signals(px)
        # Log only tradable epics
        if tradeDirection is not TradeDirection.NONE:
            logging.info(
                "SimpleMACD says: {} {}".format(tradeDirection.name, market.id)
            )

        # Calculate stop and limit distances
        limit, stop = self.calculate_stop_limit(
            tradeDirection, market.offer, market.bid, limit_perc, stop_perc
        )
        return tradeDirection, limit, stop

    def calculate_stop_limit(
        self, tradeDirection, current_offer, current_bid, limit_perc, stop_perc
    ):
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
        return limit, stop

    def generate_signals_from_dataframe(self, dataframe):
        dataframe.loc[:, "positions"] = 0
        dataframe.loc[:, "positions"] = np.where(dataframe["MACD_Hist"] >= 0, 1, 0)
        dataframe.loc[:, "signals"] = dataframe["positions"].diff()
        return dataframe

    def get_trade_direction_from_signals(self, dataframe):
        tradeDirection = TradeDirection.NONE
        if len(dataframe["signals"]) > 0:
            if dataframe["signals"].iloc[1] < 0:
                tradeDirection = TradeDirection.BUY
            elif dataframe["signals"].iloc[1] > 0:
                tradeDirection = TradeDirection.SELL
        return tradeDirection

    def backtest(self, market, start_date, end_date):
        """Backtest the strategy
        """
        # Generic initialisations
        self.broker.use_av_api = True
        trades = []
        # - Get price data for market
        prices = self.broker.get_prices(market.epic, market.id, Interval.DAY, None)
        # - Get macd data from broker forcing use of alpha_vantage
        data = self.fetch_datapoints(market)
        # - Simulate time passing by starting with N rows (from the bottom)
        # and adding the next row (on the top) one by one, calling the strategy with
        # the intermediate data and recording its output
        datapoint_used = 26
        while len(data) > datapoint_used:
            current_data = data.tail(datapoint_used).copy()
            datapoint_used += 1
            # Get trade date
            trade_dt = current_data.index.values[0].astype("M8[ms]").astype("O")
            if start_date <= trade_dt <= end_date:
                trade, limit, stop = self.find_trade_signal(market, current_data)
                if trade is not TradeDirection.NONE:
                    try:
                        price = prices.loc[trade_dt.strftime("%Y-%m-%d"), "4. close"]
                        trades.append(
                            [trade_dt.strftime("%Y-%m-%d"), trade, float(price)]
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
