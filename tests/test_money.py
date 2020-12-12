if __name__ == "__main__":
    import os
    import sys
    import inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)

from commons.money import Money
import pytest


def test_init():
    ms = [Money(1), Money(1.0), Money(1.000001), Money.from_cents(100), Money.from_cents(100.6659)]
    for m in ms:
        assert m == 1
        assert m == 1.0
        assert m == Money(1)
        assert m != 1.0000000001
        assert Money(m) == m


def test_add():
    m1 = Money(1)
    m2 = Money(2)

    assert m1 + m2 == Money(3)
    assert m1 + m2 == 3
    assert m1 + m2 == 3.00
    assert m1 + m2 >= 3


def test_arithmetic():
    m1 = Money(4)
    m2 = Money(3)

    assert m1 / 2 == Money(2) and m1 / 2 == 2
    assert m2 / 2 == 1.5 and m2 / 2 == Money(1.5)
    assert m1 / 3 == 1.33 and m1 / 3 == Money(1.33)
    assert m1 * 2.5 == 10 and m1 * 2.5 == Money(10)
    assert m1 * 2.3333333 == Money(9.33)
    with pytest.raises(TypeError):
        m1 * m2
