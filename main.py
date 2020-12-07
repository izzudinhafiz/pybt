from commons.models.market_model import Asset, Price, sq_db, pg_db
import time
import datetime as dt
pg_db.bind([Asset, Price])

start = time.time()
aapl = Asset.get(Asset.symbol == "AAPL")

start = time.time()
prices = Price.select().where((Price.asset == aapl) & (Price.time >= dt.datetime(2020, 12, 1)) & (Price.time <= dt.datetime(2020, 12, 2)))
print(len(prices))
for price in prices:
    print(price.time)
print(f"{start-time.time()}")
