import os
import alpaca_trade_api as tradeapi
from commons.models.market_model import Asset, Price, db
from commons.markettime import MarketTime
from datetime import datetime, timedelta
from peewee import chunked, DoesNotExist
import threading
import queue
import time

SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
CALL_LIMIT = 200
API_WORKER = 2
cycle_time_limit = 60/(CALL_LIMIT/API_WORKER)

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")
account = api.get_account()

asset_q = queue.Queue()
write_q = queue.Queue()
mt = MarketTime()
mt_tz = mt.market_tz


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


def worker_api(worker_id):
    while True:
        asset, start, end = asset_q.get()
        print(f"{worker_id}: working on {asset.symbol} : {start.isoformat()} -> {end.isoformat()} Remaining: {asset_q.qsize()}")
        price_dict = dict.fromkeys(["time", "open", "high", "low", "close", "volume"])
        to_save = []

        cs_start = time.time()
        barset = api.get_barset(asset.symbol, "minute", limit=1000, start=start.isoformat(), end=end.isoformat())
        for price in barset[asset.symbol]:
            price_dict = {"time": price.t,
                          "open": price.o,
                          "close": price.c,
                          "low": price.l,
                          "high": price.h,
                          "volume": price.v,
                          "asset": asset}
            to_save.append(price_dict)

        write_q.put(to_save[:])

        cycle_time = time.time() - cs_start
        if cycle_time < cycle_time_limit:
            time.sleep(cycle_time_limit - cycle_time)

        asset_q.task_done()


assets = Asset.select().where((Asset.sp500 == True) & (Asset.tradable == True)).order_by(Asset.symbol.asc())

market_time = datetime.utcnow().astimezone(mt_tz)
market_date = market_time.date()
asset_datetime = []

for asset in assets:
    try:
        last_price = Price.select().where(Price.asset == asset).order_by(Price.time.desc()).get()
        last_datetime = mt_tz.localize(last_price.time)
    except DoesNotExist:
        print(f"{asset.symbol} DOES NOT EXIST")
        continue

    asset_datetime.append((asset, last_datetime))

earliest_dt = sorted([x[1] for x in asset_datetime])[0]
market_calendar = api.get_calendar(start=earliest_dt.date().isoformat(), end=market_date.isoformat())

for asset, last_datetime in asset_datetime:
    last_date = last_datetime.date()
    last_calendar = [x for x in market_calendar if x.date == last_date][0]

    if last_calendar.date.date() == last_date:
        # Check if last time within 5 minutes of market close
        close_time = last_calendar.close
        close_datetime = mt_tz.localize(datetime.combine(last_calendar.date.date(), close_time))
        time_delta = close_datetime - last_datetime
        if time_delta > timedelta(minutes=5):
            # need to update until market close of the last timestamp date
            print("Partial Finish", asset, last_datetime, close_datetime)
            asset_q.put((asset, last_datetime + timedelta(minutes=1), close_datetime))

    # Update until today's market
    next_start = last_date + timedelta(days=1)
    next_end = market_date
    current_calendar = [x for x in market_calendar if x.date >= next_start and x.date <= next_end]

    for cal in current_calendar:
        if cal.date <= market_date:
            _start = mt_tz.localize(datetime.combine(cal.date, cal.session_open))
            _close = mt_tz.localize(datetime.combine(cal.date, cal.session_close))
            asset_q.put((asset, _start, _close))

threading.Thread(target=worker_db, daemon=True).start()
for i in range(API_WORKER):
    threading.Thread(target=worker_api, args=(i,), daemon=True).start()

asset_q.join()
write_q.join()
print("All Done")
