from pybt.indicators import SMAIndicator
from pybt.datapack import PriceDataPack
from pybt import Scorer, Optimizer, Market
from datetime import datetime
import os

# Alpaca API Information
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")

# Loading data for simulation
datapack = PriceDataPack.load_cache("dp-test.pkl")

# Getting available symbols from our datapack
assets_symbol = datapack.symbols

# Setting up our simulation context
market = Market(asset_context=assets_symbol, start_date=datetime(2020, 1, 1), end_date=datetime(2020, 1, 31), debug_mode=True)
market.load_calendar_data("alpaca", api_key=API_KEY, secret_key=SECRET_KEY)  # Gets the trading calendar from Alpaca
market.load_price_data(datapack)    # Loads our datapack into the simulation


class MAScorer(Scorer):
    # Scoring object. This runs calculation on market prices

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
                print("ERROR")
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
    # Optimizer/Strategy object. This runs decisions based on the output of our Scorer

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


# Lets register a trader/portfolio to the market. We can register multiple portfolios
market.register_portfolio(100_000, scorer=MAScorer, optimizer=BasicOptimizer)

# Run's the simulation
market.run_simulation()
