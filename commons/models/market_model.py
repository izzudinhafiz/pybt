from peewee import *

db = SqliteDatabase("market.db", pragmas={"journal_mode": "wal",
                                          "synchronous": 0,
                                          "cache_size": -4000})


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

    class Meta:
        database = db


class Financial(Model):
    asset = ForeignKeyField(Asset, backref="financials")
    dividend = FloatField()
    earnings = FloatField()
    ytd_h = FloatField()
    ytd_l = FloatField()
    market_cap = FloatField()
    ebitda = FloatField()

    class Meta:
        database = db


class Price(Model):
    asset = ForeignKeyField(Asset, backref="prices")
    open = FloatField()
    high = FloatField()
    low = FloatField()
    close = FloatField()
    volume = FloatField()
    time = TimestampField()

    class Meta:
        database = db
        indexes = (
            (("asset", "time"), True),
        )


db.create_tables([Asset, Financial, Price])
print(db.journal_mode, db.cache_size)
