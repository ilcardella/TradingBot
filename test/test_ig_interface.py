import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from Components.IGInterface import IGInterface
from common.MockRequests import (
    ig_request_login,
    ig_request_set_account,
    ig_request_account_details,
    ig_request_open_positions,
    ig_request_market_info,
    ig_request_search_market,
    ig_request_prices,
    ig_request_trade,
    ig_request_confirm_trade,
    ig_request_navigate_market,
    ig_request_watchlist,
)


@pytest.fixture
def config():
    """
    Returns a dict with config parameter for ig_interface
    """
    return {
        "ig_interface": {
            "order_type": "MARKET",
            "order_size": 1,
            "order_expiry": "DFB",
            "order_currency": "GBP",
            "order_force_open": True,
            "use_g_stop": True,
            "use_demo_account": True,
            "controlled_risk": True,
            "paper_trading": False,
        }
    }


@pytest.fixture
def credentials():
    """
    Returns a dict with credentials parameters
    """
    return {
        "username": "user",
        "password": "pwd",
        "api_key": "12345",
        "account_id": "12345",
        "av_api_key": "12345",
    }


@pytest.fixture
def ig(requests_mock, config, credentials):
    """
    Returns a instance of IGInterface
    """
    ig_request_login(requests_mock)
    ig_request_set_account(requests_mock)
    return IGInterface(config, credentials)


def test_init(ig, config):
    assert ig.orderType == config["ig_interface"]["order_type"]
    assert ig.orderSize == config["ig_interface"]["order_size"]
    assert ig.orderExpiry == config["ig_interface"]["order_expiry"]
    assert ig.orderCurrency == config["ig_interface"]["order_currency"]
    assert ig.orderForceOpen == config["ig_interface"]["order_force_open"]
    assert ig.useGStop == config["ig_interface"]["use_g_stop"]
    assert ig.useDemo == config["ig_interface"]["use_demo_account"]
    assert ig.paperTrading == config["ig_interface"]["paper_trading"]


# No need to use requests_mock fixture as "ig" already does that
def test_authenticate(ig, credentials):
    # Call function to test
    result = ig.authenticate(credentials)
    # Assert results
    assert ig.authenticated_headers["CST"] == "mock"
    assert ig.authenticated_headers["X-SECURITY-TOKEN"] == "mock"
    assert result == True


def test_authenticate_fail(requests_mock, ig, credentials):
    ig_request_login(requests_mock, fail=True)
    ig_request_set_account(requests_mock, fail=True)
    # Call function to test
    result = ig.authenticate(credentials)
    # Assert results
    assert result == False


# No need to use requests_mock fixture
def test_set_default_account(ig, credentials):
    result = ig.set_default_account(credentials["account_id"])
    assert result == True


def test_set_default_account_fail(requests_mock, ig, credentials):
    ig_request_set_account(requests_mock, fail=True)
    result = ig.set_default_account(credentials["account_id"])
    assert result == False


def test_get_account_balances(requests_mock, ig):
    ig_request_account_details(requests_mock)
    balance, deposit = ig.get_account_balances()
    assert balance is not None
    assert deposit is not None
    assert balance == 16093.12
    assert deposit == 0.0


def test_get_account_balances_fail(requests_mock, ig):
    ig_request_account_details(requests_mock, fail=True)
    balance, deposit = ig.get_account_balances()
    assert balance is None
    assert deposit is None


def test_get_open_positions(ig, requests_mock):
    ig_request_open_positions(requests_mock)

    positions = ig.get_open_positions()

    assert positions is not None
    assert "positions" in positions


def test_get_open_positions_fail(ig, requests_mock):
    ig_request_open_positions(requests_mock, fail=True)
    positions = ig.get_open_positions()

    assert positions is None


def test_get_market_info(ig, requests_mock):
    ig_request_market_info(requests_mock)
    info = ig.get_market_info("mock")

    assert info is not None
    assert "instrument" in info
    assert "snapshot" in info
    assert "dealingRules" in info


def test_get_market_info_fail(ig, requests_mock):
    ig_request_market_info(requests_mock, fail=True)
    info = ig.get_market_info("mock")
    assert info is None


def test_search_market(ig, requests_mock):
    ig_request_search_market(requests_mock)
    markets = ig.search_market("mock")

    assert markets is not None
    assert len(markets) == 8
    assert "epic" in markets[0]
    assert "expiry" in markets[0]
    assert "bid" in markets[0]
    assert "offer" in markets[0]


