from commons.models.market_model import Asset, Price, Financial, pg_db
from commons.backtest.indicators import SMAIndicator
from datetime import datetime
from commons.backtest import Scorer, Optimizer, Market

pg_db.bind([Asset, Price, Financial])

assets_symbol = [x.symbol for x in Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True))]
mt = Market(asset_context=assets_symbol, start_date=datetime(2020, 1, 1), end_date=datetime(2020, 1, 31), debug_mode=False)


class MAScorer(Scorer):

    def __init__(self):
        super().__init__()
        self.indicators = []
        for symbol in self.market.active_symbols[:10]:
            self.indicators.append(SMAIndicator(symbol, 30))

    def execute(self):
        '''
        Do some arbitary calculation on stock metrics and return scores of all possible stock in the market
        '''
        data = {}

        for indicator in self.indicators:
            cur_price = self.market.get_current_price(indicator.symbol)
            if cur_price is None:
                continue
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


class BasicOptimizer(Optimizer):

    def __init__(self):
        super().__init__()
        self.custom_data = "whatever"

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


mt.register_portfolio(100_000, scorer=MAScorer, optimizer=BasicOptimizer)

mt.run_simulation()
