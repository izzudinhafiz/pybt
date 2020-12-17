from commons.markettime import MarketTime
from commons.models.market_model import Asset, Price, Financial, pg_db, sq_db
from commons.backtest.portfolio import Portfolio
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import os
from commons.money import Money
from scipy.interpolate import interp1d
import numpy as np

pg_db.bind([Asset, Price, Financial])
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")


class Market:
    market_time = MarketTime()
    mt_tz = market_time.market_tz

    def __init__(self, start_date: datetime = None, end_date: datetime = None, asset_context: list = None, debug_mode=False):
        self.debug_mode = debug_mode
        self.start_date = start_date if start_date is not None else datetime(2015, 1, 1)
        self.end_date = end_date if end_date is not None else datetime.utcnow()

        if asset_context is None:
            self.assets = Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True)).order_by(Asset.symbol.asc())
        else:
            if not isinstance(asset_context, list):
                raise TypeError(f"asset_context must be a list. Got type {type(asset_context)}")
            self.assets = Asset.select().where(Asset.symbol << asset_context)
        self.traders = []
        self.prices = {}
        self.calendar = api.get_calendar(start=self.start_date.date().isoformat(), end=self.mt_tz.localize(self.end_date).date().isoformat())
        self.day_counter = 0
        self.tick_counter = 0
        self.total_tick = 0
        self._test_date_list = []
        self.update_day()
        self.get_today_prices()
        self.time_now = datetime.combine(self.date, self.open)
        self._daily_prices = {}

    def run_simulation(self):
        print("START SIMULATION")
        # RUN ONCE
        while True:
            self._test_date_list.append(self.time_now)
            for trader in self.traders:
                trader.update()
            self.total_tick += 1
            if not self.next_tick():
                break

        for trader in self.traders:
            trader.end_simulation()

    def next_day(self):
        self.day_counter += 1
        if self.day_counter < len(self.calendar):
            self.update_day()
            self.get_today_prices()
            return True
        else:
            return False

    def next_tick(self):
        if self.time_now == self.today_close - timedelta(minutes=1):
            if self.next_day():
                self.tick_counter = 0
            else:
                return False
        else:
            self.tick_counter += 1

        self.time_now = self.today_open + timedelta(minutes=self.tick_counter)
        return True

    def update_day(self):
        self.today = self.calendar[self.day_counter]
        self.date = self.today.date
        self.open = self.today.open
        self.close = self.today.close
        self.session_open = self.today.session_open
        self.session_close = self.today.session_close

        self.today_close = datetime.combine(self.date, self.close)
        self.today_open = datetime.combine(self.date, self.open)

    def get_today_prices(self):
        min_timestamp = self.today_open
        max_timestamp = self.today_close

        for asset in self.assets:
            self.prices[asset.symbol] = Price.select().where((Price.asset == asset) & (Price.time >= min_timestamp) & (Price.time <= max_timestamp))

        self._daily_prices = {}

    def register_portfolio(self, start_value, **kwargs):
        new_portfolio = Portfolio(start_value, self.start_date, self.end_date, **kwargs)
        self.traders.append(new_portfolio)

        return new_portfolio

    def get_current_price(self, symbol: str) -> Money:
        if symbol in self._daily_prices.keys():
            return Money(round(float(self._daily_prices[symbol](self.tick_counter)), 3))

        if symbol in self.prices.keys():
            if len(self.prices[symbol]) == 0:
                return None
        else:
            return None

        open_time = self.today_open
        close_time = self.today_close
        asset_price = [x for x in self.prices[symbol] if x.time >= open_time and x.time <= close_time]
        x_val = []
        y_val = []
        for i in range(len(asset_price)):
            current_time = asset_price[i].time
            current_close_price = asset_price[i].close
            time_delta = current_time - open_time
            minute_delta = time_delta.seconds // 60
            x_val.append(minute_delta)
            y_val.append(current_close_price)

        interp_func = interp1d(x_val, y_val, fill_value="extrapolate")
        self._daily_prices[symbol] = interp_func
        current_val = round(float(interp_func(self.tick_counter)), 3)

        return Money(current_val)
