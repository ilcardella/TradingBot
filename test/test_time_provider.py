from datetime import datetime, timedelta

import pytest
import pytz
from govuk_bank_holidays.bank_holidays import BankHolidays

from tradingbot.components import TimeAmount, TimeProvider, Utils


def test_get_seconds_to_market_opening():
    tp = TimeProvider()
    now = datetime.now()
    seconds = tp.get_seconds_to_market_opening(now)
    assert seconds > 0
    assert seconds is not None
    opening = now + timedelta(seconds=seconds)
    assert 0 <= opening.weekday() < 5
    expected = opening.replace(hour=8, minute=0, second=2, microsecond=0)
    diff = expected - opening
    assert diff.seconds < 10
    # Test function if called after midnight but before market opening
    mock = datetime.now().replace(hour=3, minute=30, second=0, microsecond=0)
    seconds = tp.get_seconds_to_market_opening(mock)
    assert seconds > 0
    assert seconds is not None
    opening = mock + timedelta(seconds=seconds)
    # assert opening.day == mock.day
    assert opening.hour == 8
    assert opening.minute == 0


def test_is_market_open():
    tp = TimeProvider()
    timezone = "Europe/London"
    tz = pytz.timezone(timezone)
    now_time = datetime.now(tz=tz).strftime("%H:%M")
    expected = Utils.is_between(
        str(now_time), ("07:55", "16:35")
    ) and BankHolidays().is_work_day(datetime.now(tz=tz))

    result = tp.is_market_open(timezone)

    assert result == expected


def test_wait_for():
    tp = TimeProvider()
    # Invalid seconds
    with pytest.raises(ValueError):
        tp.wait_for(TimeAmount.SECONDS)
    with pytest.raises(ValueError):
        tp.wait_for(TimeAmount.SECONDS, -100)
    # Wait for 3 seconds
    now = datetime.now()
    tp.wait_for(TimeAmount.SECONDS, 3)
    new = datetime.now()
    delta = new - now
    assert delta.seconds == 3
