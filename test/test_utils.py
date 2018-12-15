import os
import sys
import inspect
import pytest
from datetime import datetime, timedelta
import pytz

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,'{}/src'.format(parentdir))

from Utils import Utils

def test_midpoint():
    assert Utils.midpoint(0,10) == 5
    assert Utils.midpoint(-10, 10) == 0
    assert Utils.midpoint(10, -10) == 0
    assert Utils.midpoint(0, 0) == 0
    assert Utils.midpoint(1,2) == 1.5

def test_percentage_of():
    assert Utils.percentage_of(1,100) == 1
    assert Utils.percentage_of(0,100) == 0
    assert Utils.percentage_of(1,1) == 0.01

def test_percentage():
    assert Utils.percentage(1,100) == 1
    assert Utils.percentage(0,100) == 0
    assert Utils.percentage(200,100) == 200
    # with pytest.raises(Exception):
    #     assert Utils.percentage(-1,100)
    # with pytest.raises(Exception):
    #     assert Utils.percentage(1,-100)

def test_is_between():
    mock = '10:10'
    assert Utils.is_between(mock, ('10:09','10:11'))
    mock = '00:00'
    assert Utils.is_between(mock, ('23:59','00:01'))

def test_humanize_time():
    assert Utils.humanize_time(3600) == '01:00:00'
    assert Utils.humanize_time(4800) == '01:20:00'
    assert Utils.humanize_time(4811) == '01:20:11'

def test_get_seconds_to_market_opening():
    now = datetime.now()
    seconds = Utils.get_seconds_to_market_opening()
    assert seconds > 0
    assert seconds is not None
    opening = now + timedelta(seconds=seconds)
    assert 0 <= opening.weekday() < 5
    expected = opening.replace(hour=8,minute=0,second=2,microsecond=0)
    diff = expected - opening
    assert diff.seconds < 10

def test_is_market_open():
    timezone = 'Europe/London'
    tz = pytz.timezone(timezone)
    now_time = datetime.now(tz=tz).strftime('%H:%M')
    expected = Utils.is_between(str(now_time), ("07:55", "16:35"))

    result = Utils.is_market_open(timezone)

    assert result == expected
