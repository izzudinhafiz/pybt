from commons.models.market_model import Asset, Price, Financial, pg_db
from commons.backtest import Market
from datetime import datetime
from commons.money import Money
import talib
import numpy as np
pg_db.bind([Asset, Price, Financial])

assets_symbol = [x.symbol for x in Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True))]
mt = Market(asset_context=assets_symbol, start_date=datetime(2020, 1, 1), end_date=datetime(2020, 1, 31), debug_mode=1)


class Indicator:
    def __init__(self, symbol, duration=None):
        self.symbol = symbol
        self.duration = duration


class MAIndicator(Indicator):
    def __init__(self, symbol, duration):
        super().__init__(symbol, duration)
        self.data = []

    def update(self, current_price):
        if len(self.data) >= self.duration:
            self.data.pop(0)
        self.data.append(current_price.cents/100)

        if len(self.data) == self.duration:
            return Money(talib.SMA(np.asarray(self.data))[-1])
        else:
            return None


class Scorer:

    def __init__(self, portfolio, market):
        self.portfolio = portfolio
        self.market = market
        self.indicators = []
        self.indicators.append(MAIndicator("AAPL", 30))
        self.indicators.append(MAIndicator("GOOGL", 30))

    def execute(self):
        '''
        Do some arbitary calculation on stock metrics and return scores of all possible stock in the market
        '''
        data = {}

        for indicator in self.indicators:
            cur_price = self.market.get_current_price(indicator.symbol)
            average = indicator.update(cur_price)
            if average is None:
                continue

            price_delta = cur_price - average
            price_change = price_delta / average

            if price_change > 0.01:
                data[indicator.symbol] = -1
            elif price_change < -0.01:
                data[indicator.symbol] = 1

        return data


class Optimizer:

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def execute(self, data):
        '''
        Analyze scores and current portfolio positions and return decision to be made
        '''

        for symbol, decision in data.items():
            pos_type = "long" if decision == 1 else "short"
            open_positions = self.portfolio.get_positions(symbol)
            if open_positions:
                for position in open_positions:
                    if position.position_type != pos_type:
                        position.close_position()
            else:
                self.portfolio.open_position_by_value(symbol, 1000)


mt.register_portfolio(100_000, scorer=Scorer, optimizer=Optimizer)

mt.run_simulation()
