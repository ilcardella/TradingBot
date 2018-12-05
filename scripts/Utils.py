# Utility functions are stored in this class and accessed as static members

import logging
import json
import pytz
from enum import Enum
from datetime import datetime
from govuk_bank_holidays.bank_holidays import BankHolidays

class TradeDirection(Enum):
    """
    Enumeration that represents the trade direction in the market: NONE means
    no action to take.
    """
    NONE = 'NONE'
    BUY = 'BUY'
    SELL = 'SELL'

class Utils:
    """
    Utility class containing static methods to perform simple general actions
    """
    def __init__(self):
        pass

    @staticmethod
    def midpoint(p1, p2):
        """Return the midpoint"""
        return (p1 + p2) / 2

    @staticmethod
    def percentage_of(percent, whole):
        """Return the value of the percentage on the whole"""
        return (percent * whole) / 100.0

    @staticmethod
    def percentage(part, whole):
        """Return the percentage value of the part on the whole"""
        return 100 * float(part) / float(whole)

    @staticmethod
    def is_between(time, time_range):
        """Return True if time is between the time_range. time must be a string.
        time_range must be a tuple (a,b) where a and b are strings in format 'HH:MM'"""
        if time_range[1] < time_range[0]:
            return time >= time_range[0] or time <= time_range[1]
        return time_range[0] <= time <= time_range[1]

    @staticmethod
    def humanize_time(secs):
        """Convert the given time (in seconds) into a readable format hh:mm:ss"""
        mins, secs = divmod(secs, 60)
        hours, mins = divmod(mins, 60)
        return '%02d:%02d:%02d' % (hours, mins, secs)

    @staticmethod
    def get_seconds_to_market_opening():
        """Return the amount of seconds from now to the next market opening,
        taking into account UK bank holidays and weekends"""
        now = datetime.now()
        # Get next working day
        nextWorkDate = BankHolidays().get_next_work_day()
        nextMarketOpening = datetime(year=nextWorkDate.year, month=nextWorkDate.month, day=nextWorkDate.day, hour=8, minute=0, second=0, microsecond=0)
        # Calculate the delta from now to the next market opening
        return (nextMarketOpening - now).total_seconds()

    @staticmethod
    def is_market_open(timezone):
        """
        Return True if the market is open, false otherwise

            - **timezone**: string representing the timezone
        """
        tz = pytz.timezone(timezone)
        now_time = datetime.now(tz=tz).strftime('%H:%M')
        return Utils.is_between(str(now_time), ("07:55", "16:35"))
