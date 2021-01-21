from datetime import datetime, time, date
import alpaca_trade_api as tradeapi
from pytz import timezone
import pandas as pd


class Calendar:

    def __init__(self, _date: date, open: time, close: time, **kwargs):
        if not isinstance(_date, date):
            raise TypeError(f"date should be datetime.datetime object. Got type {type(_date)} instead")
        if not isinstance(open, time):
            raise TypeError(f"open should be datetime.time object. Got type {type(open)} instead")
        if not isinstance(close, time):
            raise TypeError(f"close should be datetime.time object. Got type {type(close)} instead")
        self.date: date = _date
        self.open: time = open
        self.close: time = close

        for key, value in kwargs.items():
            self.__dict__[key] = value


class CalendarData:

    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key: int) -> Calendar:
        return self.data[key]

    def __setitem__(self, key: int, value: Calendar):
        self.data[key] = value

    def __delitem__(self, key: int):
        del self.data[key]

    @classmethod
    def load_from_alpaca(cls, api_key: str, secret_key: str, base_url: str = "https://paper-api.alpaca.markets", start_date: datetime = datetime(2015, 1, 1), end_date: datetime = datetime.today(), tz: str = "US/Eastern"):
        api = tradeapi.REST(api_key, secret_key, base_url)
        market_tz = timezone(tz)
        start = market_tz.localize(start_date).date().isoformat()
        end = market_tz.localize(end_date).date().isoformat()
        calendar_data = api.get_calendar(start=start, end=end)

        # Convert Alpaca API reply to local Calendar object
        for i, cal in enumerate(calendar_data):
            _date = cal.date.to_pydatetime().date()
            open = cal.open
            close = cal.close
            new_cal = Calendar(_date, open, close)
            calendar_data[i] = new_cal

        return cls(calendar_data)

    @classmethod
    def load_from_pandas(cls, data):
        required_col = ["date", "open", "close"]
        cal_data = []
        for col in required_col:
            if col not in data.columns:
                raise ValueError(f"DataFrame should have ['date', 'open', 'close'] columns. Received {data.columns} instead")

        additional_col = [x for x in data.columns if x not in required_col]
        for idx, row in data.iterrows():
            if isinstance(row.date, (date, pd.Timestamp)):
                _date = row.date.to_pydatetime().date()
            else:
                raise TypeError(f"date value should either be datetime.date or pandas.Timestamp object. Got type {type(row.date)} instead")

            new_cal = Calendar(_date, row.open, row.close)
            for col in additional_col:
                new_cal.__setattr__(col, row[col])
            cal_data.append(new_cal)

        return cls(cal_data)


if __name__ == '__main__':
    import os
    SECRET_KEY = os.getenv("SECRET_KEY")
    API_KEY = os.getenv("API_KEY")
    # cal = CalendarData.load_from_alpaca(API_KEY, SECRET_KEY)
    cal_df = pd.read_excel("D:\ocr_ml\pandas_test_calendar.xlsx", parse_dates=True)
    cal = CalendarData.load_from_pandas(cal_df)

    print(cal[0].__dict__)
