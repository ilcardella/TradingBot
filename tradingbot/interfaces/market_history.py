from typing import List

import pandas

from . import Market


class MarketHistory:
    DATE_COLUMN: str = "date"
    HIGH_COLUMN: str = "high"
    LOW_COLUMN: str = "low"
    CLOSE_COLUMN: str = "close"
    VOLUME_COLUMN: str = "volume"

    market: Market
    dataframe: pandas.DataFrame

    def __init__(
        self,
        market: Market,
        date: List[str],
        high: List[float],
        low: List[float],
        close: List[float],
        volume: List[float],
    ) -> None:
        self.market = market
        self.dataframe = pandas.DataFrame(
            columns=[
                self.DATE_COLUMN,
                self.HIGH_COLUMN,
                self.LOW_COLUMN,
                self.CLOSE_COLUMN,
                self.VOLUME_COLUMN,
            ]
        )
        # TODO if date is None or empty use index
        self.dataframe[self.DATE_COLUMN] = date
        self.dataframe[self.HIGH_COLUMN] = high
        self.dataframe[self.LOW_COLUMN] = low
        self.dataframe[self.CLOSE_COLUMN] = close
        self.dataframe[self.VOLUME_COLUMN] = volume
