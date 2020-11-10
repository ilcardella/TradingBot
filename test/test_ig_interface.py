import pytest
import toml
from common.MockRequests import (
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
)

from tradingbot.components import Configuration, Interval, TradeDirection
from tradingbot.components.broker import IGInterface, InterfaceNames
from tradingbot.interfaces import Market, MarketHistory, Position


@pytest.fixture
def config():
    with open("test/test_data/trading_bot.toml", "r") as f:
        config = toml.load(f)
        # Inject ig_interface as active interface in the config file
        config["stocks_interface"]["active"] = InterfaceNames.IG_INDEX.value
        config["account_interface"]["active"] = InterfaceNames.IG_INDEX.value
        return Configuration(config)


@pytest.fixture
def ig(requests_mock, config):
    """
    Returns a instance of IGInterface
    """
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    return IGInterface(config)


# No need to use requests_mock as "ig" fixture already does that
def test_authenticate(ig):
    # Call function to test
    result = ig.authenticate()
    # Assert results
    assert ig.authenticated_headers["CST"] == "mock"
    assert ig.authenticated_headers["X-SECURITY-TOKEN"] == "mock"
    assert result is True


def test_authenticate_fail(requests_mock, ig):
    ig_request_login(requests_mock, fail=True)
    ig_request_set_account(requests_mock, fail=True)
    # Call function to test
    result = ig.authenticate()
    # Assert results
    assert result is False


# No need to use requests_mock fixture
def test_set_default_account(ig):
    result = ig.set_default_account("mock")
    assert result is True


def test_set_default_account_fail(requests_mock, ig):
    ig_request_set_account(requests_mock, fail=True)
    result = ig.set_default_account("mock")
    assert result is False


def test_get_account_balances(requests_mock, ig):
    ig_request_account_details(requests_mock)
    balance, deposit = ig.get_account_balances()
    assert balance is not None
    assert deposit is not None
    assert balance == 16093.12
    assert deposit == 10000.0


def test_get_account_balances_fail(requests_mock, ig):
    ig_request_account_details(requests_mock, fail=True)
    with pytest.raises(RuntimeError):
        balance, deposit = ig.get_account_balances()


def test_get_open_positions(ig, requests_mock):
    ig_request_open_positions(requests_mock)

    positions = ig.get_open_positions()

    assert positions is not None
    assert isinstance(positions, list)
    assert len(positions) > 0
    assert isinstance(positions[0], Position)


def test_get_open_positions_fail(ig, requests_mock):
    ig_request_open_positions(requests_mock, fail=True)
    with pytest.raises(RuntimeError):
        _ = ig.get_open_positions()


def test_get_market_info(ig, requests_mock):
    ig_request_market_info(requests_mock)
    info = ig.get_market_info("mock")

    assert info is not None
    assert isinstance(info, Market)


def test_get_market_info_fail(ig, requests_mock):
    ig_request_market_info(requests_mock, fail=True)
    with pytest.raises(RuntimeError):
        _ = ig.get_market_info("mock")


def test_search_market(ig, requests_mock):
    ig_request_market_info(requests_mock)
    ig_request_search_market(requests_mock)
    markets = ig.search_market("mock")

    assert markets is not None
    assert isinstance(markets, list)
    assert len(markets) == 8
    assert isinstance(markets[0], Market)


def test_search_market_fail(ig, requests_mock):
    ig_request_search_market(requests_mock, fail=True)
    with pytest.raises(RuntimeError):
        _ = ig.search_market("mock")


def test_get_prices(ig, requests_mock):
    ig_request_market_info(requests_mock)
    ig_request_prices(requests_mock)
    p = ig.get_prices(ig.get_market_info("mock"), Interval.HOUR, 10)
    assert p is not None
    assert isinstance(p, MarketHistory)
    assert len(p.dataframe) > 0


def test_get_prices_fail(ig, requests_mock):
    ig_request_market_info(requests_mock)
    ig_request_prices(requests_mock, fail=True)
    with pytest.raises(RuntimeError):
        _ = ig.get_prices(ig.get_market_info("mock"), Interval.HOUR, 10)


def test_trade(ig, requests_mock):
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)
    result = ig.trade("mock", TradeDirection.BUY, 0, 0)
    assert result


def test_trade_fail(ig, requests_mock):
    ig_request_trade(requests_mock, fail=True)
    ig_request_confirm_trade(requests_mock, fail=True)
    result = ig.trade("mock", TradeDirection.BUY, 0, 0)
    assert result is False


