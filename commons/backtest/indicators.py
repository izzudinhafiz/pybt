from commons import Money
import numpy as np
from collections import deque
import talib


class BaseIndicator:
    def __init__(self, symbol):
        self.symbol = symbol
        self.data = None


class SMAIndicator(BaseIndicator):
    def __init__(self, symbol, duration, length=30):
        super().__init__(symbol)
        self.data = deque([None for _ in range(30)])
        self.duration = duration
        self.history = deque([])
        self.length = length

    def update(self, current_price):
        if len(self.history) >= self.duration:
            self.history.popleft()
        self.history.append(current_price.cents/100)

        if len(self.history) == self.duration:
            new_avg = Money(talib.SMA(np.asarray(self.history))[-1])
            self.data.popleft()
            self.data.append(new_avg)

            return new_avg
        else:
            return None
