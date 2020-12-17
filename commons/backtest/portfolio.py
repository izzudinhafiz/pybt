import inspect
from datetime import datetime, timedelta
from commons.helper import get_caller
from pprint import pprint
from commons.money import Money
from commons.backtest.position import Position


class Portfolio:
    def __init__(self, start_value: float = None, start_date: datetime = None, end_date: datetime = None):
        self.start_value = Money(start_value)
        self.cash = Money(start_value)
        self.equity = Money(0)
        self.open_positions = []
        self.closed_positions = []
        self.market = get_caller(inspect.stack()[1][0])
        self.start_date = start_date if start_date is not None else self.market.start_date
        self.end_date = end_date if end_date is not None else self.market.end_date
        self.margin = start_value
        self._to_remove = []
        self.nett_gain = Money(0)

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
            nett_cost = value + (value * Position.commission_rate)
            if self.cash < nett_cost:
                return False
        else:
            open_commission = value.abs() * Position.commission_rate
            if self.margin < value.abs() or self.cash < open_commission:
                return False

        return True

    def process_open(self, position):
        if position is None:
            return
        self.cash -= position.open_value + position.open_commission
        self.equity += position.current_value
        self.margin = self.cash + self.equity
        self.nett_gain = self.cash + self.equity - self.start_value
        self.open_positions.append(position)

    def process_close(self, position):
        self.cash += position.close_value - position.close_commission
        self.equity -= position.close_value
        self._to_remove.append(position)

    def update(self):
        total_value = Money(0)
        for position in self.open_positions:
            position.update()
            if position.active == True:
                total_value += position.current_value
            else:
                self.process_close(position)

        for index in reversed(range(len(self._to_remove))):
            self.closed_positions.append(self.open_positions.pop(index))
        self._to_remove = []
        self.equity = total_value
        self.margin = self.cash + self.equity
        self.nett_gain = self.cash + self.equity - self.start_value
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
