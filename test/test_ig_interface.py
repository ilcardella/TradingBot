import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from Interfaces.IGInterface import IGInterface, IG_API_URL


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
def mock_auth(requests_mock):
    # Define mock requests
    mock_headers = {"CST": "mock", "X-SECURITY-TOKEN": "mock"}
    data = read_json("test/test_data/mock_ig_login.json")
    requests_mock.post(
        "https://demo-api.ig.com/gateway/deal/session", json=data, headers=mock_headers
    )
    data = read_json("test/test_data/mock_ig_set_account.json")
    requests_mock.put("https://demo-api.ig.com/gateway/deal/session", json=data)


@pytest.fixture
def ig(config, credentials, mock_auth):
    """
    Returns a instance of IGInterface
    """
    return IGInterface(config, credentials)


def read_json(filepath):
    # Read mock file
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except IOError:
        exit()


def test_init(ig, config):
    assert ig.orderType == config["ig_interface"]["order_type"]
    assert ig.orderSize == config["ig_interface"]["order_size"]
    assert ig.orderExpiry == config["ig_interface"]["order_expiry"]
    assert ig.orderCurrency == config["ig_interface"]["order_currency"]
    assert ig.orderForceOpen == config["ig_interface"]["order_force_open"]
    assert ig.useGStop == config["ig_interface"]["use_g_stop"]
    assert ig.useDemo == config["ig_interface"]["use_demo_account"]
    assert ig.paperTrading == config["ig_interface"]["paper_trading"]


def test_authenticate(ig, credentials, requests_mock):
    # Define mock requests
    mock_headers = {"CST": "mock", "X-SECURITY-TOKEN": "mock"}
    data = read_json("test/test_data/mock_ig_login.json")
    requests_mock.post(ig.apiBaseURL + "/session", json=data, headers=mock_headers)
    data = read_json("test/test_data/mock_ig_set_account.json")
    requests_mock.put(ig.apiBaseURL + "/session", json=data)

    # Call function to test
    result = ig.authenticate(credentials)

    # Assert results
    assert ig.authenticated_headers["CST"] == mock_headers["CST"]
    assert (
        ig.authenticated_headers["X-SECURITY-TOKEN"] == mock_headers["X-SECURITY-TOKEN"]
    )
    assert result == True


def test_authenticate_fail(ig, credentials, requests_mock):
    # Define mock requests
    mock_headers = {"CST": "mock", "X-SECURITY-TOKEN": "mock"}
    data = {"errorCode": "error.security.invalid-details"}
    requests_mock.post(
        ig.apiBaseURL + "/session", text="Fail", status_code=401, headers=mock_headers
    )
    data = read_json("test/test_data/mock_ig_set_account.json")
    requests_mock.put(ig.apiBaseURL + "/session", text="Success")

    # Call function to test
    result = ig.authenticate(credentials)

    # Assert results
    assert result == False


def test_set_default_account(ig, credentials, requests_mock):
    data = read_json("test/test_data/mock_ig_set_account.json")
    requests_mock.put(ig.apiBaseURL + "/session", status_code=200, json=data)

    result = ig.set_default_account(credentials["account_id"])

    assert result == True


def test_set_default_account_fail(ig, credentials, requests_mock):
    requests_mock.put(ig.apiBaseURL + "/session", status_code=403, text="Success")

    result = ig.set_default_account(credentials["account_id"])

    assert result == False


