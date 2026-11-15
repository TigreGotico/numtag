"""String arithmetic checked against Python's own int and Fraction.

Only tests use the number types of Python. NUMTAG_SWEEP raises the number of
random cases for a long run on a compute box.
"""
import os
import random
import io
import tokenize
import unittest
from math import gcd
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path

from numtag import digits
from numtag.digits import Rational

CASES = int(os.environ.get("NUMTAG_SWEEP", "1"))
PACKAGE = Path(digits.__file__).parent


def _number(rng: random.Random, length: int) -> str:
    return str(rng.randrange(10 ** (length - 1) if length > 1 else 0, 10 ** length))


def _lengths(rng: random.Random, count: int, longest: int) -> list[int]:
    return [rng.choice((1, 2, 3, rng.randint(1, 40), rng.randint(1, longest)))
            for _ in range(count)]


class TestWholeArithmetic(unittest.TestCase):
    def test_add_subtract_multiply_compare_on_random_magnitudes(self):
        rng = random.Random(1)
        for a_len, b_len in zip(_lengths(rng, 2000 * CASES, 120), _lengths(rng, 2000 * CASES, 120)):
            a, b = _number(rng, a_len), _number(rng, b_len)
            x, y = int(a), int(b)
            self.assertEqual(digits.add(a, b), str(x + y))
            self.assertEqual(digits.multiply(a, b), str(x * y))
            self.assertEqual(digits.compare(a, b), (x > y) - (x < y))
            big, small = (a, b) if x >= y else (b, a)
            self.assertEqual(digits.subtract(big, small), str(abs(x - y)))

    def test_thousand_digit_numbers(self):
        rng = random.Random(2)
        for _ in range(5 * CASES):
            a, b = _number(rng, 1000), _number(rng, rng.randint(900, 1000))
            x, y = int(a), int(b)
            self.assertEqual(digits.add(a, b), str(x + y))
            self.assertEqual(digits.multiply(a, b), str(x * y))
            self.assertEqual(digits.subtract(a, b) if x >= y else digits.subtract(b, a),
                             str(abs(x - y)))
            self.assertEqual(digits.divide_whole(a, b[:30]), tuple(map(str, divmod(x, int(b[:30])))))

    def test_divide_whole_and_gcd(self):
        rng = random.Random(3)
        for _ in range(1000 * CASES):
            a, b = _number(rng, rng.randint(1, 60)), _number(rng, rng.randint(1, 30))
            if int(b) == 0:
                continue
            self.assertEqual(digits.divide_whole(a, b), (str(int(a) // int(b)), str(int(a) % int(b))))
            self.assertEqual(digits.gcd(a, b), str(gcd(int(a), int(b))))

    def test_shift_appends_zeros(self):
        self.assertEqual(digits.shift("12", 600), str(12 * 10 ** 600))
        self.assertEqual(digits.shift("0", 5), "0")

    def test_normalise_strips_leading_zeros(self):
        self.assertEqual(digits.normalise("007"), "7")
        self.assertEqual(digits.normalise("000"), "0")
        self.assertEqual(digits.normalise(""), "0")

    def test_subtract_refuses_a_negative_result(self):
        with self.assertRaises(ValueError):
            digits.subtract("3", "5")

    def test_divide_by_zero_raises(self):
        with self.assertRaises(ZeroDivisionError):
            digits.divide_whole("3", "0")


def _canonical_of(value: Fraction) -> str:
    """The canonical string of a Fraction, computed with Decimal."""
    denominator = value.denominator
    while denominator % 2 == 0:
        denominator //= 2
    while denominator % 5 == 0:
        denominator //= 5
    if denominator != 1:
        return f"{value.numerator}/{value.denominator}"
    if value.denominator == 1:
        return str(value.numerator)
    with localcontext() as context:
        context.prec = len(str(value.numerator)) + len(str(value.denominator)) + 10
        return format(Decimal(value.numerator) / Decimal(value.denominator), "f")


class TestRational(unittest.TestCase):
    def test_divide_gives_lowest_terms_or_a_finite_decimal(self):
        rng = random.Random(4)
        for _ in range(3000 * CASES):
            a = _number(rng, rng.randint(1, 25))
            b = str(rng.choice((2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 20, 25, 40, 64, 100, 125,
                                1000, 1024, 3125, rng.randint(1, 10 ** 6))))
            expected = Fraction(int(a), int(b))
            with self.subTest(a=a, b=b):
                got = digits.divide(a, b)
                self.assertEqual(got, _canonical_of(expected))
                self.assertEqual(Fraction(got), expected)

    def test_sums_and_products_of_signed_rationals(self):
        rng = random.Random(5)
        for _ in range(2000 * CASES):
            p = Rational(_number(rng, rng.randint(1, 20)), str(rng.randint(1, 50)), rng.random() < 0.5)
            q = Rational(_number(rng, rng.randint(1, 20)), str(rng.randint(1, 50)), rng.random() < 0.5)
            fp = Fraction(int(p.numerator), int(p.denominator)) * (-1 if p.negative else 1)
            fq = Fraction(int(q.numerator), int(q.denominator)) * (-1 if q.negative else 1)
            self.assertEqual(Fraction((p + q).canonical()), fp + fq)
            self.assertEqual(Fraction((p * q).canonical()), fp * fq)
            if fq:
                self.assertEqual(Fraction((p / q).canonical()), fp / fq)
            total = fp + fq
            self.assertEqual((p + q).canonical(), ("-" if total < 0 else "") + _canonical_of(abs(total)))

    def test_thousand_digit_decimal(self):
        rng = random.Random(6)
        whole, fraction = _number(rng, 1000), _number(rng, 400)
        expected = Fraction(int(whole + fraction), 10 ** len(fraction))
        got = Rational.from_decimal(whole, fraction).canonical()
        self.assertEqual(Fraction(got), expected)
        self.assertEqual(got, (whole + "." + fraction).rstrip("0").rstrip("."))

    def test_zero_is_never_negative(self):
        self.assertEqual(Rational("0", "5", True).canonical(), "0")
        self.assertEqual((Rational("3", "1", True) + Rational("3")).canonical(), "0")

    def test_scaled_appends_zeros(self):
        self.assertEqual(Rational.from_decimal("2", "5").scaled(6).canonical(), "2500000")
        self.assertEqual(Rational("1", "2").scaled(3).canonical(), "500")


class TestNoNumberTypesInThePackage(unittest.TestCase):
    """A value never passes through int, float, Decimal or Fraction."""

    def test_package_source_uses_none_of_them(self):
        """Code tokens only: comments and docstrings may name the types, and
        ``int`` may annotate an exponent; it may never convert."""
        hits, files = [], sorted(PACKAGE.rglob("*.py"))
        for path in files:
            with path.open("rb") as source:
                hits += [f"{path.name}:{line}" for line in _forbidden_uses(source.readline)]
        self.assertGreaterEqual(len(files), 2)
        self.assertEqual(hits, [])

    def test_the_scan_sees_each_forbidden_use(self):
        for code in (b"x = int('3')\n", b"x = float ('3')\n", b"from decimal import Decimal\n",
                     b"import fractions\n", b"y = Fraction\n"):
            with self.subTest(code=code):
                self.assertEqual(len(_forbidden_uses(io.BytesIO(code).readline)), 1)
        self.assertEqual(_forbidden_uses(io.BytesIO(b"def f(decimal: bool) -> int:  # int(3)\n    'Decimal'\n").readline), [])


def _forbidden_uses(readline) -> list[str]:
    """Lines where code calls int or float, names Decimal or Fraction, or
    imports the decimal or fractions module."""
    tokens = [t for t in tokenize.tokenize(readline)
              if t.type in (tokenize.NAME, tokenize.OP)]
    hits = []
    for previous, token, following in zip([None] + tokens, tokens, tokens[1:] + [None]):
        if token.type != tokenize.NAME:
            continue
        call = token.string in ("int", "float") and following is not None and following.string == "("
        module = (token.string in ("decimal", "fractions") and previous is not None
                  and previous.string in ("import", "from"))
        if call or module or token.string in ("Decimal", "Fraction"):
            hits.append(f"{token.start[0]}: {token.line.strip()}")
    return sorted(set(hits))
