from pathlib import Path

import pytest
from common.MockRequests import (
    av_request_macd_ext,
    av_request_prices,
    ig_request_account_details,
    ig_request_confirm_trade,
    ig_request_login,
    ig_request_market_info,
    ig_request_navigate_market,
    ig_request_open_positions,
    ig_request_prices,
    ig_request_search_market,
    ig_request_set_account,
    ig_request_trade,
    ig_request_watchlist,
    yf_request_prices,
)

from tradingbot import TradingBot
from tradingbot.components import TimeProvider


class MockTimeProvider(TimeProvider):
    def __init__(self):
        pass

    def is_market_open(self, timezone):
        return True

    def get_seconds_to_market_opening(self, from_time):
        raise Exception

    def wait_for(self, time_amount_type, amount=-1):
        pass


@pytest.fixture
def mock_http_calls(requests_mock):
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    ig_request_account_details(requests_mock)
    ig_request_open_positions(requests_mock)
    ig_request_market_info(requests_mock)
    ig_request_search_market(requests_mock)
    ig_request_prices(requests_mock)
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)
    ig_request_navigate_market(requests_mock)
    ig_request_navigate_market(
        requests_mock, args="668394", data="mock_navigate_markets_markets.json"
    )
    ig_request_navigate_market(
        requests_mock, args="77976799", data="mock_navigate_markets_markets.json"
    )
    ig_request_navigate_market(
        requests_mock, args="89291253", data="mock_navigate_markets_markets.json"
    )
    ig_request_watchlist(requests_mock)
    ig_request_watchlist(requests_mock, args="12345678", data="mock_watchlist.json")
    av_request_prices(requests_mock)
    av_request_macd_ext(requests_mock)
    yf_request_prices(requests_mock)


def test_trading_bot(mock_http_calls):
    """
    Test trading bot main functions
    """
    config = Path("test/test_data/trading_bot.toml")
    tb = TradingBot(MockTimeProvider(), config_filepath=config)
    assert tb is not None
    # This is a hack because we are testing the functions used within
    # the start() method. We can't call start() because it gets into
    # an endless while loop
    tb.process_open_positions()
    with pytest.raises(StopIteration):
        tb.process_market_source()
    tb.close_open_positions()
    # TODO assert somehow that the http calls have been done
