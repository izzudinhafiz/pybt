from decimal import Decimal, ROUND_HALF_UP


class Money:
    __slots__ = ('cents',)

    def __init__(self, value):
        # if not isinstance(value, (int, float, Money, str)):
        #     raise TypeError(f"Value passed to Money object must be of type float, int or Money. Got type {type(value)}")

        if isinstance(value, float):
            decimalized = Decimal(str(value)).quantize(Decimal('1.11'), rounding=ROUND_HALF_UP) * 100
            self.cents = int(decimalized)
        elif isinstance(value, int):
            self.cents = value * 100
        elif isinstance(value, str):
            float(value)
            decimalized = Decimal(value).quantize(Decimal('1.11'), rounding=ROUND_HALF_UP) * 100
            self.cents = int(decimalized)
        else:
            self.cents = value.cents

    @ classmethod
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
        if isinstance(other, Money):
            return Money.from_cents(self.cents + other.cents)
        elif isinstance(other, int):
            return self + Money(other)
        else:
            raise TypeError(f"Cannot add Money object with type {type(other)}")

    def __radd__(self, other):
        return self + other

    def __sub__(self, other):
        if type(other) != Money:
            raise TypeError(f"Cannot subtract Money object with type {type(other)}")
        return Money.from_cents(self.cents - other.cents)

    def __rsub__(self, other):
        return self - other

    def __mul__(self, other):
        if not isinstance(other, (int, float)):
            return NotImplemented
        return Money.from_cents(self.cents * other)

    def __rmul__(self, other):
        return self * other

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

    def __iadd__(self, other):
        if not isinstance(other, (int, float, Money)):
            return NotImplemented

        if isinstance(other, Money):
            self.cents += other.cents

        if isinstance(other, float):
            self.cents = self.cents + int(round(other * 100))

        if isinstance(other, int):
            self.cents = self.cents + other * 100

        return self

    def __isub__(self, other):
        if not isinstance(other, (int, float, Money)):
            return NotImplemented

        if isinstance(other, Money):
            self.cents = self.cents - other.cents

        if isinstance(other, float):
            self.cents = self.cents - int(round(other * 100))

        if isinstance(other, int):
            self.cents = self.cents - other * 100

        return self

    def abs(self):
        return Money.from_cents(abs(self.cents))


if __name__ == '__main__':
    print(Money(171.545))
    value = Decimal('171.545').quantize(Decimal('1.11'), rounding=ROUND_HALF_UP)
    print(float(value))
    print(float(value * 100))
