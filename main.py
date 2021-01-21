from commons.backtest.datapack import PriceDataPack
import os
import pandas as pd
from datetime import datetime

dp = PriceDataPack.load_cache("cached_test")
print(dp.meta.source)

print(dp.get_price("AAPL", datetime(2021, 1, 7, 9, 30)))
# print(dp.symbols)

# pkl_files = os.listdir("pickled_price_data")

# dfs = {}

# for file in pkl_files:
#     file_path = os.path.join("pickled_price_data", file)
#     symbol = file[:-4]
#     df = pd.read_pickle(file_path)
#     df = df[["open", "high", "low", "close", "volume", "time"]]
#     df.set_index("time", inplace=True)
#     df.sort_index(inplace=True)
#     dfs[symbol] = df

# dp = PriceDataPack.load_pandas(dfs)

# dp.create_cache("cached_test", overwrite=True)
