import os
import sys
import inspect
import pytest

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from scripts.Strategies.SimpleMACD import SimpleMACD

class MockBroker:
    """
    Mock broker interface class
    """
    def __init__(self):
        pass

    # TODO implement mock functions used by SimpleMACD

@pytest.fixture
def config():
    """
    Returns a dict with config parameter for strategy and simpleMACD
    """
    return {
        # TODO fill required params
        }
    }

@pytest.fixture
def broker():
    return MockBroker()

def test_find_trade_signal(config, broker):
    # TODO
    assert True
