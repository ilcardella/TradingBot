import logging
import time
from datetime import datetime
from enum import Enum

import pytz
from govuk_bank_holidays.bank_holidays import BankHolidays

from . import Utils


class TimeAmount(Enum):
    """Types of amount of time to wait for"""

    SECONDS = 0
    NEXT_MARKET_OPENING = 1


class TimeProvider:
    """Class that handle functions dependents on actual time
    such as wait, sleep or compute date/time operations
    """

    def __init__(self) -> None:
        logging.debug("TimeProvider __init__")

    def is_market_open(self, timezone: str) -> bool:
        """
        Return True if the market is open, false otherwise

            - **timezone**: string representing the timezone
        """
        tz = pytz.timezone(timezone)
        now_time = datetime.now(tz=tz).strftime("%H:%M")
        return BankHolidays().is_work_day(datetime.now(tz=tz)) and Utils.is_between(
            str(now_time), ("07:55", "16:35")
        )

    def get_seconds_to_market_opening(self, from_time: datetime) -> float:
        """Return the amount of seconds from now to the next market opening,
        taking into account UK bank holidays and weekends"""
        today_opening = datetime(
            year=from_time.year,
            month=from_time.month,
            day=from_time.day,
            hour=8,
            minute=0,
            second=0,
            microsecond=0,
        )

        if from_time < today_opening and BankHolidays().is_work_day(from_time.date()):
            nextMarketOpening = today_opening
        else:
            # Get next working day
            nextWorkDate = BankHolidays().get_next_work_day(date=from_time.date())
            nextMarketOpening = datetime(
                year=nextWorkDate.year,
                month=nextWorkDate.month,
                day=nextWorkDate.day,
                hour=8,
                minute=0,
                second=0,
                microsecond=0,
            )
        # Calculate the delta from from_time to the next market opening
        return (nextMarketOpening - from_time).total_seconds()

    def wait_for(self, time_amount_type: TimeAmount, amount: float = -1.0) -> None:
        """Wait for the specified amount of time.
        An TimeAmount type can be specified
        """
        if time_amount_type is TimeAmount.NEXT_MARKET_OPENING:
            amount = self.get_seconds_to_market_opening(datetime.now())
        elif time_amount_type is TimeAmount.SECONDS:
            if amount < 0:
                raise ValueError("Invalid amount of time to wait for")
        logging.info("Wait for {0:.2f} hours...".format(amount / 3600))
        time.sleep(amount)
