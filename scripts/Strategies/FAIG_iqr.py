import logging
import numpy
import pandas
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import math
from Utils import *

# TODO we could have parent Strategy abstract class for common stuff among strategies
class FAIG_iqr:
    def __init__(self, config):
        self.read_configuration(config)
        logging.info('FAIG IQR strategy will be used.')
    
    def read_configuration(self, config):
        self.esmaStocksMargin = config['general']['esma_stocks_margin_perc']
        self.stopLossMultiplier = config['strategies']['faig']['stop_loss_multiplier']
        self.tooHighMargin = config['strategies']['faig']['too_high_margin']

    def calculate_stop_loss(self, prices):
        price_ranges = []
        closing_prices = []
        first_time_round_loop = True
        TR_prices = []
        price_compare = "bid"

        for i in prices['prices']:
            if first_time_round_loop:
                ###########################################
                # First time round loop cannot get previous
                ###########################################
                closePrice = i['closePrice'][price_compare]
                closing_prices.append(closePrice)
                high_price = i['highPrice'][price_compare]
                low_price = i['lowPrice'][price_compare]
                price_range = float(high_price - closePrice)
                price_ranges.append(price_range)
                first_time_round_loop = False
            else:
                prev_close = closing_prices[-1]
                ###########################################
                closePrice = i['closePrice'][price_compare]
                closing_prices.append(closePrice)
                high_price = i['highPrice'][price_compare]
                low_price = i['lowPrice'][price_compare]
                price_range = float(high_price - closePrice)
                price_ranges.append(price_range)
                TR = max(high_price - low_price,
                        abs(high_price - prev_close),
                        abs(low_price - prev_close))
                TR_prices.append(TR)

        return str(int(float(max(TR_prices))))

    def Chandelier_Exit_formula(self, TRADE_DIR, ATR, Price):
        # Chandelier Exit (long) = 22-day High - ATR(22) x 3
        # Chandelier Exit (short) = 22-day Low + ATR(22) x 3
        if TRADE_DIR == TradeDirection.BUY:
            return float(Price) - float(ATR) * 3
        elif TRADE_DIR == TradeDirection.SELL:
            return float(Price) + float(ATR) * 3

    def execute(self, brokerIf, epic_id):
        # Gather past prices and current market prices
        prices = self.brokerIf.get_prices(epic_id, 'DAY', 5)
        current_bid, current_offer = self.brokerIf.get_market_price(epic_id)

        if prices is None or current_bid is None or current_offer is None:
            logging.info('Strategy cannot run: something is wrong with the prices.')
            return None, None, None
        
        high_prices = []
        low_prices = []
        mid_prices = []
        close_prices = []
        ATR = self.calculate_stop_loss(prices)

        for i in prices['prices']:
            if i['highPrice']['bid'] is not None:
                highPrice = i['highPrice']['bid']
                high_prices.append(highPrice)
            ########################################
            if i['lowPrice']['bid'] is not None:
                lowPrice = i['lowPrice']['bid']
                low_prices.append(lowPrice)
            ########################################
            if i['closePrice']['bid'] is not None:
                closePrice = i['lowPrice']['bid']
                close_prices.append(closePrice)
            ########################################
            mid_prices.append(float(midpoint(highPrice, lowPrice)))

        close_prices = numpy.asarray(close_prices)
        low_prices = numpy.asarray(low_prices)
        high_prices = numpy.asarray(high_prices)
        mid_prices = numpy.asarray(mid_prices)

        xi = numpy.arange(0, len(low_prices))

        # close_prices_slope, close_prices_intercept, close_prices_r_value, close_prices_p_value, close_prices_std_err = stats.linregress(
        # xi, close_prices)
        # low_prices_slope, low_prices_intercept, low_prices_r_value, low_prices_p_value, low_prices_std_err = stats.linregress(
        # xi, low_prices)
        # high_prices_slope, high_prices_intercept, high_prices_r_value, high_prices_p_value, high_prices_std_err = stats.linregress(
        # xi, high_prices)
        # mid_prices_slope, mid_prices_intercept, mid_prices_r_value, mid_prices_p_value, mid_prices_std_err = stats.linregress(
        # xi, mid_prices)

        close_prices_slope, close_prices_intercept, close_prices_lo_slope, close_prices_hi_slope = stats.theilslopes(
            close_prices, xi, 0.99)
        low_prices_slope, low_prices_intercept, low_prices_lo_slope, low_prices_hi_slope = stats.theilslopes(
            low_prices, xi, 0.99)
        high_prices_slope, high_prices_intercept, high_prices_lo_slope, high_prices_hi_slope = stats.theilslopes(
            high_prices, xi, 0.99)
        mid_prices_slope, mid_prices_intercept, mid_prices_lo_slope, mid_prices_hi_slope = stats.theilslopes(
            mid_prices, xi, 0.99)

        # print ("#####################################################")
        # print ("#####################################################")
        # print
        # ("#####################################################")

        # print ("Please uncomment this to enable graphs for
        # debugging")

        # print ("#####################################################")
        # print ("#####################################################")
        # print
        # ("#####################################################")

        # close_prices_line = close_prices_slope * xi + close_prices_intercept
        # low_prices_line = low_prices_slope * xi + low_prices_intercept
        # high_prices_line = high_prices_slope * xi + high_prices_intercept
        # mid_prices_line = mid_prices_slope * xi +
        # mid_prices_intercept

        # plt.plot(
        # xi,
        # low_prices_line,
        # xi,
        # high_prices_line,
        # xi,
        # close_prices,
        # 'g--',
        # xi,
        # mid_prices_line)
        # plt.fill_between(
        # xi,
        # low_prices_line,
        # high_prices_line,
        # facecolor='green',
        # alpha=0.5)
        # plt.xlabel('X Axis')
        # plt.ylabel('Y Axis')
        # plt.show()
        # plt.clf()

        # print ("#####################################################")
        # print ("#####################################################")
        # print
        # ("#####################################################")

        # print ("Please uncomment this to enable graphs for
        # debugging")

        # print ("#####################################################")
        # print ("#####################################################")
        # print
        # ("#####################################################")

        # HIGH
        std_dev_2_MID_HIGH = float(
            mid_prices_intercept + (abs(stats.iqr(mid_prices, nan_policy='omit') * 2)))
        # LOW
        std_dev_2_MID_LOW = float(mid_prices_intercept -
                                    (abs(stats.iqr(mid_prices, nan_policy='omit') * 2)))

        if float(current_bid) > float(std_dev_2_MID_HIGH):
            trade_direction = TradeDirection.SELL
        elif float(current_bid) < float(std_dev_2_MID_LOW):
            trade_direction = TradeDirection.BUY
        else:
            pip_limit = 9999999  # Junk Data
            stop_pips = "999999"  # Junk Data
            trade_direction = TradeDirection.NONE
            logging.info("Unable to define a trade direction for {}".format(epic_id))

        if trade_direction == TradeDirection.BUY:
            pip_limit = int(abs(float(max(mid_prices)) -
                                float(current_bid)) / self.stopLossMultiplier)
            ce_stop = self.Chandelier_Exit_formula(
                trade_direction, ATR, min(low_prices))
            stop_pips = str(int(abs(float(current_bid) - (ce_stop))))
            logging.info("Will BUY {} and take profit at {} pips"
                            .format(str(epic_id), str(pip_limit)))

        elif trade_direction == TradeDirection.SELL:
            pip_limit = int(abs(float(min(mid_prices)) -
                                float(current_bid)) / self.stopLossMultiplier)
            ce_stop = self.Chandelier_Exit_formula(
                trade_direction, ATR, max(high_prices))
            stop_pips = str(int(abs(float(current_bid) - (ce_stop))))
            logging.info("Will SELL {} and take profit at {} pips"
                            .format(str(epic_id), str(pip_limit)))
        elif trade_direction == TradeDirection.NONE:
            logging.warn("Trade direction is NONE")

        # Sanity Checks
        esma_new_margin_req = int(percentage_of(self.esmaStocksMargin,
                                                current_bid))
        if int(esma_new_margin_req) > int(stop_pips):
            stop_pips = int(esma_new_margin_req)
            logging.info("ESMA Readjustment, stop at {} pips".format(stop_pips))

        if int(stop_pips) > int(self.tooHighMargin):
            trade_direction = TradeDirection.NONE
            logging.info("Stop at {} pips is too high, no trade".format(stop_pips))

        if int(pip_limit) < 2:
            trade_direction = TradeDirection.NONE
            logging.info("Pip limit too low, no trade")

        limitDistance_value = str(pip_limit)  # Limit
        stopDistance_value = str(stop_pips)  # Stop

        logging.info("Order for {} will be a {} with limit at {} and stop at {}"
                    .format(str(epic_id), str(trade_direction), str(limitDistance_value), str(stopDistance_value)))
        
        return trade_direction, limitDistance_value, stopDistance_value
