import os
import pickle
import warnings
import pandas as pd
from typing import Optional
import datetime as dt
from pybt.datapack.metadata import DataPackMetaData

DEBUG = False


class PriceData:
    def __init__(self, symbol: str, source_type: str, **kwargs):
        self.symbol = symbol
        self.price_data = {}
        self.source = None
        self.source_type = source_type
        self.active_data: pd.DataFrame = None
        self.active_date: dt.date = None

        if self.source_type == "pandas-hdf5":
            if kwargs.get("data_generator", None) is not None:
                self.source = kwargs["data_generator"]
                self._load_price = self._hdf_load
                if not isinstance(self.source, pd.HDFStore):
                    raise TypeError(f"Pandas HDF5 source requires a pandas.HDFStore generator. Got {type(self.source)} instead")
            else:
                raise AttributeError(f"Pandas HDF5 source requires a data_generator argument to initialize")

        elif self.source_type == "pandas":
            self._load_price = self._pd_load

            if kwargs.get("df", None) is not None:
                if not isinstance(kwargs["df"], pd.DataFrame):
                    raise TypeError(f"Pandas source requires a pandas.DataFrame source. Got {type(self.source)} instead")
            else:
                raise AttributeError(f"Pandas source requires a df argument to initialize")

            self._raw = kwargs["df"]
            self.source = self._raw.groupby(pd.Grouper(freq="D"))
        else:
            raise NotImplementedError(f"{source_type} is not implemented. Supported sources are [pandas-hdf5, pandas]")

    def get_price(self, datetime: dt.datetime) -> pd.Series:

        date = datetime.date()

        # Check if we have date data in memory. if not we load into memory and essentially offload old data
        if not self.active_date == date:
            if DEBUG:
                print(f"{type(self).__name__} {self.symbol} Loading Data")
            self._load_price(date)
        try:
            return self.active_data.loc[datetime]
        except KeyError:
            return None

    def get_prices(self, date: dt.date) -> pd.DataFrame:
        if not self.active_date == date:
            if DEBUG:
                print(f"{type(self).__name__} {self.symbol} Loading Data")
            self._load_price(date)

        return self.active_data

    def _pd_load(self, date: dt.date):
        self.active_data = self.source.get_group(date)
        self.active_data.sort_index(inplace=True)
        self.active_date = date

    def _hdf_load(self, date: dt.date):
        """Lazy Loader for Pandas HDFStore object
        Loads current date data into memory

        Args:
            date (dt.date): Date to load into memory
        """
        store = self.source
        start_string = f"pd.Timestamp('{date.strftime('%Y-%m-%d')}')"
        end_string = f"pd.Timestamp('{(date + dt.timedelta(days=1)).strftime('%Y-%m-%d')}')"
        load_string = f"index >= {start_string} & index < {end_string}"

        self.active_data = store.select(self.symbol, load_string)
        self.active_data.sort_index(inplace=True)
        self.active_date = date

    def _pd_save(self, store: pd.HDFStore):
        if self.source_type != "pandas":
            raise TypeError(f"Called to save on unsupported mode. Tried to use pandas_save while source is {self.source_type}")
        store.append(self.symbol, self._raw)

    def _deprecated_load_pandas(self, data: pd.DataFrame) -> None:
        """Eager loading of data into memory.
        Deprecated

        Args:
            data (pd.DataFrame): Data to load
        """
        self._raw = data
        if not self._raw.index.is_monotonic:
            self._raw = self._raw.sort_index()

        self.price_data = self._raw.groupby(pd.Grouper(freq="D"))

    def __getitem__(self, key: dt.date) -> pd.DataFrame:
        try:
            return self.price_data.get_group(key)
        except KeyError:
            return None

    def __len__(self):
        warnings.warn("Call to __len__ for PriceData object is innacurate. The length depends on the data source type")
        if self.source_type == "pandas-hdf5":
            return self.source.get_storer(self.symbol).nrows
        elif self.source_type == "pandas":
            return len(self.source)
        else:
            return 0


