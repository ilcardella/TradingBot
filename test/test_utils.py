from tradingbot.components import Utils


def test_midpoint():
    assert Utils.midpoint(0, 10) == 5
    assert Utils.midpoint(-10, 10) == 0
    assert Utils.midpoint(10, -10) == 0
    assert Utils.midpoint(0, 0) == 0
    assert Utils.midpoint(1, 2) == 1.5


def test_percentage_of():
    assert Utils.percentage_of(1, 100) == 1
    assert Utils.percentage_of(0, 100) == 0
    assert Utils.percentage_of(1, 1) == 0.01


def test_percentage():
    assert Utils.percentage(1, 100) == 1
    assert Utils.percentage(0, 100) == 0
    assert Utils.percentage(200, 100) == 200
    # with pytest.raises(Exception):
    #     assert Utils.percentage(-1,100)
    # with pytest.raises(Exception):
    #     assert Utils.percentage(1,-100)


def test_is_between():
    mock = "10:10"
    assert Utils.is_between(mock, ("10:09", "10:11"))
    mock = "00:00"
    assert Utils.is_between(mock, ("23:59", "00:01"))


def test_humanize_time():
    assert Utils.humanize_time(3600) == "01:00:00"
    assert Utils.humanize_time(4800) == "01:20:00"
    assert Utils.humanize_time(4811) == "01:20:11"