def test_search_market_fail(ig, requests_mock):
    ig_request_search_market(requests_mock, fail=True)
    markets = ig.search_market("mock")
    assert markets is None


def test_get_prices(ig, requests_mock):
    ig_request_prices(requests_mock)
    p = ig.get_prices("mock", "mock", "mock")
    assert p is not None
    assert "prices" in p


def test_get_prices_fail(ig, requests_mock):
    ig_request_prices(requests_mock, fail=True)
    p = ig.get_prices("mock", "mock", "mock")
    assert p is None


def test_trade(ig, requests_mock):
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)
    result = ig.trade("mock", "BUY", 0, 0)
    assert result


def test_trade_fail(ig, requests_mock):
    ig_request_trade(requests_mock, fail=True)
    ig_request_confirm_trade(requests_mock, fail=True)
    result = ig.trade("mock", "BUY", 0, 0)
    assert result == False


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
    assert result == False

    ig_request_confirm_trade(requests_mock, fail=True)
    result = ig.confirm_order("123456789")
    assert result == False


def test_close_position(ig, requests_mock):
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(requests_mock)
    pos = {
        "market": {"instrumentName": "mock"},
        "position": {"direction": "BUY", "dealId": "123456789"},
    }
    result = ig.close_position(pos)
    assert result


def test_close_position_fail(ig, requests_mock):
    ig_request_trade(requests_mock, fail=True)
    ig_request_confirm_trade(requests_mock, fail=True)
    pos = {
        "market": {"instrumentName": "mock"},
        "position": {"direction": "BUY", "dealId": "123456789"},
    }
    result = ig.close_position(pos)
    assert result == False


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
    assert result == False

    ig_request_open_positions(requests_mock)
    ig_request_trade(requests_mock)
    ig_request_confirm_trade(
        requests_mock,
        data={"dealId": "123456789", "dealStatus": "FAIL", "reason": "FAIL"},
    )

    result = ig.close_all_positions()
    assert result == False


def test_http_get(ig, requests_mock):
    data = {"mock1": "mock", "mock2": 2}
    requests_mock.get("http://www.mock.com", status_code=200, json=data)
    response = ig.http_get("http://www.mock.com")

    assert response is not None
    assert isinstance(response, dict)
    assert response == data


def test_get_account_used_perc(ig, requests_mock):
    ig_request_account_details(requests_mock)
    perc = ig.get_account_used_perc()

    assert perc is not None
    assert perc == 0


def test_get_account_used_perc_fail(ig, requests_mock):
    ig_request_account_details(requests_mock, fail=True)
    perc = ig.get_account_used_perc()

    assert perc is None


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
    data = ig.navigate_market_node("")
    assert data is None


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


def test_get_watchlist_list(ig, requests_mock):
    ig_request_watchlist(requests_mock)
    data = ig.get_watchlist("")
    assert "watchlists" in data
    assert len(data["watchlists"]) == 5
    assert data["watchlists"][0]["id"] == "12345678"
    assert data["watchlists"][1]["id"] == "Popular Markets"
    assert data["watchlists"][2]["id"] == "Major Indices"
    assert data["watchlists"][3]["id"] == "6817448"
    assert data["watchlists"][4]["id"] == "Major Commodities"

    ig_request_watchlist(requests_mock, fail=True)
    data = ig.get_watchlist("")
    assert data is None

    ig_request_watchlist(requests_mock, data="mock_error.json")
    data = ig.get_watchlist("")
    assert data is None


def test_get_watchlist_markets(ig, requests_mock):
    ig_request_watchlist(requests_mock, data="mock_watchlist_list.json")
    ig_request_watchlist(requests_mock, args="12345678", data="mock_watchlist.json")

    data = ig.get_markets_from_watchlist("My Watchlist")
    assert isinstance(data, list)
    assert len(data) == 3
    assert data[0]["epic"] == "CS.D.BITCOIN.TODAY.IP"
    assert data[1]["epic"] == "IX.D.FTSE.DAILY.IP"
    assert data[2]["epic"] == "IX.D.DAX.DAILY.IP"

    data = ig.get_markets_from_watchlist("wrong_name")
    assert data is None

    ig_request_watchlist(
        requests_mock, args="12345678", data="mock_watchlist.json", fail=True
    )
    data = ig.get_markets_from_watchlist("wrong_name")
    assert data is None
