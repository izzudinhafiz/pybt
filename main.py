import os
import alpaca_trade_api as tradeapi
from commons.models.market_model import Asset, Price, db
from datetime import datetime, timedelta
import pandas as pd
from commons.markettime import MarketTime
import sys
from peewee import chunked
import threading
import math
import time

lock = threading.Lock()


def worker(w_id):
    for i in range(3):
        with lock:
            print(f"{w_id}: Got Lock")
            time.sleep(1)
            print(f"{w_id}: Releasing Lock")


for n in range(5):
    threading.Thread(target=worker, args=(n,)).start()
