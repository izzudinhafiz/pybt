if __name__ == "__main__":
    import os
    import sys
    import inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)

from commons.money import Money
from commons.backtest import Market
from datetime import datetime, timedelta, time
import pytest
import csv
from pprint import pprint


def test_init():
    market = Market(asset_context=["AAPL"], start_date=datetime(2020, 12, 1), end_date=datetime(2020, 12, 3))
    first_day = market.calendar[0]
    last_day = market.calendar[-1]

    assert first_day.date == datetime(2020, 12, 1)
    assert last_day.date == datetime(2020, 12, 3)
    assert len(market.calendar) == 3


def test_ticking():
    market = Market(asset_context=["AAPL"], start_date=datetime(2020, 12, 1), end_date=datetime(2020, 12, 3))

    market.run_simulation()
    debug_date_list = []
    with open("tests\\debug_date_list.csv", "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            debug_date_list.append(row[0])

    debug_date_list = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in debug_date_list]

    for label_datetime, test_datetime in zip(debug_date_list, market._test_date_list):
        assert label_datetime == test_datetime

    assert market.total_tick == 1170  # 3 days of 9:30 AM to 4 PM
    assert market.day_counter == 3


test_init()
test_ticking()
