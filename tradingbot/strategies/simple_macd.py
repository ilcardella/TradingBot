import datetime
import logging
from typing import Tuple

import numpy as np
import pandas

from ..components import Configuration, Interval, TradeDirection
from ..components.broker import Broker
from ..interfaces import Market, MarketHistory
from . import BacktestResult, Strategy, TradeSignal


class SimpleMACD(Strategy):
    """
    Strategy that use the MACD technical indicator of a market to decide whether
    to buy, sell or hold.
    Buy when the MACD cross over the MACD signal and price is above 200 EMA.
    Sell when the MACD cross below the MACD signal and price is below 200 EMA.
    """

    def __init__(self, config: Configuration, broker: Broker) -> None:
        super().__init__(config, broker)
        logging.info("Simple MACD strategy initialised.")

    def read_configuration(self, config: Configuration) -> None:
        """
        Read the json configuration
        """
        raw = config.get_raw_config()
        strategy_config = raw.get("strategies", {}).get("simple_macd", {})
        self.max_spread_perc = strategy_config.get("max_spread_perc", 0.1)

        # Configuration for indicators
        self.ema_period = 200
        self.atr_period = 14
        self.atr_multiplier = 1.5
        self.risk_reward_ratio = 1.5

    def initialise(self) -> None:
        """
        Initialise SimpleMACD strategy
        """
        pass

    def fetch_datapoints(self, market: Market) -> MarketHistory:
        """
        Fetch historic data (prices) to calculate indicators.
        We need enough data for EMA 200.
        """
        return self.broker.get_prices(market, Interval.DAY, 300)

    def find_trade_signal(
        self, market: Market, datapoints: MarketHistory
    ) -> TradeSignal:
        """
        Calculate indicators and find trade signal based on MACD crossover + EMA trend filter.
        """
        if datapoints is None or len(datapoints.dataframe) < self.ema_period:
            logging.warning(f"Not enough data for {market.epic}")
            return TradeDirection.NONE, None, None

        df = self._calculate_indicators(datapoints.dataframe.copy())

        # Get latest completed candle
        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # Spread constraint
        if market.bid - market.offer > self.max_spread_perc:
            return TradeDirection.NONE, None, None

        signal = TradeDirection.NONE

        # Buy Signal:
        # 1. Price > EMA 200 (Trend Filter)
        # 2. MACD crosses above Signal (Prev Hist < 0 and Curr Hist > 0)
        if curr["close"] > curr["EMA200"]:
            if prev["Hist"] < 0 and curr["Hist"] > 0:
                signal = TradeDirection.BUY

        # Sell Signal:
        # 1. Price < EMA 200 (Trend Filter)
        # 2. MACD crosses below Signal (Prev Hist > 0 and Curr Hist < 0)
        elif curr["close"] < curr["EMA200"]:
            if prev["Hist"] > 0 and curr["Hist"] < 0:
                signal = TradeDirection.SELL

        if signal is not TradeDirection.NONE:
            logging.info(f"SimpleMACD says: {signal.name} {market.id}")
            limit, stop = self.calculate_stop_limit(
                signal, market.offer, market.bid, curr["ATR"]
            )
            return signal, limit, stop

        return TradeDirection.NONE, None, None

    def _calculate_indicators(self, df: pandas.DataFrame) -> pandas.DataFrame:
        # EMA 200
        df["EMA200"] = df["close"].ewm(span=self.ema_period, adjust=False).mean()

        # MACD (12, 26, 9)
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema12 - ema26
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["Hist"] = df["MACD"] - df["Signal"]

        # ATR
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        ranges = pandas.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df["ATR"] = true_range.rolling(self.atr_period).mean()

        return df

    def calculate_stop_limit(
        self,
        tradeDirection: TradeDirection,
        current_offer: float,
        current_bid: float,
        atr: float,
    ) -> Tuple[float, float]:
        """
        Calculate Stop Loss and Take Profit using ATR.
        """
        stop_loss_pips = atr * self.atr_multiplier

        if tradeDirection == TradeDirection.BUY:
            stop = current_bid - stop_loss_pips
            limit = current_offer + (stop_loss_pips * self.risk_reward_ratio)
        elif tradeDirection == TradeDirection.SELL:
            stop = current_offer + stop_loss_pips
            limit = current_bid - (stop_loss_pips * self.risk_reward_ratio)
        else:
            raise ValueError("Trade direction cannot be NONE")

        return limit, stop

    def backtest(
        self, market: Market, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> BacktestResult:
        """Backtest the strategy"""
        # TODO
        raise NotImplementedError("Work in progress")
