# Better Backtester

A backtesting framework for stock trading algorithm with the following aim

- [x] Safe simulation (separation of market data and portfolio environment to minimize look ahead mistakes)
- [x] Fast simulation (500 indicators, 10,000 timestep (daily: 40 years, minute: 1.25 years) in 10 minutes)
- [ ] Multiple frequency ability (daily, 1minute, 5minute, 1hour etc.)
- [ ] Multiple strategy simulation at once
- [x] Simple to implement (remove complexity to setup for beginners. MINIMAL boilerplate codes)
- [x] Extensible implementation (allows more complex setup for more advanced users)
- [ ] Interactive preview of simulation data

# Usage

## Basic Usage

```python
from pybt import Market

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

## Loading Data

Currently supported data sources are:

- Pandas DataFrames
- Cached DataPack (which can be created from Pandas DataFrames)

### Loading Pandas DataFrames

The DataFrames must contain an Index of `datetime[n64]` type (which is the default Pandas timestamp type) and columns of [Open, Low, High, Close, Volume] data. All column dtype should be `float64`. Type enforcement for data columns is not strict, but this may lead to low performance during the simulation.

**Example DataFrame**

|                     |  Open  | High  |  Low  | Close | Volume |
| :-----------------: | :----: | :---: | :---: | :---: | :----: |
| 2021-01-07 09:30:00 | 123.45 | 125.7 | 123.2 | 124.5 | 1470.0 |
| 2021-01-07 09:31:00 | 124.5  | 129.3 | 124.8 | 127.5 | 1321.0 |
| 2021-01-07 09:32:00 | 127.5  | 130.5 | 127.6 | 130.1 | 1899.0 |
|         ...         |  ...   |  ...  |  ...  |  ...  |  ...   |

**Structuring Multiple DataFrames**

Most use cases would require multiple symbols of price data to be loaded for simulation. This can be achieved by creating a `dict[symbol, dataframe]` that has the symbols as the key and that symbol's DataFrame as the value.

**Actually Loading Data**

DataFrames must be loaded into the `PriceDataPack` object. This object presents a common interface for the `Market` object to interact with. This can be done by calling the object's classmethod `.load_pandas` as below.

```python
from pybt.datapack import PriceDataPack

aapl_df = pd.read_csv("appl.txt")
goog_df = pd.read_csv("goog.txt")

data = {}
data["AAPL"] = aapl_df
data["GOOG"] = goog_df

datapack = PriceDataPack.load_pandas(data)
```

**Creating a Cached Data Pack**

It is best to not use Pandas when loading massive datasets into the simulation. This is because, the data from Pandas must be held in memory and can cause the OS to start paging files. Additionally, there is a significant initial load time when reading a DataFrame source (ie calls to `pd.read_csv`) for hundreds of symbols. If however, the dataset is small, it is possible to keep using Pandas entirely.

We can address this by using the cached version of the data pack. We create it once, and can keep reloading it as necessary with very high performance.

```python
from pybt.datapack import PriceDataPack

aapl_df = pd.read_csv("appl.txt")
goog_df = pd.read_csv("goog.txt")

data = {}
data["AAPL"] = aapl_df
data["GOOG"] = goog_df

datapack = PriceDataPack.load_pandas(data)  # We load intial data once
datapack.create_cache("test_cache_1")       # Creates an efficient HDF5 Store cache

datapack = PriceDataPack.load_cache("test_cache_1") # Future simulation can use this cache
```

## Creating a Portfolio

```python
market.register_portfolio(1000000)
```

Portfolios are the representation of a trader. They will contain the trading strategy and optimizer which you will manipulate to implement your own trading strategy

## Implementing Strategy

The minimum required implementation that allows you to create a strategy is to use the `Optimizer` object.

You then create a custom class that inherits from `Optimizer` and specify (at a minimum) an `execute` method which will **always** need `self` and `data` as arguments

`Optimizer` class has access to the `Portfolio` object by referencing `self.portfolio`.

`execute` method gets called for every timestep in the simulation

```python
from pybt import Optimizer

class MyStrategy(Optimizer):
    def execute(self, data):
        # Do Something Here

market.register_portfolio(100000, optimizer=MyStrategy)
```

### Coin Flipping Buy/Sell Strategy

```python
import random

class CoinFlipStrategy(Optimizer):

    def execute(self, data):
        for ticker in self.portfolio.asset_context:
            coin_flip = random.randint(0, 2) # If 0, we dont buy, if 1, we buy

            if coin_flip:
                self.portfolio.open_position_by_value(ticker, 100)
```

## Optimizers and Scorers

To minimize the risk of look ahead bias (as well as some data pipelining to speed up simulation), `Optimizer` classes have no access to market data. So to create a strategy based on market data, we need to implement a `Scorer` class.

- `Scorer` have access to market data but not portfolio
- `Optimizer` have access to portfolio data but not market data
- `Optimizer` can access return values from `Scorer` class by unpacking the `data` argument in the `execute` function

In summary, we create a `Scorer` class, do some calculation to decide on which stock to buy/sell and return that decision. `Optimizer` class can then access this return value and actually execute the trade (or not execute if for example, your portfolio exposure is too high etc.)

### Moving Average Crossover Strategy

## TODO:

1. Allow different period for backtesting (eg, minute, 5minute, 1hour, daily)

## Maybe TODO:

- Change how Indicators are implemented so we can do bulk updating of indicators (optimization issue)
