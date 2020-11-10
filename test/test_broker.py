import pytest
import toml
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

from tradingbot.components import Configuration, Interval, TradeDirection
from tradingbot.components.broker import Broker, BrokerFactory, InterfaceNames
from tradingbot.interfaces import Market, MarketHistory, MarketMACD, Position


@pytest.fixture(
    params=[
        InterfaceNames.IG_INDEX.value,
        InterfaceNames.ALPHA_VANTAGE.value,
        InterfaceNames.YAHOO_FINANCE.value,
    ]
)
def config(request):
    with open("test/test_data/trading_bot.toml", "r") as f:
        config = toml.load(f)
        # Inject the fixture parameter in the configuration
        config["stocks_interface"]["active"] = request.param
        # To speed up the tests, reduce the timeout of all interfaces
        config["stocks_interface"][InterfaceNames.YAHOO_FINANCE.value][
            "api_timeout"
        ] = 0
        config["stocks_interface"][InterfaceNames.ALPHA_VANTAGE.value][
            "api_timeout"
        ] = 0
        return Configuration(config)


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


@pytest.fixture
def broker(mock_http_calls, config):
    return Broker(BrokerFactory(config))


def test_get_open_positions(broker):
    p = broker.get_open_positions()
    assert p is not None
    assert isinstance(p, list)
    assert len(p) > 0
    assert isinstance(p[0], Position)


def test_get_markets_from_watchlist(broker):
    m = broker.get_markets_from_watchlist("My Watchlist")
    assert m is not None
    assert isinstance(m, list)
    assert len(m) > 0
    assert isinstance(m[0], Market)


def test_navigate_market_node(broker):
    # TODO
    # Root node
    node = broker.navigate_market_node("")
    assert node is not None
    # Specific node
    node = broker.navigate_market_node("12345")
    assert node is not None


def test_get_account_used_perc(broker):
    perc = broker.get_account_used_perc()
    assert perc == 62.138354775208285


def test_close_all_positions(broker):
    assert broker.close_all_positions()


def test_close_position(broker):
    pos = broker.get_open_positions()
    for p in pos:
        assert broker.close_position(p)


def test_trade(broker):
    assert broker.trade("mock", TradeDirection.BUY, 100, 50)


def test_get_market_info(broker):
    market = broker.get_market_info("mock")
    assert market is not None
    assert isinstance(market, Market)


def test_search_market(broker):
    markets = broker.search_market("mock")
    assert markets is not None
    assert isinstance(markets, list)
    assert isinstance(markets[0], Market)


def test_get_prices(broker):
    hist = broker.get_prices(broker.get_market_info("mock"), Interval.DAY, 10)
    assert hist is not None
    assert isinstance(hist, MarketHistory)
    assert MarketHistory.DATE_COLUMN in hist.dataframe
    assert len(hist.dataframe[MarketHistory.DATE_COLUMN]) > 0
    assert MarketHistory.HIGH_COLUMN in hist.dataframe
    assert len(hist.dataframe[MarketHistory.HIGH_COLUMN]) > 0
    assert MarketHistory.LOW_COLUMN in hist.dataframe
    assert len(hist.dataframe[MarketHistory.LOW_COLUMN]) > 0
    assert MarketHistory.CLOSE_COLUMN in hist.dataframe
    assert len(hist.dataframe[MarketHistory.CLOSE_COLUMN]) > 0
    assert MarketHistory.VOLUME_COLUMN in hist.dataframe
    assert len(hist.dataframe[MarketHistory.VOLUME_COLUMN]) > 0


def test_get_macd(broker):
    market = broker.get_market_info("mock")
    interval = Interval.HOUR
    macd = broker.get_macd(market, interval, 10)

    assert macd is not None
    assert isinstance(macd, MarketMACD)
    assert MarketMACD.DATE_COLUMN in macd.dataframe
    assert len(macd.dataframe[MarketMACD.DATE_COLUMN]) > 0
    assert MarketMACD.MACD_COLUMN in macd.dataframe
    assert len(macd.dataframe[MarketMACD.MACD_COLUMN]) > 0
    assert MarketMACD.SIGNAL_COLUMN in macd.dataframe
    assert len(macd.dataframe[MarketMACD.SIGNAL_COLUMN]) > 0
    assert MarketMACD.HIST_COLUMN in macd.dataframe
    assert len(macd.dataframe[MarketMACD.HIST_COLUMN]) > 0
