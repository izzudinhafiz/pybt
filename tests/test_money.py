if __name__ == "__main__":
    import os
    import sys
    import inspect
    currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    parentdir = os.path.dirname(currentdir)
    sys.path.append(parentdir)

from pybt.commons import Money
import pytest


def test_init():
    ms = [Money(1), Money(1.0), Money(1.000001), Money.from_cents(100), Money.from_cents(100.4569)]
    for m in ms:
        assert m == 1
        assert m == 1.0
        assert m == Money(1)
        assert m != 1.0000000001
        assert Money(m) == m

    ms = [Money(1.999), Money(2), Money(2.001), Money.from_cents(199.987)]
    for m in ms:
        assert m == 2
        assert m == 2.0
        assert m == Money(2)
        assert m != 2.0000000001
        assert Money(m) == m


def test_rounding():
    assert Money(1.379) == 1.38
    assert Money(1.371) == 1.37


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


def test_incr_decr():
    m1 = Money(2)
    m2 = Money(2)
    m3 = Money(2)
    m4 = Money(2)

    m1 += Money(1)
    m2 += 1
    m3 -= Money(1)
    m4 -= 1

    assert m1 == 3
    assert m2 == 3
    assert m3 == 1
    assert m4 == 1
