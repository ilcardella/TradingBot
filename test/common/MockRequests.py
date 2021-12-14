import json
import re
from enum import Enum

from tradingbot.components.broker import IG_API_URL

# Set global variables used in fixtures
TEST_DATA_IG = "test/test_data/ig"
TEST_DATA_AV = "test/test_data/alpha_vantage"
TEST_DATA_YF = "test/test_data/yfinance"
IG_BASE_URI = IG_API_URL.BASE_URI.value.replace("@", IG_API_URL.DEMO_PREFIX.value)


class AV_API_URL(Enum):
    """AlphaVantage API URLs"""

    BASE_URI = "https://www.alphavantage.co/query?"
    MACD_EXT = "MACDEXT"
    TS_DAILY = "TIME_SERIES_DAILY"


class YF_API_URL(Enum):
    """YFinance API URLs"""

    BASE_URI = "https://query2.finance.yahoo.com/v8/finance/chart"


def read_json(filepath):
    """Read a JSON file"""
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except IOError:
        exit()


def ig_request_login(mock, data="mock_login.json", fail=False):
    """Mock login response"""
    mock.post(
        "{}/{}".format(IG_BASE_URI, IG_API_URL.SESSION.value),
        json=read_json("{}/{}".format(TEST_DATA_IG, data)),
        headers={"CST": "mock", "X-SECURITY-TOKEN": "mock"},
        status_code=401 if fail else 200,
    )


def ig_request_set_account(mock, data="mock_set_account.json", fail=False):
    """Mock set account response"""
    mock.put(
        "{}/{}".format(IG_BASE_URI, IG_API_URL.SESSION.value),
        json=read_json("{}/{}".format(TEST_DATA_IG, data)),
        status_code=401 if fail else 200,
    )


def ig_request_account_details(mock, data="mock_account_details.json", fail=False):
    """Mock account details"""
    mock.get(
        "{}/{}".format(IG_BASE_URI, IG_API_URL.ACCOUNTS.value),
        json=read_json("{}/{}".format(TEST_DATA_IG, data)),
        status_code=401 if fail else 200,
    )


def ig_request_open_positions(mock, data="mock_positions.json", fail=False):
    """Mock open positions call"""
    mock.get(
        "{}/{}".format(IG_BASE_URI, IG_API_URL.POSITIONS.value),
        json=read_json("{}/{}".format(TEST_DATA_IG, data)),
        status_code=401 if fail else 200,
    )


def ig_request_market_info(mock, args="", data="mock_market_info.json", fail=False):
    """Mock market info call"""
    mock.get(
        re.compile("{}/{}/{}".format(IG_BASE_URI, IG_API_URL.MARKETS.value, args)),
        json=data
        if isinstance(data, dict)
        else read_json("{}/{}".format(TEST_DATA_IG, data)),
        status_code=401 if fail else 200,
    )


def ig_request_search_market(mock, args="", data="mock_market_search.json", fail=False):
    """Mock market search call"""
    mock.get(
        re.compile(
            re.escape(
                "{}/{}?searchTerm={}".format(
                    IG_BASE_URI, IG_API_URL.MARKETS.value, args
                )
            )
        ),
        json=read_json("{}/{}".format(TEST_DATA_IG, data)),
        status_code=401 if fail else 200,
    )


def ig_request_prices(mock, args="", data="mock_historic_price.json", fail=False):
    """Mock prices call"""
    mock.get(
        re.compile("{}/{}/{}".format(IG_BASE_URI, IG_API_URL.PRICES.value, args)),
        json=read_json("{}/{}".format(TEST_DATA_IG, data)),
        status_code=401 if fail else 200,
    )


def ig_request_trade(mock, data={"dealReference": "123456789"}, fail=False):
    """Mock trade call"""
    mock.post(
        "{}/{}".format(IG_BASE_URI, IG_API_URL.POSITIONS_OTC.value),
        json=data,
        status_code=401 if fail else 200,
    )


def ig_request_confirm_trade(
    mock,
    data={"dealId": "123456789", "dealStatus": "SUCCESS", "reason": "SUCCESS"},
    fail=False,
):
    """Mock confirm trade call"""
    mock.get(
        "{}/{}/{}".format(IG_BASE_URI, IG_API_URL.CONFIRMS.value, data["dealId"]),
        json=data,
        status_code=401 if fail else 200,
    )


def ig_request_navigate_market(
    mock, args="", data="mock_navigate_markets_nodes.json", fail=False
):
    """Mock navigate market call"""
    mock.get(
        re.compile("{}/{}/{}".format(IG_BASE_URI, IG_API_URL.MARKET_NAV.value, args)),
        json=read_json("{}/{}".format(TEST_DATA_IG, data)),
        status_code=401 if fail else 200,
    )


def ig_request_watchlist(mock, args="", data="mock_watchlist_list.json", fail=False):
    """Mock watchlist call"""
    mock.get(
        re.compile("{}/{}/{}".format(IG_BASE_URI, IG_API_URL.WATCHLISTS.value, args)),
        json=read_json("{}/{}".format(TEST_DATA_IG, data)),
        status_code=401 if fail else 200,
    )


###################################################################
# Alpha Vantage mock requests
###################################################################


def av_request_macd_ext(mock, args="", data="mock_macd_ext_buy.json", fail=False):
    """Mock MACD EXT call"""
    mock.get(
        re.compile(
            re.escape(
                "{}function={}&symbol={}".format(
                    AV_API_URL.BASE_URI.value, AV_API_URL.MACD_EXT.value, args
                )
            )
        ),
        json=data
        if isinstance(data, dict)
        else read_json("{}/{}".format(TEST_DATA_AV, data)),
        status_code=401 if fail else 200,
    )


def av_request_prices(mock, args="", data="mock_av_daily.json", fail=False):
    """Mock AV prices"""
    mock.get(
        re.compile(
            re.escape(
                "{}function={}&symbol={}".format(
                    AV_API_URL.BASE_URI.value, AV_API_URL.TS_DAILY.value, args
                )
            )
        ),
        json=data
        if isinstance(data, dict)
        else read_json("{}/{}".format(TEST_DATA_AV, data)),
        status_code=401 if fail else 200,
    )


###################################################################
# Yahoo Finance mock requests
###################################################################


def yf_request_prices(mock, args="", data="mock_history_day_max.json", fail=False):
    """Mock YF prices"""
    mock.get(
        re.compile(re.escape("{}/{}".format(YF_API_URL.BASE_URI.value, args))),
        json=data
        if isinstance(data, dict)
        else read_json("{}/{}".format(TEST_DATA_YF, data)),
        status_code=401 if fail else 200,
    )
