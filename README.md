# Better Backtester

A backtesting framework for stock trading algorithm with the following aim

- [x] Safe simulation (separation of market data and portfolio environment to minimize look ahead mistakes)
- [x] Fast simulation (500 indicators, 10,000 timestep (daily: 40 years, minute: 1.25 years) in 10 minutes)
- [ ] Multiple frequency ability (daily, 1minute, 5minute, 1hour etc.)
- [ ] Multiple strategy simulation at once
- [x] Simple to implement (remove complexity to setup for beginners. MINIMAL boilerplate codes)
- [x] Extensible implementation (allows more complex setup for more advanced users)
- [ ] Interactive preview of simulation data

## Usage

### Basic Usage

```python
from commons.backtest import Market

market = Market(asset_context=["AAPL", "GOOGL"])
```

You only need to supply Market with `asset_context` which is the list of assets that will be tradable in the market. (This should be a list of ticker symbols)

### Specifiying Start/End Date

```python
from datetime import datetime

market = Market(asset_context=["AAPL", "GOOGL"], start_date=datetime(2020, 1, 1), end_date=datetime(2020, 1, 31))
```

Additionally you can specificy a custom `start_date` and `end_date`.

If you do not, `start_date` defaults to an arbitary `datetime(2015, 1, 1)` and `end_date` will be today's date

### Creating a Portfolio

```python
market.register_portfolio(1000000)
```

Portfolios are the representation of a trader. They will contain the trading strategy and optimizer which you will manipulate to implement your own trading strategy

### Implementing Strategy

The minimum required implementation that allows you to create a strategy is to use the `Optimizer` object.

You then create a custom class that inherits from `Optimizer` and specify (at a minimum) an `execute` method which will **always** need `self` and `data` as arguments

`Optimizer` class has access to the `Portfolio` object by referencing `self.portfolio`.

`execute` method gets called for every timestep in the simulation

```python
from commons.backtest import Optimizer

class MyStrategy(Optimizer):
    def execute(self, data):
        # Do Something Here

market.register_portfolio(100000, optimizer=MyStrategy)
```

#### Coin Flipping Buy/Sell Strategy

```python
import random

class CoinFlipStrategy(Optimizer):

    def execute(self, data):
        for ticker in self.portfolio.asset_context:
            coin_flip = random.randint(0, 2) # If 0, we dont buy, if 1, we buy

            if coin_flip:
                self.portfolio.open_position_by_value(ticker, 100)
```

### Optimizers and Scorers

To minimize the risk of look ahead bias (as well as some data pipelining to speed up simulation), `Optimizer` classes have no access to market data. So to create a strategy based on market data, we need to implement a `Scorer` class.

- `Scorer` have access to market data but not portfolio
- `Optimizer` have access to portfolio data but not market data
- `Optimizer` can access return values from `Scorer` class by unpacking the `data` argument in the `execute` function

In summary, we create a `Scorer` class, do some calculation to decide on which stock to buy/sell and return that decision. `Optimizer` class can then access this return value and actually execute the trade (or not execute if for example, your portfolio exposure is too high etc.)

#### Moving Average Crossover Strategy

## TODO:

1. Allow different period for backtesting (eg, minute, 5minute, 1hour, daily)
2. Allow different data source loading

## Maybe TODO:

- Change how Indicators are implemented so we can do bulk updating of indicators (optimization issue)
