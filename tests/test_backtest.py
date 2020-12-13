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
import os
import time
from commons.models.market_model import Asset, Price, Financial, pg_db
import alpaca_trade_api as tradeapi

pg_db.bind([Asset, Price, Financial])
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")


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


def test_current_price():
    market = Market(asset_context=["MMM"], start_date=datetime(2020, 12, 1), end_date=datetime(2020, 12, 3))

    debug_price_list = []
    with open("tests\\price_interp.csv", "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            debug_price_list.append(row[4])

    debug_price_list = debug_price_list[1:]

    for i in range(3*390):
        price = market.get_current_price("MMM")
        test_price = Money(float(debug_price_list[i]))

        assert price == test_price
        market.next_tick()


def test_loop_speed():
    assets_symbol = [x.symbol for x in Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True))]
    mt = Market(asset_context=assets_symbol, end_date=datetime(2015, 1, 30))
    portfolio = mt.register_portfolio(1000*len(assets_symbol))

    ASSET_COUNT = 100
    for i in range(ASSET_COUNT):
        portfolio.open_position_by_value(assets_symbol[i], 1000)

    start_time = time.time()
    LOOP_COUNT = 100
    for i in range(LOOP_COUNT):
        for position in portfolio.positions:
            position.update()
        mt.next_tick()

    elapsed = time.time() - start_time
    loop_time = (elapsed / LOOP_COUNT) * 1000
    loop_position_time = loop_time / len(portfolio.positions) * 1000

    assert loop_position_time <= 55
    # print(f"Total time: {elapsed:.2f} s | Avg Time/Loop: {(elapsed / LOOP_COUNT) *1000:.2f} ms | Avg Time/Loop/Position: {(elapsed / LOOP_COUNT / len(portfolio.positions)) * 1000 * 1000:.0f} µs ")
