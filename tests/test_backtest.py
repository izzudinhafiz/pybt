if __name__ == "__main__":
    import os
    import sys
    import inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)

from pybt.commons import Money
from pybt import Market
from pybt.datapack import PriceDataPack
from datetime import datetime, time, date
import csv
import os
import time
import alpaca_trade_api as tradeapi

SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")
datapack = PriceDataPack.load_cache("cached_test")


def test_init():
    market = Market(asset_context=["AAPL"], start_date=datetime(2020, 12, 1), end_date=datetime(2020, 12, 3))
    market.load_calendar_data("alpaca", api_key=API_KEY, secret_key=SECRET_KEY)
    market.load_price_data(datapack)
    first_day = market.calendar[0]
    last_day = market.calendar[-1]

    assert first_day.date == date(2020, 12, 1)
    assert last_day.date == date(2020, 12, 3)
    assert len(market.calendar) == 3


def test_ticking():
    market = Market(asset_context=["AAPL"], start_date=datetime(2020, 12, 1), end_date=datetime(2020, 12, 3), test_mode=True)
    market.load_calendar_data("alpaca", api_key=API_KEY, secret_key=SECRET_KEY)
    market.load_price_data(datapack)
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
    market.load_calendar_data("alpaca", api_key=API_KEY, secret_key=SECRET_KEY)
    market.load_price_data(datapack)
    debug_price_list = []
    with open("tests\\price_interp.csv", "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            debug_price_list.append(row[4])

    debug_price_list = debug_price_list[1:]

    for i in range(3*390):
        price = market.get_current_price("MMM")
        test_price = Money(debug_price_list[i])

        print(market.time_now, test_price, price)
        assert price == test_price
        market.next_tick()


def test_loop_speed():
    assets_symbol = datapack.symbols
    market = Market(asset_context=assets_symbol, end_date=datetime(2015, 1, 30))
    market.load_calendar_data("alpaca", api_key=API_KEY, secret_key=SECRET_KEY)
    market.load_price_data(datapack)
    portfolio = market.register_portfolio(1000*len(assets_symbol))

    ASSET_COUNT = 100
    for i in range(ASSET_COUNT):
        portfolio.open_position_by_value(assets_symbol[i], 1000)

    start_time = time.time()
    LOOP_COUNT = 100
    for i in range(LOOP_COUNT):
        for position in portfolio.open_positions:
            position.update()
        market.next_tick()

    elapsed = time.time() - start_time
    loop_time = (elapsed / LOOP_COUNT) * 1000
    loop_position_time = loop_time / len(portfolio.open_positions) * 1000

    print(f"Loop Time: {loop_position_time:.0f} µs")
    assert loop_position_time <= 65
    # print(f"Total time: {elapsed:.2f} s | Avg Time/Loop: {(elapsed / LOOP_COUNT) *1000:.2f} ms | Avg Time/Loop/Position: {(elapsed / LOOP_COUNT / len(portfolio.positions)) * 1000 * 1000:.0f} µs ")
