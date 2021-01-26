import pickle


class DataPackMetaData:
    """
    Class to hold metadata about datapacks. Contains below minimum attribute.
    Can contain additional attributes based on data_source. inspect with .__dict__

    Attributes
    ----------
    data_type : str
        datapack type
    file_path : str
        path to actual datapack
    data_source : str
        where the data source came from (Alpaca, Quandl, Custom etcs)

    """

    def __init__(self, data_type: str = None, source: str = None, path: str = None, symbols: list[str] = None, **kwargs):
        self.data_type = data_type
        self.file_path = path
        self.data_source = source

        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(path: str) -> "DataPackMetaData":
        with open(path, "rb") as f:
            return pickle.load(f)
