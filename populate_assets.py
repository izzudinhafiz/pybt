import os
import alpaca_trade_api as tradeapi
from commons.models.market_model import Asset, db
import json
import requests
SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")

api = tradeapi.REST(API_KEY, SECRET_KEY, base_url="https://paper-api.alpaca.markets")
account = api.get_account()

assets = api.list_assets()
sp500 = json.loads(requests.get("https://datahub.io/core/s-and-p-500-companies/r/constituents.json").content)
sp500_d = dict(zip((x["Symbol"] for x in sp500), (x["Sector"] for x in sp500)))

to_save = []
for asset in assets:
    to_save.append(Asset(_class=asset.__getattr__("class"),
                         easy_to_borrow=asset.easy_to_borrow,
                         exchange=asset.exchange,
                         uuid=asset.id,
                         marginable=asset.marginable,
                         name=asset.name,
                         shortable=asset.shortable,
                         status=asset.status,
                         symbol=asset.symbol,
                         tradable=asset.tradable))

with db.atomic():
    Asset.bulk_create(to_save, batch_size=999)

to_update = [x for x in Asset.select() if x.symbol in sp500_d.keys()]

for asset in to_update:
    asset.sp500 = True
    asset.sector = sp500_d[asset.symbol]

Asset.bulk_update(to_update, fields=[Asset.sp500, Asset.sector])
