import os
import alpaca_trade_api as tradeapi
from commons.models.market_model import Asset, Price, db
from commons.markettime import MarketTime
from datetime import datetime, timedelta
from peewee import chunked, DoesNotExist
import threading
import queue
import math
import time

SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")
account = api.get_account()
api_time_format = '%Y-%m-%dT%H:%M:%S-04:00'

asset_q = queue.Queue()
write_q = queue.Queue()
mt = MarketTime()
mt_tz = mt.market_tz
db_lock = threading.Lock()


def worker_db():
    while True:
        print(f"Write Queue Size: {write_q.qsize()}")
        try:
            data = write_q.get(block=False)
            with db.atomic():
                for batch in chunked(data, 999):
                    Price.insert_many(batch).execute()
            write_q.task_done()
        except queue.Empty:
            time.sleep(5)


def worker_start(worker_id):
    while True:
        asset, last_time = asset_q.get()
        print(f"{worker_id}: working on {asset.symbol}")
        price_dict = dict.fromkeys(["time", "open", "high", "low", "close", "volume"])
        to_save = []

        start_time = last_time
        n = 0

        while start_time > datetime(2015, 1, 1, tzinfo=mt_tz):
            cs_start = time.time()
            barset = api.get_barset(asset.symbol, "minute", limit=1000, end=start_time.isoformat())
            for price in barset[asset.symbol]:
                price_dict = {"time": price.t,
                              "open": price.o,
                              "close": price.c,
                              "low": price.l,
                              "high": price.h,
                              "volume": price.v,
                              "asset": asset}
                to_save.append(price_dict)

            if len(barset[asset.symbol]) != 0:
                last_timestamp = barset[asset.symbol][0].t

                start_time = last_timestamp.to_pydatetime() + timedelta(minutes=-1)
                n += 1
            else:
                break

            if n != 0 and n % 20 == 0:
                write_q.put(to_save[:])
                print(f"{worker_id}: {asset.symbol} | Placed in queue: {start_time}")
                to_save = []

            cycle_time = time.time() - cs_start
            if cycle_time < (60/100):
                time.sleep((60/100) - cycle_time)

        write_q.put(to_save[:])
        print(f"{worker_id}: Finished {asset.symbol}")
        asset_q.task_done()


def worker_start_end(worker_id):
    while True:
        asset, last_time = asset_q.get()
        print(f"{worker_id}: working on {asset.symbol}")
        price_dict = dict.fromkeys(["time", "open", "high", "low", "close", "volume"])
        to_save = []

        start_time = last_time
        end_time = start_time + timedelta(days=2, minutes=-1)
        n = 0

        while start_time < mt_tz.localize(datetime.utcnow()):
            cs_start = time.time()
            if n % 1 == 0:
                print(f"{worker_id}: {asset.symbol} | {start_time}")

            barset = api.get_barset(asset.symbol, "minute", limit=1000, start=start_time.isoformat(),  end=end_time.isoformat())
            for symbol, prices in barset.items():
                _a = Asset.get(Asset.symbol == symbol)
                for price in prices:
                    price_dict = {"time": price.t,
                                  "open": price.o,
                                  "close": price.c,
                                  "low": price.l,
                                  "high": price.h,
                                  "volume": price.v,
                                  "asset": _a}

                    to_save.append(price_dict)
            start_time = end_time + timedelta(minutes=1)
            end_time = start_time + timedelta(days=2, minutes=-1)
            n += 1

            if n != 0 and n % 100 == 0:
                write_q.put(to_save[:])
                print(f"{worker_id}: {asset.symbol} | Placed in queue: {start_time}")
                to_save = []

        print(f"{worker_id}: Finished {asset.symbol}")
        asset_q.task_done()


assets = Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True)).order_by(Asset.symbol.asc())


for asset in assets:
    try:
        last_price = Price.select().where(Price.asset == asset).order_by(Price.time.asc()).get()
        last_time = mt_tz.localize(last_price.time)
        last_time = last_time + timedelta(minutes=-1)
    except DoesNotExist:
        last_time = datetime.utcnow()

    time_delta = last_time - datetime(2015, 1, 2, 9, 30, tzinfo=mt_tz)
    if time_delta > timedelta(days=0.5):
        asset_q.put((asset, last_time))


threading.Thread(target=worker_db, daemon=True).start()
for i in range(2):
    threading.Thread(target=worker_start, args=(i,), daemon=True).start()


asset_q.join()
write_q.join()
print("All Done")
