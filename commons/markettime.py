import datetime as dt
from pytz import timezone


class MarketTime:
    def __init__(self, tz="US/Eastern"):
        self.market_tz = timezone(tz)
        self.open_time = dt.time(9, 30)
        self.close_time = dt.time(16)
        self.local_tz = timezone("Asia/Kuala_Lumpur")

    def open(self, year, month, day):
        return self.market_tz.localize(dt.datetime(year, month, day, self.open_time.hour, self.open_time.minute)).isoformat()

    def close(self, year, month, day):
        return self.market_tz.localize(dt.datetime(year, month, day, self.close_time.hour, self.close_time.minute)).isoformat()
