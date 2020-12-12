from commons.models.market_model import Asset, Price, sq_db, pg_db
import time
import datetime as dt
import csv

pg_db.bind([Asset, Price])

start = time.time()
aapl = Asset.get(Asset.symbol == "AAPL")

start = time.time()
prices = Price.select().where((Price.asset == aapl) & (Price.time >= dt.datetime(2020, 12, 1)) & (Price.time <= dt.datetime(2020, 12, 4))).dicts()

headers = prices[0].keys()
with open("scenario_test.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    for price in prices:
        writer.writerow(price)
