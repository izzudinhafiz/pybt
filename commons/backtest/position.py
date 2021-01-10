from commons.money import Money
from commons.helper import get_caller
import inspect
from datetime import datetime, timedelta
import warnings


class Position:
    commission_rate = 0.01

    def __init__(self, portfolio):
        self.portfolio = portfolio
        self.debug_mode = self.portfolio.debug_mode
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
        self.close_type = None      # Closing reason ie of type [incomplete_price, take_profit, stop_loss, manual_close]

        self.take_profit = None
        self.stop_loss = None

        self.gain = None
        self.total_commission = self.open_commission + self.close_commission

    @classmethod
    def open_by_value(cls, symbol, value, take_profit=None, stop_loss=None):
        if type(value) != Money:
            value = Money(value)
        position = cls(get_caller(inspect.stack()[1][0]))  # get_caller gets the portfolio object that called this position.
        market = position.portfolio.market
        current_price = market.get_current_price(symbol)
        if current_price is None:
            return None
        size = value / current_price
        is_open = position.open_position(symbol, size, current_price, take_profit, stop_loss)

        if is_open:
            return position
        else:
            return None

    def open_position(self, symbol: str, size: Money, open_price: Money, take_profit=None, stop_loss=None):
        if size == 0:
            return None

        self.symbol = symbol
        self.size = size
        self.open_price = open_price
        self.current_price = open_price
        self.open_value = self.open_price * self.size
        self.open_time = self.portfolio.market.time_now
        self.active = True
        self.position_type = "long" if size > 0 else "short"
        self.open_commission = self.open_value.abs() * self.commission_rate
        self.total_commission = self.open_commission
        self.current_value = self.current_price * self.size
        self.gain = self.current_value - self.open_value
        self.process_tp_sl(take_profit, stop_loss)

        if self.debug_mode:
            print(f"[{self.open_time}][{self.symbol}] {self.position_type} position opened. Price: {self.open_price} TP: {self.take_profit} SL: {self.stop_loss}")

        return self

    def close_position(self, close_type=None):
        self.close_time = self.portfolio.market.time_now
        self.close_price = self.portfolio.market.get_current_price(self.symbol)
        self.current_price = self.close_price if self.close_price else self.current_price  # Handles incomplete_price scenario
        self.current_value = self.current_price * self.size
        self.close_commission = Money(self.commission_rate * self.current_value).abs()
        self.total_commission = self.open_commission + self.close_commission
        self.close_value = self.current_value
        self.gain = self.current_value - self.open_value
        self.active = False

        if close_type is None:
            self.close_type = "manual_close"
        else:
            self.close_type = close_type

        if self.debug_mode >= 1:
            print(f"[{self.close_time}][{self.symbol}][{self.close_type}] position closed. Price {self.close_price} Nett Gain {self.gain - self.total_commission}")
        return self

    def process_tp_sl(self, take_profit, stop_loss):
        if isinstance(take_profit, (int, float, Money)):
            self.take_profit = take_profit if isinstance(take_profit, Money) else Money(take_profit)
        elif isinstance(take_profit, tuple):
            if take_profit[0] == "percent":
                if take_profit[1] < 1:
                    raise ValueError(f"take_profit percentage mode requires value greater than 1")
                if self.position_type == "long":
                    profit_level = self.open_price * take_profit[1]
                else:
                    profit_level = self.open_price - self.open_price * (take_profit[1] - 1)
                self.take_profit = profit_level
            else:
                raise ValueError(f"{take_profit[0]} unsupported. take_profit only supports 'percent' mode")
        else:
            self.take_profit = None

        if isinstance(stop_loss, (int, float, Money)):
            self.stop_loss = stop_loss if isinstance(stop_loss, Money) else Money(stop_loss)
        elif isinstance(stop_loss, tuple):
            if stop_loss[0] == "percent":
                if stop_loss[1] > 1:
                    raise ValueError(f"stop_loss percentage mode requires value less than 1")
                if self.position_type == "long":
                    loss_level = self.open_price * stop_loss[1]
                else:
                    loss_level = self.open_price - self.open_price * (stop_loss[1] - 1)
                self.stop_loss = loss_level
            else:
                raise ValueError(f"{stop_loss[0]} unsupported. stop_loss only supports 'percent' mode")
        else:
            self.stop_loss = None

    def update(self):
        if not self.active:
            return

        price = self.portfolio.market.get_current_price(self.symbol)
        if price is None:
            self.terminate_early()
            return

        self.current_price = price
        should_close = self.should_close()
        if should_close:
            return self.close_position(should_close)

        self.current_value = self.current_price * self.size
        self.gain = self.current_value - self.open_value

        return self.gain

    def terminate_early(self):
        warnings.warn(f"{self.symbol} Opened on: {self.open_time} Terminated on {self.portfolio.market.time_now} due to insufficient price data")
        return self.close_position("incomplete_price")

    def should_close(self):
        if self.take_profit is not None:
            if self.position_type == "long":
                if self.current_price >= self.take_profit:
                    return "take_profit"
            else:
                if self.current_price <= self.take_profit:
                    return "take_profit"

        if self.stop_loss is not None:
            if self.position_type == "long":
                if self.current_price <= self.stop_loss:
                    return "stop_loss"
            else:
                if self.current_price >= self.stop_loss:
                    return "stop_loss"

        return False
