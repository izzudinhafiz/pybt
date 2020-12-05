from commons.models.market_model import Asset, Price, Financial, db
from commons.markettime import MarketTime
from datetime import datetime
import alpaca_trade_api as tradeapi
import os


SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")


class Market:
    market_time = MarketTime()
    mt_tz = market_time.market_tz

    def __init__(self, start_date: datetime = None, asset_context: list = None):
        if start_date is None:
            start_date = datetime(2015, 1, 1)

        if asset_context is None:
            self.assets = Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True)).order_by(Asset.symbol.asc())
        else:
            self.assets = Asset.select().where(Asset.symbol << asset_context)

        self.calendar = api.get_calendar(start=start_date.date().isoformat(), end=self.mt_tz.localize(datetime.utcnow()).date().isoformat())
        self.counter = 0
        self.update_day()
        self.get_today_price()

    def next_day(self):
        self.counter += 1

    def update_day(self):
        self.today = self.calendar[self.counter]
        self.date = self.today.date
        self.open = self.today.open
        self.close = self.today.close
        self.session_open = self.today.session_open
        self.session_close = self.today.session_close

    def get_today_price(self):
        min_timestamp = datetime.combine(self.date, self.session_open).timestamp()
        max_timestamp = datetime.combine(self.date, self.session_close).timestamp()
        self.prices = Price.select().where((Price.asset << self.assets) & (Price.time >= min_timestamp) & (Price.time <= max_timestamp)).execute()


mt = Market(asset_context=["AAPL"])

for price in mt.prices:
    print(price.open)
