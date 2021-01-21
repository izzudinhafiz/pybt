from commons.markettime import MarketTime
from commons.models.market_model import Asset, Price, Financial, pg_db, sq_db
from commons.backtest.portfolio import Portfolio
from commons.backtest.datapack import CalendarData, Calendar, PriceDataPack, PriceData
from datetime import datetime, timedelta, date, time
import alpaca_trade_api as tradeapi
import os
from commons.money import Money
from scipy.interpolate import interp1d
import numpy as np
import pandas as pd
from commons.helper import timer
pg_db.bind([Asset, Price, Financial])
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")


class Market:
    market_time = MarketTime()
    mt_tz = market_time.market_tz

    def __init__(self, asset_context: list[str], frequency: str = "1minute", start_date: datetime = None, end_date: datetime = None,  debug_mode: bool = False, test_mode: bool = False):
        self.debug_mode = debug_mode
        self.frequency = frequency
        self.start_date = start_date if start_date is not None else datetime(2015, 1, 1)
        self.end_date = end_date if end_date is not None else datetime.utcnow()
        self.test_mode = test_mode
        self.traders = []
        self.prices: dict[str, PriceData] = {}
        self._daily_prices = {}

        # Timing Context
        self.day_counter = 0
        self.tick_counter = 0
        self.total_tick = 0

        # Frequency Context
        if self.frequency == "1minute":
            self.next_tick = self._minute_next_tick
        elif self.frequency == "1hour":
            self.next_tick = self._hour_next_tick
        elif self.frequency == "daily":
            self.next_tick = self._daily_next_tick
        else:
            raise ValueError(f"{self.frequency} invalid. Frequency should be '1minute', '1hour' or 'daily'")

        if self.test_mode:
            self._test_date_list = []

        # Data Context
        # TODO: This needs to be generalized to accept different data source
        self.assets = asset_context
        # self.assets = Asset.select().where(Asset.symbol << asset_context)
        self.active_symbols = self.assets

        self.calendar = None
        self.time_now = None
        self.datapack: PriceDataPack = None
        self.get_today_prices: function = None

        self._fully_initialized = False

    def load_calendar_data(self, source: str, **kwargs):
        if source == "alpaca":
            api_key = kwargs.get("api_key", None)
            secret_key = kwargs.get("secret_key", None)
            start_date = kwargs.get("start_date", self.start_date)
            end_date = kwargs.get("end_date", self.end_date)

            self.calendar = CalendarData.load_from_alpaca(api_key, secret_key, start_date=start_date, end_date=end_date)
        elif source == "dataframe":
            data = kwargs.get("data", None)
            if not isinstance(data, pd.DataFrame):
                raise TypeError(f"df should be type pandas.DataFrame. Got {type(data)} instead")
            self.calendar = CalendarData.load_from_pandas(data)
        else:
            raise ValueError(f"source should be 'alpaca' or 'pandas'. Got '{source}' instead")

        self._update_day()

        self.time_now = datetime.combine(self.date, self.open)
        self._fully_initialized = True

    def load_price_data(self, source: PriceDataPack):
        self.datapack = source
        self.get_today_prices = self._get_today_prices_dp
        self.get_today_prices()
        self._fully_initialized = True

    @timer
    def run_simulation(self):
        if not self._fully_initialized:
            raise RuntimeError(f"Incomplete initialization. Must load calendar data and price data first")
        print("START SIMULATION")
        # RUN ONCE
        while True:
            if self.test_mode:
                self._test_date_list.append(self.time_now)
            for trader in self.traders:
                trader.update()
            self.total_tick += 1
            if not self.next_tick():
                break

        for trader in self.traders:
            trader.end_simulation()
        print("SIMULATION ENDED")

    def _next_day(self):
        self.day_counter += 1
        if self.day_counter < len(self.calendar):
            self._update_day()
            self.get_today_prices()
            return True
        else:
            return False

    def _hour_next_tick(self):
        raise NotImplementedError("Hourly simulation has not been implemented yet")

    def _daily_next_tick(self):
        pass

    def _minute_next_tick(self):
        if self.time_now == self.today_close - timedelta(minutes=1):
            if self._next_day():
                self.tick_counter = 0
            else:
                return False
        else:
            self.tick_counter += 1

        self.time_now = self.today_open + timedelta(minutes=self.tick_counter)
        return True

    def _update_day(self):
        self.today: Calendar = self.calendar[self.day_counter]
        self.date: date = self.today.date
        self.open: time = self.today.open
        self.close: time = self.today.close

        self.today_close = datetime.combine(self.date, self.close)
        self.today_open = datetime.combine(self.date, self.open)

    def _get_today_prices_db(self):
        min_timestamp = self.today_open
        max_timestamp = self.today_close

        for asset in self.assets:
            # self.prices[asset] = None
            self.prices[asset.symbol] = Price.select().where((Price.asset == asset) & (Price.time >= min_timestamp) & (Price.time <= max_timestamp))

        self._daily_prices = {}

    def _get_today_prices_dp(self):
        # This method calls Datapack's load_day_prices(date) which asks the datapack to
        # actually load the data into memory (or whatever). Making it available to calls for
        # get_price(datetime)
        for symbol in self.assets:
            self.prices[symbol] = self.datapack.get_prices(symbol, self.today.date)

        self._daily_prices = {}

    # DB mode
    def _get_current_price(self, symbol: str) -> Money:
        # Check if we have saved data for the pricing
        # _daily_prices gets cleared by get_today_prices function
        if symbol in self._daily_prices.keys():
            interp_func, latest_tick_data = self._daily_prices[symbol]
            tick_counter, price = latest_tick_data

            # Check if we have the current price already calculated
            if self.tick_counter == tick_counter:
                return price

            # We dont have the latest tick data, so we calculate it based on the interp function
            current_val = Money(round(float(interp_func(self.tick_counter)), 3))

            # We save that calculated value so we dont have to recalc if we get asked again
            self._daily_prices[symbol] = (interp_func, (self.tick_counter, current_val))

            return current_val

        # Some sanity checks to make sure we have some price data
        if symbol not in self.prices.keys():
            return None
            # if len(self.prices[symbol]) == 0:
            # return None
        # else:
            # return None
        try:
            # If we get here, we need to create an interp function before returning the current price
            # We save that interp function so we dont have to recreate it again for that day
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
            current_val = round(float(interp_func(self.tick_counter)), 3)
            current_val = Money(current_val)
            self._daily_prices[symbol] = (interp_func, (self.total_tick, current_val))

            return current_val
        except ValueError as e:
            del self.prices[symbol]
            print(e)
            return None

    # DP Mode
    def get_current_price(self, symbol: str) -> Money:
        # Check if we have saved data for the pricing
        # _daily_prices gets cleared by get_today_prices function
        if symbol in self._daily_prices.keys():
            interp_func, latest_tick_data = self._daily_prices[symbol]
            tick_counter, price = latest_tick_data

            # Check if we have the current price already calculated
            if self.tick_counter == tick_counter:
                return price

            # We dont have the latest tick data, so we calculate it based on the interp function
            current_val = Money(round(float(interp_func(self.tick_counter)), 3))

            # We save that calculated value so we dont have to recalc if we get asked again
            self._daily_prices[symbol] = (interp_func, (self.tick_counter, current_val))

            return current_val

        # Some sanity checks to make sure we have some price data
        if symbol not in self.prices.keys():
            return None
        try:
            # If we get here, we need to create an interp function before returning the current price
            # We save that interp function so we dont have to recreate it again for that day
            open_time = self.today_open
            close_time = self.today_close
            df = self.prices[symbol]
            asset_price = df.loc[open_time: close_time]
            y_val = list(asset_price["close"])
            x_val = list((asset_price.index - open_time).total_seconds()//60)
            x_val = [int(x) for x in x_val]
            interp_func = interp1d(x_val, y_val, fill_value="extrapolate")
            current_val = round(float(interp_func(self.tick_counter)), 3)
            current_val = Money(current_val)
            self._daily_prices[symbol] = (interp_func, (self.tick_counter, current_val))

            return current_val
        except ValueError as e:
            del self.prices[symbol]
            print(e)
            return None
        except AttributeError as e:
            del self.prices[symbol]
            print(e)
            return None

    def register_portfolio(self, start_value, **kwargs):
        new_portfolio = Portfolio(start_value, self.start_date, self.end_date, **kwargs)
        self.traders.append(new_portfolio)

        return new_portfolio
