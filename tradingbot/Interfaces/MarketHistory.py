import pandas

from Interfaces.Market import Market


class MarketHistory:
    DATE_COLUMN = "date"
    HIGH_COLUMN = "high"
    LOW_COLUMN = "low"
    CLOSE_COLUMN = "close"
    VOLUME_COLUMN = "volume"

    def __init__(
        self,
        market: Market,
        date: list,
        high: list,
        low: list,
        close: list,
        volume: list,
    ):
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
