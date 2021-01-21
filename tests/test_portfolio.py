if __name__ == "__main__":
    import os
    import sys
    import inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)

from commons.money import Money
from commons.backtest import Market
from commons.backtest.datapack import PriceDataPack
from datetime import datetime
import csv
import os
from commons.models.market_model import Asset, Price, Financial, pg_db
import alpaca_trade_api as tradeapi


pg_db.bind([Asset, Price, Financial])
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")
datapack = PriceDataPack.load_cache("cached_test")


def test_portfolio_long_position():
    portfolio_label_data = []
    with open("tests\\portfolio_test.csv", "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            portfolio_label_data.append(row)

    market = Market(asset_context=["MMM"], start_date=datetime(2020, 12, 1), end_date=datetime(2020, 12, 3))
    market.load_calendar_data("alpaca", api_key=API_KEY, secret_key=SECRET_KEY)
    market.load_price_data(datapack)
    portfolio = market.register_portfolio(100_000)
    portfolio.open_position_by_size("MMM", 500)

    portfolio_label_data = portfolio_label_data[1:]

    for time, label_price, label_value, label_gain, label_total_equity, label_nett_gain in portfolio_label_data:
        portfolio.update()
        position = portfolio.open_positions[0]

        assert Money(label_price) == position.current_price
        assert Money(label_value) == position.current_value
        assert Money(label_gain) == position.gain
        assert Money(label_nett_gain) == portfolio.nett_gain
        assert Money(label_total_equity) == portfolio.cash + portfolio.equity
        market.next_tick()


def test_portfolio_short_position():
    portfolio_label_data = []
    with open("tests\\portfolio_short_test.csv", "r", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            portfolio_label_data.append(row)

    market = Market(asset_context=["MMM"], start_date=datetime(2020, 12, 1), end_date=datetime(2020, 12, 3))
    market.load_calendar_data("alpaca", api_key=API_KEY, secret_key=SECRET_KEY)
    market.load_price_data(datapack)
    portfolio = market.register_portfolio(100_000)
    portfolio.open_position_by_size("MMM", -500)

    portfolio_label_data = portfolio_label_data[1:]

    for time, label_price, label_value, label_gain, label_total_equity, label_nett_gain, label_margin in portfolio_label_data:
        portfolio.update()
        position = portfolio.open_positions[0]

        if Money(label_price) != position.current_price:
            print(market.time_now, Money(label_price), position.current_price)

        assert Money(label_price) == position.current_price
        assert Money(label_value) == position.current_value
        assert Money(label_gain) == position.gain
        assert Money(label_nett_gain) == portfolio.nett_gain
        assert Money(label_total_equity) == portfolio.cash + portfolio.equity
        assert Money(label_margin) == portfolio.margin
        market.next_tick()


# test_portfolio_short_position()
