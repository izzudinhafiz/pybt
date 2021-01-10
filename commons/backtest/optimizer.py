from commons.helper import set_object_by_caller
from commons.backtest import Portfolio


class BaseOptimizer:
    def __init__(self):
        self.portfolio = set_object_by_caller(Portfolio)

    def execute(self):
        raise NotImplementedError("Optimizer class must have an 'execute' method defined")