def test_confirm_order(ig, requests_mock):
    ig_request_confirm_trade(requests_mock)
    result = ig.confirm_order("123456789")
    assert result


def test_confirm_order_fail(ig, requests_mock):
    ig_request_confirm_trade(
        requests_mock,
        data={"dealId": "123456789", "dealStatus": "REJECTED", "reason": "FAIL"},
    )
    result = ig.confirm_order("123456789")
    assert result is False

    ig_request_confirm_trade(requests_mock, fail=True)
    with pytest.raises(RuntimeError):
        result = ig.confirm_order("123456789")


def test_close_position(ig, requests_mock):
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)
    pos = Position(
        deal_id="123456789",
        size=1,
        create_date="mock",
        direction=TradeDirection.BUY,
        level=100,
        limit=110,
        stop=90,
        currency="GBP",
        epic="mock",
        market_id=None,
    )
    result = ig.close_position(pos)
    assert result


def test_close_position_fail(ig, requests_mock):
    ig_request_trade(requests_mock, fail=True)
    ig_request_confirm_trade(requests_mock, fail=True)
    pos = Position(
        deal_id="123456789",
        size=1,
        create_date="mock",
        direction=TradeDirection.BUY,
        level=100,
        limit=110,
        stop=90,
        currency="GBP",
        epic="mock",
        market_id=None,
    )
    result = ig.close_position(pos)
    assert result is False


def test_close_all_positions(ig, requests_mock):
    ig_request_open_positions(requests_mock)
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)
    result = ig.close_all_positions()
    assert result


def test_close_all_positions_fail(ig, requests_mock):
    ig_request_open_positions(requests_mock)
    ig_request_trade(requests_mock, fail=True)
    ig_request_confirm_trade(requests_mock)

    result = ig.close_all_positions()
    assert result is False

    ig_request_open_positions(requests_mock)
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(
        requests_mock,
        data={"dealId": "123456789", "dealStatus": "FAIL", "reason": "FAIL"},
    )

    result = ig.close_all_positions()
    assert result is False


def test_get_account_used_perc(ig, requests_mock):
    ig_request_account_details(requests_mock)
    perc = ig.get_account_used_perc()

    assert perc is not None
    assert perc == 62.138354775208285


def test_get_account_used_perc_fail(ig, requests_mock):
    ig_request_account_details(requests_mock, fail=True)
    with pytest.raises(RuntimeError):
        _ = ig.get_account_used_perc()


def test_navigate_market_node_nodes(ig, requests_mock):
    ig_request_navigate_market(requests_mock)
    data = ig.navigate_market_node("")
    assert "nodes" in data
    assert len(data["nodes"]) == 3
    assert data["nodes"][0]["id"] == "668394"
    assert data["nodes"][0]["name"] == "Cryptocurrency"
    assert data["nodes"][1]["id"] == "77976799"
    assert data["nodes"][1]["name"] == "Options (Australia 200)"
    assert data["nodes"][2]["id"] == "89291253"
    assert data["nodes"][2]["name"] == "Options (US Tech 100)"
    assert len(data["markets"]) == 0

    ig_request_navigate_market(requests_mock, fail=True)
    with pytest.raises(RuntimeError):
        data = ig.navigate_market_node("")


def test_navigate_market_node_markets(ig, requests_mock):
    ig_request_navigate_market(
        requests_mock, data="mock_navigate_markets_markets.json", args="12345678"
    )
    data = ig.navigate_market_node("12345678")
    assert "nodes" in data
    assert len(data["nodes"]) == 0
    assert "markets" in data
    assert len(data["markets"]) == 3
    assert data["markets"][0]["epic"] == "KC.D.AVLN8875P.DEC.IP"
    assert data["markets"][1]["epic"] == "KC.D.AVLN8875P.MAR.IP"
    assert data["markets"][2]["epic"] == "KC.D.AVLN8875P.JUN.IP"


def test_get_watchlist_markets(ig, requests_mock):
    ig_request_market_info(requests_mock)
    ig_request_watchlist(requests_mock, data="mock_watchlist_list.json")
    ig_request_watchlist(requests_mock, args="12345678", data="mock_watchlist.json")

    data = ig.get_markets_from_watchlist("My Watchlist")
    assert isinstance(data, list)
    assert len(data) == 3
    assert isinstance(data[0], Market)

    data = ig.get_markets_from_watchlist("wrong_name")
    assert len(data) == 0

    ig_request_watchlist(
        requests_mock, args="12345678", data="mock_watchlist.json", fail=True
    )
    data = ig.get_markets_from_watchlist("wrong_name")
    assert len(data) == 0