class PriceDataPack:
    cache_path = "data_cache"
    meta_path = "metadata"

    def __init__(self, source: str = None, path: str = None):
        self.symbols: list[str] = []
        self.data: dict[str, PriceData] = {}
        self.meta: DataPackMetaData = DataPackMetaData(source, path)

    def set_active_symbols(self, symbols: list[str]):
        if all(item in self.data.keys() for item in symbols):
            self.symbols = symbols
        else:
            raise ValueError(f"Given symbols cannot set to be active since the symbols data is not available")

    def get_price(self, symbol: str, datetime: dt.datetime):
        return self[symbol].get_price(datetime)

    def get_prices(self, symbol, date):
        return self[symbol].get_prices(date)

    def load_bulk_data(self, data: list[PriceData]) -> None:
        for item in data:
            self[item.symbol] = item

        self.symbols = [x for x in self.data.keys()]

    def __getitem__(self, key: str) -> PriceData:
        #Key is symbol
        return self.data[key]

    def __setitem__(self, key: str, value: PriceData) -> None:
        self.data[key] = value

    def __len__(self):
        return len(self.data)

    def save(self, path: str) -> None:
        self.meta.save(path)

    @classmethod
    def load_cache(cls, name: str, active_symbols: Optional[list[str]] = None, path_to_meta: Optional[str] = None) -> 'PriceDataPack':
        metadata = None
        cls.valid_filename(name, raise_error=True)
        metadata_dir = os.path.join(os.getcwd(), cls.cache_path, cls.meta_path)
        metadata_path = os.path.join(metadata_dir, name + ".pkl")

        with open(metadata_path, "rb") as f:
            metadata = pickle.load(f)

        if metadata.source == "pandas-hdf5":
            store = pd.HDFStore(metadata.source_path, mode="r")  # doesnt load into memory
            keys = store.keys()
            dps = []
            dp = cls()
            dp.meta = metadata

            # Dont load all of the cached data, just subsets
            if active_symbols:
                if all(item in [key.replace("/", "") for key in keys] for item in active_symbols):
                    keys = active_symbols

            for key in keys:
                symbol = key.replace("/", "")
                temp = PriceData(symbol, metadata.source, data_generator=store)
                dps.append(temp)

            dp.load_bulk_data(dps)

            return dp
        else:
            raise NotImplementedError("Only supports pandas-hdf5")

    @classmethod
    def load_pandas(cls, dfs: dict[str, pd.DataFrame], active_symbols: list = None):
        """Creates a PriceDataPack from a dictionary of pandas DataFrame

        Args:
            dfs (dict[str, pd.DataFrame]): dictionary of DataFrame. key of dictionary should be the symbol of the stock
            active_symbols (list, optional): optional list of symbol for . Defaults to None.

        Returns:
            [type]: [description]
        """
        metadata = DataPackMetaData("pandas", None)
        dp = cls()
        dp.meta = metadata
        dps = []
        for symbol, df in dfs.items():
            temp = PriceData(symbol, metadata.data_type, df=df)
            dps.append(temp)

        dp.load_bulk_data(dps)

        return dp

    @classmethod
    def load_sql(cls):
        pass

    @staticmethod
    def valid_filename(name: str, raise_error: bool = False):
        invalid = '<>:"/\|?* '
        name = os.path.splitext(name)[0]
        if any(item in invalid for item in name):
            if raise_error:
                raise ValueError(f"Filename cannot contain {invalid}")
            else:
                return False
        return True

    def create_cache(self, name: str, overwrite: bool = False):
        metadata = self.meta
        self.valid_filename(name, raise_error=True)  # Check if valid filename, this raises an error and stops execution
        cache_dir = os.path.join(os.getcwd(), self.cache_path)
        if not os.path.exists(cache_dir):
            os.mkdir(cache_dir)

        if not os.path.exists(os.path.join(cache_dir, self.meta_path)):
            os.mkdir(os.path.join(cache_dir, self.meta_path))

        file_name = name + ".h5"
        file_path = os.path.join(cache_dir, file_name)
        full_path = os.path.abspath(file_path)

        if os.path.exists(full_path) & (not overwrite):
            raise FileExistsError(f"{full_path} exists already. Set overwrite mode if you want to replace the file")

        if metadata.data_type == "pandas":
            store = pd.HDFStore(full_path, mode="w")

            for key, data in self.data.items():
                data._pd_save(store)

            store.close()
            metadata.data_type = "pandas-hdf5"
            metadata.file_path = full_path

            self.meta = metadata
            self.save(os.path.join(cache_dir, self.meta_path, name + ".pkl"))
            print(f"Saved cached data at {full_path}")
        else:
            raise NotImplementedError(f"Caching {metadata.data_type} is not yet supported")
