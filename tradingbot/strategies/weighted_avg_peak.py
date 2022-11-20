# mypy: ignore-errors

import logging
import math
from datetime import datetime
from typing import Optional, Tuple

import numpy
from numpy import Inf, NaN, arange, array, asarray, isscalar
from scipy import stats

from ..components import Configuration, Interval, TradeDirection, Utils
from ..components.broker import Broker
from ..interfaces import Market, MarketHistory
from . import BacktestResult, Strategy, TradeSignal


class WeightedAvgPeak(Strategy):
    """
    All credits of this strategy goes to GitHub user @tg12.
    """

    def __init__(self, config: Configuration, broker: Broker) -> None:
        super().__init__(config, broker)
        logging.info("Weighted Average Peak strategy initialised.")

    def read_configuration(self, config: Configuration) -> None:
        """
        Read the json configuration
        """
        raw = config.get_raw_config()
        self.max_spread = raw["strategies"]["weighted_avg_peak"]["max_spread"]
        self.limit_p = raw["strategies"]["weighted_avg_peak"]["limit_perc"]
        self.stop_p = raw["strategies"]["weighted_avg_peak"]["stop_perc"]
        # TODO add these to the config file
        self.profit_indicator_multiplier = 0.3
        self.ESMA_new_margin = 21  # (20% for stocks)
        self.too_high_margin = 100  # No stupidly high pip limit per trade
        # Normally would be 3/22 days but dull stocks require a lower multiplier
        self.ce_multiplier = 2
        self.greed_indicator = 99999

    def initialise(self) -> None:
        """
        Initialise the strategy
        """
        pass

    def fetch_datapoints(self, market: Market) -> MarketHistory:
        """
        Fetch weekly prices of past 18 weeks
        """
        return self.broker.get_prices(market, Interval.WEEK, 18)

    def find_trade_signal(
        self, market: Market, datapoints: MarketHistory
    ) -> TradeSignal:
        """
        TODO add description of strategy key points
        """
        # limit_perc = self.limit_p
        # stop_perc = max(market.stop_distance_min, self.stop_p)

        # Spread constraint
        if market.bid - market.offer > self.max_spread:
            return TradeDirection.NONE, None, None

        # Compute mid price
        current_mid = Utils.midpoint(market.bid, market.offer)

        high_prices = datapoints.dataframe[MarketHistory.HIGH_COLUMN].values
        low_prices = datapoints.dataframe[MarketHistory.LOW_COLUMN].values
        close_prices = datapoints.dataframe[MarketHistory.CLOSE_COLUMN].values
        ltv = datapoints.dataframe[MarketHistory.VOLUME_COLUMN].values

        # Check dataset integrity
        array_len_check = []
        array_len_check.append(len(high_prices))
        array_len_check.append(len(low_prices))
        array_len_check.append(len(close_prices))
        array_len_check.append(len(ltv))
        if not all(x == array_len_check[0] for x in array_len_check):
            logging.error("Historic datapoints incomplete for {}".format(market.epic))
            return TradeDirection.NONE, None, None

        # compute weighted average and std deviation of prices using volume as weight
        low_prices = numpy.ma.asarray(low_prices)
        high_prices = numpy.ma.asarray(high_prices)
        ltv = numpy.ma.asarray(ltv)
        low_weighted_avg, low_weighted_std_dev = self.weighted_avg_and_std(
            low_prices, ltv
        )
        high_weighted_avg, high_weighted_std_dev = self.weighted_avg_and_std(
            high_prices, ltv
        )

        # The VWAP can be used similar to moving averages, where prices above
        # the VWAP reflect a bullish sentiment and prices below the VWAP
        # reflect a bearish sentiment. Traders may initiate short positions as
        # a stock price moves below VWAP for a given time period or initiate
        # long position as the price moves above VWAP

        tmp_high_weight_var = float(high_weighted_avg + high_weighted_std_dev)
        tmp_low_weight_var = float(low_weighted_avg + low_weighted_std_dev)
        # e.g
        # series = [0,0,0,2,0,0,0,-2,0,0,0,2,0,0,0,-2,0]

        maxtab_high, _mintab_high = self.peakdet(high_prices, 0.3)
        _maxtab_low, mintab_low = self.peakdet(low_prices, 0.3)

        # convert to array so can work on min/max
        mintab_low_a = array(mintab_low)[:, 1]
        maxtab_high_a = array(maxtab_high)[:, 1]

        xb = range(0, len(mintab_low_a))
        xc = range(0, len(maxtab_high_a))

        (
            mintab_low_a_slope,
            mintab_low_a_intercept,
            mintab_low_a_lo_slope,
            mintab_low_a_hi_slope,
        ) = stats.mstats.theilslopes(mintab_low_a, xb, 0.99)
        (
            maxtab_high_a_slope,
            maxtab_high_a_intercept,
            maxtab_high_a_lo_slope,
            maxtab_high_a_hi_slope,
        ) = stats.mstats.theilslopes(maxtab_high_a, xc, 0.99)

        peak_count_high = 0
        peak_count_low = 0
        # how may "peaks" are BELOW the threshold
        for a in mintab_low_a:
            if float(a) < float(tmp_low_weight_var):
                peak_count_low += 1

        # how may "peaks" are ABOVE the threshold
        for a in maxtab_high_a:
            if float(a) > float(tmp_high_weight_var):
                peak_count_high += 1

        additional_checks_sell = [
            int(peak_count_low) > int(peak_count_high),
            float(mintab_low_a_slope) < float(maxtab_high_a_slope),
        ]
        additional_checks_buy = [
            int(peak_count_high) > int(peak_count_low),
            float(maxtab_high_a_slope) > float(mintab_low_a_slope),
        ]

        sell_rules = [
            float(current_mid) >= float(numpy.max(maxtab_high_a)),
            all(additional_checks_sell),
        ]
        buy_rules = [
            float(current_mid) <= float(numpy.min(mintab_low_a)),
            all(additional_checks_buy),
        ]

        trade_direction = TradeDirection.NONE
        if any(buy_rules):
            trade_direction = TradeDirection.BUY
        elif any(sell_rules):
            trade_direction = TradeDirection.SELL

        if trade_direction is TradeDirection.NONE:
            return trade_direction, None, None

        logging.info("Strategy says: {} {}".format(trade_direction.name, market.id))

        ATR = self.calculate_stop_loss(close_prices, high_prices, low_prices)

        if trade_direction is TradeDirection.BUY:
            pip_limit = int(
                abs(float(max(high_prices)) - float(market.bid))
                * self.profit_indicator_multiplier
            )
            ce_stop = self.Chandelier_Exit_formula(
                trade_direction, ATR, min(low_prices)
            )
            stop_pips = int(abs(float(market.bid) - (ce_stop)))
        elif trade_direction is TradeDirection.SELL:
            pip_limit = int(
                abs(float(min(low_prices)) - float(market.bid))
                * self.profit_indicator_multiplier
            )
            ce_stop = self.Chandelier_Exit_formula(
                trade_direction, ATR, max(high_prices)
            )
        stop_pips = int(abs(float(market.bid) - (ce_stop)))

        esma_new_margin_req = int(Utils.percentage_of(self.ESMA_new_margin, market.bid))

        if int(esma_new_margin_req) > int(stop_pips):
            stop_pips = int(esma_new_margin_req)
        # is there a case for a 20% drop? ... Especially over 18 weeks or
        # so?
        if int(stop_pips) > int(esma_new_margin_req):
            stop_pips = int(esma_new_margin_req)
        if int(pip_limit) == 0:
            # not worth the trade
            trade_direction = TradeDirection.NONE
        if int(pip_limit) == 1:
            # not worth the trade
            trade_direction = TradeDirection.NONE
        if int(pip_limit) >= int(self.greed_indicator):
            pip_limit = int(self.greed_indicator - 1)
        if int(stop_pips) > int(self.too_high_margin):
            logging.warning("Junk data for {}".format(market.epic))
            return TradeDirection.NONE, None, None
        return trade_direction, pip_limit, stop_pips

    def calculate_stop_loss(
        self,
        close_prices: numpy.ndarray,
        high_prices: numpy.ndarray,
        low_prices: numpy.ndarray,
    ) -> str:
        price_ranges = []
        closing_prices = []
        first_time_round_loop = True
        TR_prices = []
        # They should be all the same length but just in case to be safe
        length = min(len(close_prices), len(high_prices), len(low_prices))

        for index in range(length):
            if first_time_round_loop:
                # First time round loop cannot get previous
                closePrice = close_prices[index]
                closing_prices.append(closePrice)
                high_price = high_prices[index]
                low_price = low_prices[index]
                price_range = float(high_price - closePrice)
                price_ranges.append(price_range)
                first_time_round_loop = False
            else:
                prev_close = closing_prices[-1]
                closePrice = close_prices[index]
                closing_prices.append(closePrice)
                high_price = high_prices[index]
                low_price = low_prices[index]
                price_range = float(high_price - closePrice)
                price_ranges.append(price_range)
                TR = max(
                    high_price - low_price,
                    abs(high_price - prev_close),
                    abs(low_price - prev_close),
                )
                TR_prices.append(TR)

        # for i in prices['prices']:
        #     if first_time_round_loop:
        #         # First time round loop cannot get previous
        #         closePrice = i['closePrice'][price_compare]
        #         closing_prices.append(closePrice)
        #         high_price = i['highPrice'][price_compare]
        #         low_price = i['lowPrice'][price_compare]
        #         price_range = float(high_price - closePrice)
        #         price_ranges.append(price_range)
        #         first_time_round_loop = False
        #     else:
        #         prev_close = closing_prices[-1]
        #         closePrice = i['closePrice'][price_compare]
        #         closing_prices.append(closePrice)
        #         high_price = i['highPrice'][price_compare]
        #         low_price = i['lowPrice'][price_compare]
        #         price_range = float(high_price - closePrice)
        #         price_ranges.append(price_range)
        #         TR = max(high_price - low_price,
        #                 abs(high_price - prev_close),
        #                 abs(low_price - prev_close))
        #         TR_prices.append(TR)

        return str(int(float(max(TR_prices))))

    def weighted_avg_and_std(
        self, values: numpy.ndarray, weights: numpy.ndarray
    ) -> Tuple[float, float]:
        """
        Return the weighted average and standard deviation.

        values, weights -- Numpy ndarrays with the same shape.
        """
        average = numpy.average(values, weights=weights)
        variance = numpy.average((values - average) ** 2, weights=weights)
        return (float(average), math.sqrt(variance))

    def peakdet(
        self, v: numpy.ndarray, delta: float, x: Optional[numpy.ndarray] = None
    ) -> Tuple[Optional[numpy.ndarray], Optional[numpy.ndarray]]:
        """
        Converted from MATLAB script at http://billauer.co.il/peakdet.html

        Returns two arrays

        function [maxtab, mintab]=peakdet(v, delta, x)
        %PEAKDET Detect peaks in a vector
        %        [MAXTAB, MINTAB] = PEAKDET(V, DELTA) finds the local
        %        maxima and minima ("peaks") in the vector V.
        %        MAXTAB and MINTAB consists of two columns. Column 1
        %        contains indices in V, and column 2 the found values.
        %
        %        With [MAXTAB, MINTAB] = PEAKDET(V, DELTA, X) the indices
        %        in MAXTAB and MINTAB are replaced with the corresponding
        %        X-values.
        %
        %        A point is considered a maximum peak if it has the maximal
        %        value, and was preceded (to the left) by a value lower by
        %        DELTA.

        % Eli Billauer, 3.4.05 (Explicitly not copyrighted).
        % This function is released to the public domain; Any use is allowed.

        """
        maxtab = []
        mintab = []

        if x is None:
            x = arange(len(v))

        v = asarray(v)

        if len(v) != len(x):
            logging.error("Input vectors v and x must have same length")
            return None, None

        if not isscalar(delta):
            logging.error("Input argument delta must be a scalar")
            return None, None

        if delta <= 0:
            logging.error("Input argument delta must be positive")
            return None, None

        mn, mx = Inf, -Inf
        mnpos, mxpos = NaN, NaN

        lookformax = True

        for i in arange(len(v)):
            this = v[i]
            if this > mx:
                mx = this
                mxpos = x[i]
            if this < mn:
                mn = this
                mnpos = x[i]

            if lookformax:
                if this < mx - delta:
                    maxtab.append((mxpos, mx))
                    mn = this
                    mnpos = x[i]
                    lookformax = False
            else:
                if this > mn + delta:
                    mintab.append((mnpos, mn))
                    mx = this
                    mxpos = x[i]
                    lookformax = True

        return array(maxtab), array(mintab)

    def Chandelier_Exit_formula(
        self, TRADE_DIR: TradeDirection, ATR: str, Price: float
    ) -> float:
        # Chandelier Exit (long) = 22-day High - ATR(22) x 3
        # Chandelier Exit (short) = 22-day Low + ATR(22) x 3
        if TRADE_DIR is TradeDirection.BUY:
            return float(Price) - float(ATR) * int(self.ce_multiplier)
        elif TRADE_DIR is TradeDirection.SELL:
            return float(Price) + float(ATR) * int(self.ce_multiplier)
        raise ValueError("trade direction can't be NONE")

    def backtest(
        self, market: Market, start_date: datetime, end_date: datetime
    ) -> BacktestResult:
        """Backtest the strategy"""
        # TODO
        raise NotImplementedError("Work in progress")
