import os
import sys
import inspect
import pytest
import json

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, "{}/src".format(parentdir))

from Interfaces.MarketProvider import MarketProvider
from common.MockComponents import MockBroker, MockIG, MockAV


@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    # Read configuration file
    try:
        with open("config/config.json", "r") as file:
            config = json.load(file)
    except IOError:
        exit()
    return config


def test_market_provider_epics_list(config):
    """
    Test the MarketProvider configured to fetch markets from an epics list
    """
    # Define configuration for this test
    config["alpha_vantage"]["enable"] = True
    config["general"]["market_source"]["value"] = "list"
    config["general"]["epic_ids_filepath"] = "test/test_data/epics_list.txt"

    # Mock services and other components
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_buy.json"),
    }
    broker = MockBroker(config, services)

    # Create class to test
    mp = MarketProvider(config, broker)

    # Request all markets and verify the MarketProvider return the correct ones
    # Run the test several times resetting the market provider
    for _ in range(4):
        expected_list = []
        with open("test/test_data/epics_list.txt", "r") as epics_list:
            for cnt, line in enumerate(epics_list):
                expected_list += [line.rstrip()]

        n = mp.next().epic
        assert n in expected_list
        expected_list.remove(n)
        try:
            while n:
                n = mp.next().epic
                assert n in expected_list
                expected_list.remove(n)
        except StopIteration:
            # Verify we read all epics in the list
            assert len(expected_list) == 0
            # Verify reading the next raise another exception
            with pytest.raises(StopIteration) as e:
                mp.next()
            mp.reset()
            continue
        # If we get here it means that next did not raise an exception at the end of the list
        assert False


def test_market_provider_watchlist(config):
    """
    Test the MarketProvider configured to fetch markets from an IG watchlist
    """
    # Define configuration for this test
    config["alpha_vantage"]["enable"] = True
    config["general"]["market_source"]["value"] = "watchlist"
    config["general"]["watchlist_name"] = "mock"

    # Mock services and other components
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_buy.json"),
    }
    broker = MockBroker(config, services)

    # Create class to test
    mp = MarketProvider(config, broker)

    # The MockBroker is configured to return a mock watchlist
    # Run the test several times resetting the market provider
    for _ in range(4):
        assert mp.next().epic == "EPIC1"
        assert mp.next().epic == "EPIC2"
        assert mp.next().epic == "EPIC3"
        assert mp.next().epic == "EPIC4"

        with pytest.raises(StopIteration) as e:
            mp.next()
        mp.reset()


def test_market_provider_api(config):
    """
    Test the MarketProvider configured to fetch markets from IG nodes
    """
    # Define configuration for this test
    config["alpha_vantage"]["enable"] = True
    config["general"]["market_source"]["value"] = "api"

    # Mock services and other components
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_buy.json"),
    }
    broker = MockBroker(config, services)

    # TODO
    # Create class to test
    #mp = MarketProvider(config, broker)
    assert True


def test_market_provider_market_from_epic(config):
    """
    Test the MarketProvider get_market_from_epic() function
    """
    # Define configuration for this test
    config["alpha_vantage"]["enable"] = True
    config["general"]["market_source"]["value"] = "list"
    config["general"]["epic_ids_filepath"] = "test/test_data/epics_list.txt"

    # Mock services and other components
    services = {
        "ig_index": MockIG(
            "test/test_data/mock_ig_market_info.json",
            "test/test_data/mock_ig_historic_price.json",
        ),
        "alpha_vantage": MockAV("test/test_data/mock_macdext_buy.json"),
    }
    broker = MockBroker(config, services)

    # Create class to test
    mp = MarketProvider(config, broker)
    market = mp.get_market_from_epic("MOCK")
    assert market is not None
    assert market.epic == "MOCK"