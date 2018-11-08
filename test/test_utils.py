import os
import sys
import inspect
import pytest

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from scripts.Utils import Utils

def test_midpoint():
    assert Utils.midpoint(0,10) == 5
    assert Utils.midpoint(-10, 10) == 0
    assert Utils.midpoint(0, 0) == 0
    assert Utils.midpoint(1,2) == 1.5

def test_percentage_of():
    assert Utils.percentage_of(1,100) == 1
    assert Utils.percentage_of(0,100) == 0
    assert Utils.percentage_of(1,1) == 0.01
