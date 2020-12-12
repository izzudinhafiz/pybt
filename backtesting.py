from commons.models.market_model import Asset, Price, Financial, pg_db, sq_db
from commons.backtest import Market
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi
import os
import time
from pprint import pprint
pg_db.bind([Asset, Price, Financial])
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")


assets_symbol = [x.symbol for x in Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True))]
mt = Market(asset_context=assets_symbol, end_date=datetime(2015, 1, 2))
portfolio = mt.register_portfolio(100000)
portfolio.open_position_by_value("AAPL", 1000)

for i in range(5):
    for position in portfolio.positions:
        position.update()
        pprint((position.current_value, position.current_price))
    mt.next_tick()
