from decimal import *


class Money:
    def __init__(self, value):
        if not isinstance(value, (int, float, Money)):
            raise TypeError(f"Value passed to Money object must be of type float, int or Money. Got type {type(value)}")

        if isinstance(value, float):
            self.cents = int(round(value * 100))
        elif isinstance(value, int):
            self.cents = value * 100
        else:
            self.cents = value.cents

    @classmethod
    def from_cents(cls, value):
        _ = Money(0)
        if type(value) == int:
            _.cents = value
        elif type(value) == float:
            _.cents = int(round(value))
        else:
            raise TypeError(f"Cannot create {type(cls).__name__} from cents if cents not of type int or float")

        return _

    def __repr__(self):
        return f"{type(self).__name__}({self.cents / 100.0:.2f})"

    def __str__(self):
        return f"{self.cents / 100.0:.2f}"

    def __add__(self, other):
        if type(other) != Money:
            raise TypeError(f"Cannot add Money object with type {type(other)}")
        return Money.from_cents(self.cents + other.cents)

    def __sub__(self, other):
        if type(other) != Money:
            raise TypeError(f"Cannot subtract Money object with type {type(other)}")
        return Money.from_cents(self.cents - other.cents)

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            return NotImplemented
        return Money.from_cents(self.cents * other)

    def __truediv__(self, other):
        if not isinstance(other, (int, float, Money)):
            return NotImplemented

        if isinstance(other, (int, float)):
            return Money.from_cents(self.cents / other)

        if isinstance(other, Money):
            return self.cents / other.cents

    def __eq__(self, other):
        if type(other) == Money:
            if self.cents == other.cents:
                return True
            else:
                return False
        elif type(other) in [int, float]:
            if self.cents / 100 == other:
                return True
            else:
                return False
        else:
            raise TypeError(f"Cannot compare {self.__class__} with object of type {type(other)}")

    def __ne__(self, other):
        if type(other) == Money:
            if self.cents != other.cents:
                return True
            else:
                return False
        elif type(other) in [int, float]:
            if self.cents / 100 != other:
                return True
            else:
                return False
        else:
            raise TypeError(f"Cannot compare {self.__class__} with object of type {type(other)}")

    def __lt__(self, other):
        if type(other) == Money:
            if self.cents < other.cents:
                return True
            else:
                return False
        elif type(other) in [int, float]:
            if self.cents / 100 < other:
                return True
            else:
                return False
        else:
            raise TypeError(f"Cannot compare {self.__class__} with object of type {type(other)}")

    def __le__(self, other):
        return self < other or self == other

    def __gt__(self, other):
        if type(other) == Money:
            if self.cents > other.cents:
                return True
            else:
                return False
        elif type(other) in [int, float]:
            if self.cents / 100 > other:
                return True
            else:
                return False
        else:
            raise TypeError(f"Cannot compare {self.__class__} with object of type {type(other)}")

    def __ge__(self, other):
        return self > other or self == other


if __name__ == '__main__':
    a = [Money(2), Money(2.1), Money(2.1234), Money(Money(2))]
    print(int(1.991))
    print(int(0.99))
    for money in a:
        print(money)

    b = Money(2.1234)
    print(Money(2) + Money(2.1299))
    print(Money(2) / 3)

    c = [2, 2.0, 2.00, 2.01, 1.99, 1]

    for comp in c:
        print(comp, Money(2) <= comp)
