from pybt.commons.helper import set_object_by_caller
from pybt import Market


class BaseScorer:
    def __init__(self):
        self.market = set_object_by_caller(Market)

    def execute(self, data):
        raise NotImplementedError("Scorer object must have an execute method defined")
