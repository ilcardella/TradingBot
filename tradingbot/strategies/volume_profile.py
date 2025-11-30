import datetime
import logging
from typing import Dict, Tuple

import numpy as np
import pandas

from ..components import Configuration, Interval, TradeDirection
from ..components.broker import Broker
from ..interfaces import Market, MarketHistory
from . import BacktestResult, Strategy, TradeSignal


class VolumeProfile(Strategy):
    """
    Strategy based on Volume Profile and Order Flow analysis.

    Key Concepts:
    - Volume Profile: Identifies price levels with high trading activity (Value Areas)
    - Point of Control (POC): Price level with highest volume
    - Value Area High/Low (VAH/VAL): Boundaries containing 70% of volume
    - Order Flow Imbalance: Detects aggressive buying/selling pressure

    Entry Logic:
    - BUY: Price pulls back to VAL/POC with bullish order flow imbalance
    - SELL: Price rallies to VAH/POC with bearish order flow imbalance
    """

    def __init__(self, config: Configuration, broker: Broker) -> None:
        super().__init__(config, broker)
        logging.info("Volume Profile strategy initialised.")

    def read_configuration(self, config: Configuration) -> None:
        """
        Read the configuration
        """
        raw = config.get_raw_config()
        strategy_config = raw.get("strategies", {}).get("volume_profile", {})

        # Spread constraint
        self.max_spread_perc = strategy_config.get("max_spread_perc", 0.1)

        # Volume Profile settings
        self.lookback_periods = strategy_config.get("lookback_periods", 50)
        self.value_area_percentage = strategy_config.get("value_area_percentage", 70)
        self.price_bins = strategy_config.get("price_bins", 30)

        # Order flow settings
        self.imbalance_threshold = strategy_config.get("imbalance_threshold", 1.5)

        # Risk management
        self.atr_period = strategy_config.get("atr_period", 14)
        self.base_atr_multiplier = strategy_config.get("base_atr_multiplier", 1.5)
        self.min_risk_reward = strategy_config.get("min_risk_reward", 1.5)
        self.max_risk_reward = strategy_config.get("max_risk_reward", 3.0)

    def initialise(self) -> None:
        """
        Initialise Volume Profile strategy
        """
        pass

    def fetch_datapoints(self, market: Market) -> MarketHistory:
        """
        Fetch historic price and volume data
        """
        # Fetch enough data for volume profile analysis
        return self.broker.get_prices(market, Interval.DAY, self.lookback_periods + 20)

    def find_trade_signal(
        self, market: Market, datapoints: MarketHistory
    ) -> TradeSignal:
        """
        Analyze volume profile and order flow to generate trade signals
        """
        if datapoints is None or len(datapoints.dataframe) < self.lookback_periods:
            logging.warning(f"Not enough data for {market.epic}")
            return TradeDirection.NONE, None, None

        # Spread constraint
        if market.bid - market.offer > self.max_spread_perc:
            return TradeDirection.NONE, None, None

        df = datapoints.dataframe.copy()

        # Calculate ATR for risk management
        atr = self._calculate_atr(df)

        # Build volume profile for recent period
        recent_data = df.tail(self.lookback_periods)
        volume_profile = self._build_volume_profile(recent_data)

        # Extract key levels
        poc = volume_profile["poc"]
        vah = volume_profile["vah"]
        val = volume_profile["val"]

        # Get current price
        current_price = df.iloc[-1]["close"]

        # Analyze order flow imbalance
        order_flow = self._analyze_order_flow(df.tail(10))

        # Determine signal
        signal = TradeDirection.NONE

        # BUY Signal: Price near VAL or POC with bullish imbalance
        if self._is_near_level(current_price, val, atr) or self._is_near_level(
            current_price, poc, atr
        ):
            if order_flow["imbalance"] > self.imbalance_threshold:
                signal = TradeDirection.BUY
                logging.info(
                    f"VolumeProfile BUY: Price {current_price:.4f} near support (VAL: {val:.4f}, POC: {poc:.4f}), Imbalance: {order_flow['imbalance']:.2f}"
                )

        # SELL Signal: Price near VAH or POC with bearish imbalance
        elif self._is_near_level(current_price, vah, atr) or self._is_near_level(
            current_price, poc, atr
        ):
            if order_flow["imbalance"] < -self.imbalance_threshold:
                signal = TradeDirection.SELL
                logging.info(
                    f"VolumeProfile SELL: Price {current_price:.4f} near resistance (VAH: {vah:.4f}, POC: {poc:.4f}), Imbalance: {order_flow['imbalance']:.2f}"
                )

        if signal is not TradeDirection.NONE:
            # Calculate dynamic risk/reward based on distance to key levels
            risk_reward = self._calculate_dynamic_risk_reward(
                signal, current_price, poc, vah, val, atr
            )

            limit, stop = self._calculate_stop_limit(
                signal, market.offer, market.bid, atr, risk_reward
            )

            logging.info(
                f"VolumeProfile says: {signal.name} {market.id} (RR: {risk_reward:.2f})"
            )
            return signal, limit, stop

        return TradeDirection.NONE, None, None

    def _build_volume_profile(self, df: pandas.DataFrame) -> Dict[str, float]:
        """
        Build volume profile and identify key levels
        """
        # Get price range
        price_min = df["low"].min()
        price_max = df["high"].max()

        # Create price bins
        price_range = np.linspace(price_min, price_max, self.price_bins)
        volume_at_price = np.zeros(len(price_range) - 1)

        # Distribute volume across price levels
        for _, row in df.iterrows():
            # Find which bins this candle's range covers
            low_idx = np.searchsorted(price_range, row["low"], side="right") - 1
            high_idx = np.searchsorted(price_range, row["high"], side="left")

            # Distribute volume proportionally across the range
            bins_covered = max(1, high_idx - low_idx)
            volume_per_bin = row["volume"] / bins_covered

            for i in range(max(0, low_idx), min(len(volume_at_price), high_idx)):
                volume_at_price[i] += volume_per_bin

        # Find Point of Control (POC) - price with highest volume
        poc_idx = np.argmax(volume_at_price)
        poc = (price_range[poc_idx] + price_range[poc_idx + 1]) / 2

        # Find Value Area (70% of volume)
        total_volume = volume_at_price.sum()
        target_volume = total_volume * (self.value_area_percentage / 100)

        # Start from POC and expand until we reach target volume
        val_idx = poc_idx
        vah_idx = poc_idx
        accumulated_volume = volume_at_price[poc_idx]

        while accumulated_volume < target_volume:
            # Check which direction has more volume
            vol_below = volume_at_price[val_idx - 1] if val_idx > 0 else 0
            vol_above = (
                volume_at_price[vah_idx + 1]
                if vah_idx < len(volume_at_price) - 1
                else 0
            )

            if vol_above > vol_below and vah_idx < len(volume_at_price) - 1:
                vah_idx += 1
                accumulated_volume += volume_at_price[vah_idx]
            elif val_idx > 0:
                val_idx -= 1
                accumulated_volume += volume_at_price[val_idx]
            else:
                break

        val = (price_range[val_idx] + price_range[val_idx + 1]) / 2
        vah = (price_range[vah_idx] + price_range[vah_idx + 1]) / 2

        return {
            "poc": poc,
            "vah": vah,
            "val": val,
            "volume_profile": volume_at_price,
            "price_levels": price_range,
        }

    def _analyze_order_flow(self, df: pandas.DataFrame) -> Dict[str, float]:
        """
        Analyze order flow to detect buying/selling pressure imbalance

        Positive imbalance = Aggressive buying (price closing near highs with volume)
        Negative imbalance = Aggressive selling (price closing near lows with volume)
        """
        buying_pressure = 0
        selling_pressure = 0

        for _, row in df.iterrows():
            # Calculate where price closed within the range (0 = low, 1 = high)
            range_size = row["high"] - row["low"]
            if range_size > 0:
                close_position = (row["close"] - row["low"]) / range_size
            else:
                close_position = 0.5

            # Weight by volume
            volume_weighted = row["volume"]

            # Close near high = buying pressure, close near low = selling pressure
            buying_pressure += close_position * volume_weighted
            selling_pressure += (1 - close_position) * volume_weighted

        # Calculate imbalance ratio
        total_pressure = buying_pressure + selling_pressure
        if total_pressure > 0:
            imbalance = (buying_pressure - selling_pressure) / total_pressure * 10
        else:
            imbalance = 0

        return {
            "imbalance": imbalance,
            "buying_pressure": buying_pressure,
            "selling_pressure": selling_pressure,
        }

    def _calculate_atr(self, df: pandas.DataFrame) -> float:
        """
        Calculate Average True Range
        """
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())

        ranges = pandas.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(self.atr_period).mean().iloc[-1]

        return atr

    def _is_near_level(
        self, price: float, level: float, atr: float, tolerance: float = 0.5
    ) -> bool:
        """
        Check if price is near a key level (within tolerance * ATR)
        """
        distance = abs(price - level)
        return distance <= (atr * tolerance)

    def _calculate_dynamic_risk_reward(
        self,
        signal: TradeDirection,
        current_price: float,
        poc: float,
        vah: float,
        val: float,
        atr: float,
    ) -> float:
        """
        Calculate dynamic risk/reward ratio based on distance to key levels

        Better RR when:
        - Entry is far from target (more room to run)
        - Entry is close to stop level (tight stop)
        """
        if signal == TradeDirection.BUY:
            # Target is VAH, stop is below VAL
            target_distance = abs(vah - current_price)
            stop_distance = abs(current_price - val) + atr
        else:  # SELL
            # Target is VAL, stop is above VAH
            target_distance = abs(current_price - val)
            stop_distance = abs(vah - current_price) + atr

        # Calculate ratio
        if stop_distance > 0:
            risk_reward = target_distance / stop_distance
        else:
            risk_reward = self.min_risk_reward

        # Clamp to reasonable range
        risk_reward = max(self.min_risk_reward, min(self.max_risk_reward, risk_reward))

        return risk_reward

    def _calculate_stop_limit(
        self,
        trade_direction: TradeDirection,
        current_offer: float,
        current_bid: float,
        atr: float,
        risk_reward: float,
    ) -> Tuple[float, float]:
        """
        Calculate Stop Loss and Take Profit using ATR and dynamic RR
        """
        stop_loss_distance = atr * self.base_atr_multiplier
        take_profit_distance = stop_loss_distance * risk_reward

        if trade_direction == TradeDirection.BUY:
            stop = current_bid - stop_loss_distance
            limit = current_offer + take_profit_distance
        elif trade_direction == TradeDirection.SELL:
            stop = current_offer + stop_loss_distance
            limit = current_bid - take_profit_distance
        else:
            raise ValueError("Trade direction cannot be NONE")

        return limit, stop

    def backtest(
        self, market: Market, start_date: datetime.datetime, end_date: datetime.datetime
    ) -> BacktestResult:
        """Backtest the strategy"""
        raise NotImplementedError("Backtesting not implemented yet")
