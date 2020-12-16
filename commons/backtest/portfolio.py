import inspect
from datetime import datetime, timedelta
from commons.helper import get_caller
from pprint import pprint
from commons.money import Money
from commons.backtest.position import Position


class Portfolio:
    def __init__(self, start_value: float = None, start_date: datetime = None, end_date: datetime = None):
        self.cash = Money(start_value)
        self.equity = Money(start_value)
        self.positions = []
        self.market = get_caller(inspect.stack()[1][0])
        self.start_date = start_date if start_date is not None else self.market.start_date
        self.end_date = end_date if end_date is not None else self.market.end_date
        self.margin = start_value

    def open_position_by_value(self, symbol, value):
        if self.can_open(value):
            self.process_open(Position.open_by_value(symbol, value))
            return True
        return False

    def open_position_by_size(self, symbol, size):
        current_price = self.market.get_current_price(symbol)
        buy_value = current_price * size
        if self.can_open(buy_value):
            self.process_open(Position.open_by_value(symbol, buy_value))
            return True
        return False

    def open_position_by_ratio(self, symbol, ratio):
        if ratio > 0:
            buy_value = self.cash * ratio
        elif ratio < 0:
            buy_value = self.margin * ratio
        else:
            return False
        if self.can_open(buy_value):
            self.process_open(Position.open_by_value(symbol, buy_value))
            return True
        return False

    def can_open(self, value):
        if type(value) != Money:
            value = Money(value)

        if value > 0:
            if self.cash < value:
                return False
        else:
            if self.margin < value:
                return False

        return True

    def process_open(self, position):
        if position is None:
            return

        if position.position_type == "long":
            self.cash -= position.open_value
            self.equity += position.nett_gain
        elif position.position_type == "short":
            self.cash += position.open_value
            self.equity += position.nett_gain
        else:
            raise AttributeError(f"Position type is {position.position_type}. Invalid type")
        self.positions.append(position)

    def process_close(self, position):
        pass

    def update(self):
        total_value = 0
        for position in self.positions:
            total_value += position.current_value

        self.equity = total_value
        self.score_stock()
        self.optimizer()
        self.execute()

    def optimizer(self):
        pass

    def score_stock(self):
        pass

    def execute(self):
        pass

    def end_simulation(self):
        pass
