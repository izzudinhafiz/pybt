from commons.models.market_model import Asset, Price, Financial, pg_db, sq_db
from commons.backtest import Market
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import os
import time
from pprint import pprint
import random
pg_db.bind([Asset, Price, Financial])
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")


assets_symbol = [x.symbol for x in Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True))]
mt = Market(asset_context=assets_symbol, end_date=datetime(2015, 1, 30))
portfolio = mt.register_portfolio(1000*1000)


for i in range(100):
    portfolio.open_position_by_value(assets_symbol[i], 1000)

start_time = time.time()

LOOP_COUNT = 100
for i in range(LOOP_COUNT):
    for position in portfolio.positions:
        position.update()
    mt.next_tick()

elapsed = time.time() - start_time
print(f"Total time: {elapsed:.2f} s | Avg Time/Loop: {(elapsed / LOOP_COUNT) *1000:.2f} ms | Avg Time/Loop/Position: {(elapsed / LOOP_COUNT / len(portfolio.positions)) * 1000 * 1000:.0f} µs ")
