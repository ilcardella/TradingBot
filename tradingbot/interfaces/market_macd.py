from typing import List

import pandas

from . import Market


class MarketMACD:
    DATE_COLUMN: str = "Date"
    MACD_COLUMN: str = "MACD"
    SIGNAL_COLUMN: str = "Signal"
    HIST_COLUMN: str = "Hist"

    market: Market
    dataframe: pandas.DataFrame

    def __init__(
        self,
        market: Market,
        date: List[str],
        macd: List[float],
        signal: List[float],
        hist: List[float],
    ) -> None:
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