def test_get_account_balances(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_account_details.json")
    requests_mock.get(ig.apiBaseURL + "/accounts", status_code=200, json=data)
    balance, deposit = ig.get_account_balances()

    assert balance is not None
    assert deposit is not None
    assert balance == 16093.12
    assert deposit == 0.0


def test_get_account_balances_fail(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_account_details.json")
    requests_mock.get(ig.apiBaseURL + "/accounts", status_code=401, json=data)
    balance, deposit = ig.get_account_balances()

    assert balance is None
    assert deposit is None


def test_get_open_positions(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_positions.json")
    requests_mock.get(ig.apiBaseURL + "/positions", status_code=200, json=data)

    positions = ig.get_open_positions()

    assert positions is not None
    assert "positions" in positions


def test_get_open_positions_fail(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_positions.json")
    requests_mock.get(ig.apiBaseURL + "/positions", status_code=401, json=data)

    positions = ig.get_open_positions()

    assert positions is None


def test_get_market_info(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_market_info.json")
    requests_mock.get(ig.apiBaseURL + "/markets/mock", status_code=200, json=data)

    info = ig.get_market_info("mock")

    assert info is not None
    assert "instrument" in info
    assert "snapshot" in info
    assert "dealingRules" in info


def test_get_market_info_fail(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_market_info.json")
    requests_mock.get(ig.apiBaseURL + "/markets/mock", status_code=401, json=data)

    info = ig.get_market_info("mock")

    assert info is None


def test_get_prices(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_historic_price.json")
    requests_mock.get(
        ig.apiBaseURL + "/prices/mock/mock/mock", status_code=200, json=data
    )

    p = ig.get_prices("mock", "mock", "mock")

    assert p is not None
    assert "prices" in p


def test_get_prices_fail(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_historic_price.json")
    requests_mock.get(
        ig.apiBaseURL + "/prices/mock/mock/mock", status_code=401, json=data
    )

    p = ig.get_prices("mock", "mock", "mock")

    assert p is None


def test_trade(ig, requests_mock):
    data = {"dealReference": "123456789"}
    requests_mock.post(ig.apiBaseURL + "/positions/otc", status_code=200, json=data)
    data = {"dealId": "123456789", "dealStatus": "SUCCESS", "reason": "SUCCESS"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)

    result = ig.trade("mock", "BUY", 0, 0)

    assert result


def test_trade_fail(ig, requests_mock):
    data = {"dealReference": "123456789"}
    requests_mock.post(ig.apiBaseURL + "/positions/otc", status_code=401, json=data)
    data = {"dealId": "123456789", "dealStatus": "SUCCESS", "reason": "SUCCESS"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)

    result = ig.trade("mock", "BUY", 0, 0)

    assert result == False


def test_confirm_order(ig, requests_mock):
    data = {"dealId": "123456789", "dealStatus": "SUCCESS", "reason": "SUCCESS"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)

    result = ig.confirm_order("123456789")

    assert result


def test_confirm_order_fail(ig, requests_mock):
    data = {"dealId": "123456789", "dealStatus": "REJECTED", "reason": "FAIL"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)
    result = ig.confirm_order("123456789")
    assert result == False

    data = {"dealId": "123456789", "dealStatus": "MOCK", "reason": "SUCCESS"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=401, json=data)
    result = ig.confirm_order("123456789")
    assert result == False


def test_close_position(ig, requests_mock):
    data = {"dealReference": "123456789"}
    requests_mock.post(ig.apiBaseURL + "/positions/otc", status_code=200, json=data)
    data = {"dealId": "123456789", "dealStatus": "SUCCESS", "reason": "SUCCESS"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)
    pos = {
        "market": {"instrumentName": "mock"},
        "position": {"direction": "BUY", "dealId": "123456789"},
    }
    result = ig.close_position(pos)
    assert result


def test_close_position_fail(ig, requests_mock):
    data = {"dealReference": "123456789"}
    requests_mock.post(ig.apiBaseURL + "/positions/otc", status_code=401, json=data)
    data = {"dealId": "123456789", "dealStatus": "SUCCESS", "reason": "SUCCESS"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)
    pos = {
        "market": {"instrumentName": "mock"},
        "position": {"direction": "BUY", "dealId": "123456789"},
    }
    result = ig.close_position(pos)
    assert result == False


def test_close_all_positions(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_positions.json")
    requests_mock.get(ig.apiBaseURL + "/positions", status_code=200, json=data)
    data = {"dealReference": "123456789"}
    requests_mock.post(ig.apiBaseURL + "/positions/otc", status_code=200, json=data)
    data = {"dealId": "123456789", "dealStatus": "SUCCESS", "reason": "SUCCESS"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)

    result = ig.close_all_positions()
    assert result


def test_close_all_positions_fail(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_positions.json")
    requests_mock.get(ig.apiBaseURL + "/positions", status_code=200, json=data)
    data = {"dealReference": "123456789"}
    requests_mock.post(ig.apiBaseURL + "/positions/otc", status_code=401, json=data)
    data = {"dealId": "123456789", "dealStatus": "SUCCESS", "reason": "SUCCESS"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)
    result = ig.close_all_positions()
    assert result == False

    data = read_json("test/test_data/mock_ig_positions.json")
    requests_mock.get(ig.apiBaseURL + "/positions", status_code=200, json=data)
    data = {"dealReference": "123456789"}
    requests_mock.post(ig.apiBaseURL + "/positions/otc", status_code=200, json=data)
    data = {"dealId": "123456789", "dealStatus": "FAIL", "reason": "FAIL"}
    requests_mock.get(ig.apiBaseURL + "/confirms/123456789", status_code=200, json=data)
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
    data = read_json("test/test_data/mock_ig_account_details.json")
    requests_mock.get(ig.apiBaseURL + "/accounts", status_code=200, json=data)
    perc = ig.get_account_used_perc()

    assert perc is not None
    assert perc == 0


def test_get_account_used_perc_fail(ig, requests_mock):
    data = read_json("test/test_data/mock_ig_account_details.json")
    requests_mock.get(ig.apiBaseURL + "/accounts", status_code=401, json=data)
    perc = ig.get_account_used_perc()

    assert perc is None


def test_navigate_market_node_nodes(ig, requests_mock):
    mock = {
        "nodes": [
            {"id": "668394", "name": "Cryptocurrency"},
            {"id": "77976799", "name": "Options (Australia 200)"},
            {"id": "89291253", "name": "Options (US Tech 100)"},
        ],
        "markets": None,
    }
    requests_mock.get(
        "{}/{}/".format(ig.apiBaseURL, IG_API_URL.MARKET_NAV.value),
        status_code=200,
        json=mock,
    )

    data = ig.navigate_market_node("")
    assert data == mock

    data = ig.navigate_market_node("123")
    assert data is None

    requests_mock.get(
        "{}/{}/".format(ig.apiBaseURL, IG_API_URL.MARKET_NAV.value),
        status_code=401,
        json=mock,
    )

    data = ig.navigate_market_node("")
    assert data is None


def test_navigate_market_node_markets(ig, requests_mock):
    mock = {
        "nodes": None,
        "markets": [
            {
                "delayTime": 0,
                "epic": "KC.D.AVLN8875P.DEC.IP",
                "netChange": 0.01,
                "lotSize": 0,
                "expiry": "DEC-18",
                "instrumentType": "SHARES",
                "instrumentName": "General Accident PLC 8.875 Pfd",
                "high": 134.55,
                "low": 129.5,
                "percentageChange": 0.01,
                "updateTime": "4461000",
                "updateTimeUTC": "02:14:21",
                "bid": 131.49,
                "offer": 132.54,
                "otcTradeable": True,
                "streamingPricesAvailable": False,
                "marketStatus": "EDITS_ONLY",
                "scalingFactor": 1,
            },
            {
                "delayTime": 0,
                "epic": "KC.D.AVLN8875P.MAR.IP",
                "netChange": 0.0,
                "lotSize": 0,
                "expiry": "MAR-19",
                "instrumentType": "SHARES",
                "instrumentName": "General Accident PLC 8.875 Pfd",
                "high": 135.03,
                "low": 129.84,
                "percentageChange": 0.0,
                "updateTime": "4461000",
                "updateTimeUTC": "02:14:21",
                "bid": 131.82,
                "offer": 133.01,
                "otcTradeable": True,
                "streamingPricesAvailable": False,
                "marketStatus": "EDITS_ONLY",
                "scalingFactor": 1,
            },
            {
                "delayTime": 0,
                "epic": "KC.D.AVLN8875P.JUN.IP",
                "netChange": 0.01,
                "lotSize": 0,
                "expiry": "JUN-19",
                "instrumentType": "SHARES",
                "instrumentName": "General Accident PLC 8.875 Pfd",
                "high": 135.64,
                "low": 130.04,
                "percentageChange": 0.0,
                "updateTime": "4461000",
                "updateTimeUTC": "02:14:21",
                "bid": 132.03,
                "offer": 133.62,
                "otcTradeable": True,
                "streamingPricesAvailable": False,
                "marketStatus": "EDITS_ONLY",
                "scalingFactor": 1,
            },
        ],
    }
    requests_mock.get(
        "{}/{}/12345678".format(ig.apiBaseURL, IG_API_URL.MARKET_NAV.value),
        status_code=200,
        json=mock,
    )

    data = ig.navigate_market_node("12345678")
    assert data == mock

    def test_get_watchlist(ig, requests_mock):
        mock = {
            "watchlists": [
                {
                    "id": "12345678",
                    "name": "My Watchlist",
                    "editable": true,
                    "deleteable": false,
                    "defaultSystemWatchlist": false,
                },
                {
                    "id": "Popular Markets",
                    "name": "Popular Markets",
                    "editable": false,
                    "deleteable": false,
                    "defaultSystemWatchlist": true,
                },
                {
                    "id": "Major Indices",
                    "name": "Major Indices",
                    "editable": false,
                    "deleteable": false,
                    "defaultSystemWatchlist": false,
                },
                {
                    "id": "6817448",
                    "name": "Major FX",
                    "editable": false,
                    "deleteable": false,
                    "defaultSystemWatchlist": false,
                },
                {
                    "id": "Major Commodities",
                    "name": "Major Commodities",
                    "editable": false,
                    "deleteable": false,
                    "defaultSystemWatchlist": false,
                },
            ]
        }
        requests_mock.get(
            "{}/{}/".format(ig.apiBaseURL, IG_API_URL.WATCHLISTS.value),
            status_code=200,
            json=mock,
        )
        data = ig.get_watchlist("")
        assert mock == data

        requests_mock.get(
            "{}/{}/".format(ig.apiBaseURL, IG_API_URL.WATCHLISTS.value),
            status_code=401,
            json=mock,
        )
        data = ig.get_watchlist("")
        assert data is None

        requests_mock.get(
            "{}/{}/".format(ig.apiBaseURL, IG_API_URL.WATCHLISTS.value),
            status_code=200,
            json={"errorCode": ""},
        )
        data = ig.get_watchlist("")
        assert data is None

    def test_get_markets_from_watchlist(ig, requests_mock):
        mock = {
            "watchlists": [
                {
                    "id": "12345678",
                    "name": "My Watchlist",
                    "editable": true,
                    "deleteable": false,
                    "defaultSystemWatchlist": false,
                },
                {
                    "id": "Popular Markets",
                    "name": "Popular Markets",
                    "editable": false,
                    "deleteable": false,
                    "defaultSystemWatchlist": true,
                },
                {
                    "id": "Major Indices",
                    "name": "Major Indices",
                    "editable": false,
                    "deleteable": false,
                    "defaultSystemWatchlist": false,
                },
                {
                    "id": "6817448",
                    "name": "Major FX",
                    "editable": false,
                    "deleteable": false,
                    "defaultSystemWatchlist": false,
                },
                {
                    "id": "Major Commodities",
                    "name": "Major Commodities",
                    "editable": false,
                    "deleteable": false,
                    "defaultSystemWatchlist": false,
                },
            ]
        }
        mock_watchlist = {
            "markets": [
                {
                    "instrumentName": "Bitcoin",
                    "expiry": "DFB",
                    "epic": "CS.D.BITCOIN.TODAY.IP",
                    "instrumentType": "CURRENCIES",
                    "marketStatus": "TRADEABLE",
                    "lotSize": 1.0,
                    "high": 3247.4,
                    "low": 3106.7,
                    "percentageChange": -0.25,
                    "netChange": -7.87,
                    "bid": 3129.72,
                    "offer": 3169.72,
                    "updateTime": "18:11:51",
                    "updateTimeUTC": "18:11:51",
                    "delayTime": 0,
                    "streamingPricesAvailable": true,
                    "scalingFactor": 1,
                },
                {
                    "instrumentName": "FTSE 100",
                    "expiry": "DFB",
                    "epic": "IX.D.FTSE.DAILY.IP",
                    "instrumentType": "INDICES",
                    "marketStatus": "EDITS_ONLY",
                    "lotSize": 10.0,
                    "high": 6847.1,
                    "low": 6788.2,
                    "percentageChange": -0.59,
                    "netChange": -40.5,
                    "bid": 6790.8,
                    "offer": 6794.8,
                    "updateTime": "02:14:21",
                    "updateTimeUTC": "02:14:21",
                    "delayTime": 0,
                    "streamingPricesAvailable": true,
                    "scalingFactor": 1,
                },
                {
                    "instrumentName": "Germany 30",
                    "expiry": "DFB",
                    "epic": "IX.D.DAX.DAILY.IP",
                    "instrumentType": "INDICES",
                    "marketStatus": "EDITS_ONLY",
                    "lotSize": 25.0,
                    "high": 10875.8,
                    "low": 10804.0,
                    "percentageChange": -0.37,
                    "netChange": -40.4,
                    "bid": 10809.4,
                    "offer": 10814.4,
                    "updateTime": "02:14:21",
                    "updateTimeUTC": "02:14:21",
                    "delayTime": 0,
                    "streamingPricesAvailable": true,
                    "scalingFactor": 1,
                },
            ]
        }

        requests_mock.get(
            "{}/{}/".format(ig.apiBaseURL, IG_API_URL.WATCHLISTS.value),
            status_code=200,
            json=mock,
        )
        requests_mock.get(
            "{}/{}/12345678".format(ig.apiBaseURL, IG_API_URL.WATCHLISTS.value),
            status_code=200,
            json=mock_watchlist,
        )

        data = ig.get_markets_from_watchlist("My Watchlist")
        assert data == mock_watchlist

        data = ig.get_markets_from_watchlist("wrong_name")
        assert data is None
