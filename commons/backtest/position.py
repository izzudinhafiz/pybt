from commons.money import Money
from commons.helper import get_caller
import inspect
from datetime import datetime, timedelta


class Position:
    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.symbol = None
        self.size = None
        self.position_type = None
        self.active = None

        self.open_price = None
        self.open_value = None
        self.open_time = None
        self.open_commission = Money(0)

        self.current_value = None
        self.current_price = None

        self.close_value = None
        self.close_time = None
        self.close_price = None
        self.close_commission = Money(0)

        self.take_profit = None
        self.stop_loss = None

        self.nett_gain = None
        self.commission_rate = 0.01
        self.total_commission = self.open_commission + self.close_commission

    @classmethod
    def open_by_value(cls, symbol, value):
        if type(value) != Money:
            value = Money(value)
        position = cls(get_caller(inspect.stack()[1][0]))  # get_caller gets the portfolio object that called this position.
        market = position.portfolio.market
        current_price = market.get_current_price(symbol)
        if current_price is None:
            return None
        size = value / current_price
        position.open_position(symbol, size, current_price)

        return position

    def open_position(self, symbol: str, size: Money, open_price: Money):
        self.symbol = symbol
        self.size = size
        self.open_price = Money(open_price)
        self.current_price = Money(open_price)
        self.open_value = self.open_price * self.size
        self.current_value = self.current_price * self.size
        self.open_time = self.portfolio.market.time_now
        self.active = True
        self.position_type = "long" if size > 0 else "short"
        self.open_commission = Money(self.open_value * self.commission_rate)
        self.total_commission = self.open_commission
        self.calculate_nett_gain()

        return self.current_value

    def close_position(self):
        self.close_time = self.portfolio.market.time_now
        self.close_price = self.portfolio.market.get_current_price(self.symbol)
        self.current_price = self.close_price
        self.close_value = self.close_price * self.size
        self.close_commission = round(self.commission_rate * self.close_value, 2)
        self.total_commission = self.open_commission + self.close_commission
        self.active = False
        self.calculate_nett_gain()

        return (self.close_value, self.nett_gain)

    def calculate_nett_gain(self):
        if self.position_type == "long":
            gross_gain = self.current_value - self.open_value
            self.nett_gain = gross_gain - self.total_commission
        elif self.position_type == "short":
            gross_gain = self.open_value - self.current_value
            self.nett_gain = gross_gain - self.total_commission

    def update(self):
        if not self.active:
            return

        price = self.portfolio.market.get_current_price(self.symbol)
        if price is None:
            self.terminate_early()
            return

        self.current_price = price

        self.current_value = self.current_price * self.size
        self.calculate_nett_gain()

        return self.nett_gain

    def terminate_early(self):
        self.active = False
        print(f"{self.symbol} Opened on: {self.open_time} Terminated on {self.portfolio.market.time_now} due to insufficient price data")
