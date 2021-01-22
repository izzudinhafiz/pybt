from peewee import *
import os

PG_USER = os.getenv("PG_USER")
PG_PW = os.getenv("PG_PW")

sq_db = SqliteDatabase("market.db", pragmas={"journal_mode": "wal",
                                             "synchronous": 0,
                                             "cache_size": -4000})

pg_db = PostgresqlDatabase("alpaca_market",
                           user=PG_USER,
                           password=PG_PW,
                           host="localhost",
                           port=5432)


class Asset(Model):
    _class = CharField(column_name="class")
    easy_to_borrow = BooleanField()
    exchange = CharField()
    uuid = UUIDField(unique=True)
    marginable = BooleanField()
    name = CharField(null=True)
    shortable = BooleanField()
    status = CharField()
    symbol = CharField()
    tradable = BooleanField()
    sp500 = BooleanField(default=False)
    sector = CharField(null=True)


class Financial(Model):
    asset = ForeignKeyField(Asset, backref="financials")
    dividend = FloatField()
    earnings = FloatField()
    ytd_h = FloatField()
    ytd_l = FloatField()
    market_cap = FloatField()
    ebitda = FloatField()


class Price(Model):
    asset = ForeignKeyField(Asset, backref="prices")
    open = FloatField()
    high = FloatField()
    low = FloatField()
    close = FloatField()
    volume = FloatField()
    time = TimestampField()

    class Meta:
        indexes = (
            (("asset", "time"), True),
        )


# sq_db.bind([Asset, Financial, Price])
# sq_db.create_tables([Asset, Financial, Price])
# pg_db.bind([Asset, Financial, Price])
# pg_db.create_tables([Asset, Financial, Price])
