from commons.models.market_model import Asset, Price, Financial, pg_db, sq_db
from commons.markettime import MarketTime
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import os
import time

pg_db.bind([Asset, Price, Financial])
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")


class Market:
    market_time = MarketTime()
    mt_tz = market_time.market_tz

    def __init__(self, start_date: datetime = None, end_date: datetime = None, asset_context: list = None):
        if start_date is None:
            self.start_date = datetime(2015, 1, 1)
        else:
            self.start_date = start_date

        if end_date is None:
            self.end_date = datetime.utcnow()
        else:
            self.end_date = end_date

        if asset_context is None:
            self.assets = Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True)).order_by(Asset.symbol.asc())
        else:
            self.assets = Asset.select().where(Asset.symbol << asset_context)
        self.traders = []
        self.prices = {}
        self.calendar = api.get_calendar(start=self.start_date.date().isoformat(), end=self.mt_tz.localize(self.end_date).date().isoformat())
        self.day_counter = 0
        self.tick_counter = 0
        self.update_day()
        self.get_today_prices()
        self.time_now = datetime.combine(self.date, self.open)

    def run_simulation(self):
        print("START SIMULATION")
        # RUN ONCE
        while self.next_tick():
            for trader in self.traders:
                trader.update()

        for trader in self.traders:
            trader.end_simulation()

        print("END SIMULATION")

    def next_day(self):
        self.day_counter += 1
        if self.day_counter < len(self.calendar):
            self.update_day()
            # self.get_today_prices()
            return True
        else:
            return False

    def next_tick(self):
        if self.time_now > datetime.combine(self.date, self.close):
            if self.next_day():
                self.tick_counter = 0
            else:
                return False
        else:
            self.tick_counter += 1

        self.time_now = datetime.combine(self.date, self.open) + timedelta(minutes=self.tick_counter)
        return True

    def update_day(self):
        self.today = self.calendar[self.day_counter]
        self.date = self.today.date
        self.open = self.today.open
        self.close = self.today.close
        self.session_open = self.today.session_open
        self.session_close = self.today.session_close

    def get_today_prices(self):
        min_timestamp = datetime.combine(self.date, self.session_open).timestamp()
        max_timestamp = datetime.combine(self.date, self.session_close).timestamp()

        for asset in self.assets:
            self.prices[asset.symbol] = Price.select().where((Price.asset == asset) & (Price.time >= min_timestamp) & (Price.time <= max_timestamp))

    def register_portfolio(self, start_value, **kwargs):
        new_portfolio = Portfolio(self, start_value, self.start_date, self.end_date, **kwargs)
        self.traders.append(new_portfolio)

        return new_portfolio

    def get_current_price(self, symbol):
        try:
            prices = self.prices[symbol]
        except KeyError:
            return None

        if len(prices) == 0:
            return None

        current_time = self.time_now
        nearest_time = None
        nearest_index = None
        for index, price in enumerate(prices):
            if price.time == current_time:
                return price.open
            if nearest_time is None:
                nearest_time = price.time
                nearest_index = index
            elif abs(price.time - current_time) < abs(nearest_time - current_time):
                nearest_time = price.time
                nearest_index = index

        if nearest_time > current_time:
            if nearest_index != 0:
                prev_index = nearest_index - 1
                next_index = nearest_index
            else:
                return prices[0].open
        else:
            if nearest_index < len(prices) - 1:
                prev_index = nearest_index
                next_index = nearest_index + 1
            else:
                return prices[-1].close

        prev_price = prices[prev_index]
        next_price = prices[next_index]
        range_delta = (next_price.time - prev_price.time).seconds
        time_delta = (current_time - prev_price.time).seconds
        ratio = time_delta / range_delta
        price_delta = next_price.open - prev_price.close
        current_price = price_delta * ratio + prev_price.close
        return round(current_price, 2)


class Portfolio:

    def __init__(self, market: Market, start_value: float = None, start_date: datetime = None, end_date: datetime = None):
        self.cash = start_value
        self.asset = self.cash
        self.positions = []
        self.market = market

    def open_position_by_value(self, symbol, value):
        current_price = self.market.get_current_price(symbol)

    def open_position_by_volume(self, symbol, volume):
        pass

    def open_position_by_ratio(self, symbol, ratio):
        pass

    def update(self):
        pass

    def end_simulation(self):
        pass


assets_symbol = [x.symbol for x in Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True))]
mt = Market(asset_context=assets_symbol, end_date=datetime(2015, 1, 2))
mt.register_portfolio(100000)

for i in range(20):
    print(mt.time_now, mt.get_current_price("MMM"))
    mt.next_tick()
prices = mt.prices["MMM"][:5]

for price in prices:
    print(price.time, price.open, price.close)
# mt.run_simulation()
