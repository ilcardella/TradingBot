import pandas

from Interfaces.Market import Market


class MarketMACD:
    DATE_COLUMN = "Date"
    MACD_COLUMN = "MACD"
    SIGNAL_COLUMN = "Signal"
    HIST_COLUMN = "Hist"

    def __init__(
        self, market: Market, date: list, macd: list, signal: list, hist: list
    ):
        self.market = market
        self.dataframe = pandas.DataFrame(
            columns=[
                self.DATE_COLUMN,
                self.MACD_COLUMN,
                self.SIGNAL_COLUMN,
                self.HIST_COLUMN,
            ]
        )
        # TODO if date is None or empty use index
        self.dataframe[self.DATE_COLUMN] = date
        self.dataframe[self.MACD_COLUMN] = macd
        self.dataframe[self.SIGNAL_COLUMN] = signal
        self.dataframe[self.HIST_COLUMN] = hist
