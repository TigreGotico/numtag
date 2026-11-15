"""Arithmetic on digit strings.

A magnitude is a string of ASCII digits with no sign. A ``Rational`` is a sign,
a numerator and a denominator, each a magnitude. No value ever passes through
the number types of Python, so no value has a size limit or a rounding error.
Single digits and carries are small machine integers; ``ord`` reads a digit.
"""
from dataclasses import dataclass

_ZERO = ord("0")


def normalise(a: str) -> str:
    """``a`` without leading zeros; the empty string is zero."""
    return a.lstrip("0") or "0"


def compare(a: str, b: str) -> int:
    """-1, 0 or 1 as magnitude ``a`` is less than, equal to or more than ``b``."""
    a, b = normalise(a), normalise(b)
    if len(a) != len(b):
        return -1 if len(a) < len(b) else 1
    if a == b:
        return 0
    return -1 if a < b else 1


def _digits(a: str) -> list[int]:
    """The digits of ``a``, least significant first."""
    return [ord(c) - _ZERO for c in reversed(a)]


def _join(digits: list[int]) -> str:
    """The magnitude whose digits, least significant first, are ``digits``."""
    return normalise("".join(chr(_ZERO + d) for d in reversed(digits)))


def add(a: str, b: str) -> str:
    """The sum of two magnitudes."""
    x, y = _digits(a), _digits(b)
    out, carry = [], 0
    for i in range(max(len(x), len(y))):
        total = carry + (x[i] if i < len(x) else 0) + (y[i] if i < len(y) else 0)
        out.append(total % 10)
        carry = total // 10
    out.append(carry)
    return _join(out)


def subtract(a: str, b: str) -> str:
    """``a - b`` for magnitudes with ``a >= b``."""
    if compare(a, b) < 0:
        raise ValueError(f"{a} - {b} is negative")
    x, y = _digits(a), _digits(b)
    out, borrow = [], 0
    for i, digit in enumerate(x):
        total = digit - borrow - (y[i] if i < len(y) else 0)
        borrow = 1 if total < 0 else 0
        out.append(total + 10 * borrow)
    return _join(out)


def multiply(a: str, b: str) -> str:
    """The product of two magnitudes."""
    x, y = _digits(a), _digits(b)
    out = [0] * (len(x) + len(y))
    for i, dx in enumerate(x):
        if dx:
            for j, dy in enumerate(y):
                out[i + j] += dx * dy
    carry = 0
    for k, total in enumerate(out):
        total += carry
        out[k] = total % 10
        carry = total // 10
    return _join(out)


def shift(a: str, places: int) -> str:
    """``a`` times ten to the power ``places``: zeros appended."""
    a = normalise(a)
    return a if a == "0" else a + "0" * places


def divide_whole(a: str, b: str) -> tuple[str, str]:
    """Quotient and remainder of magnitude ``a`` by magnitude ``b``."""
    if normalise(b) == "0":
        raise ZeroDivisionError(f"{a} / 0")
    quotient, remainder = [], "0"
    for c in normalise(a):
        remainder = normalise(remainder + c)
        digit = 0
        while compare(remainder, b) >= 0:
            remainder = subtract(remainder, b)
            digit += 1
        quotient.append(chr(_ZERO + digit))
    return normalise("".join(quotient)), remainder


def gcd(a: str, b: str) -> str:
    """The greatest common divisor of two magnitudes, by Euclid's algorithm."""
    a, b = normalise(a), normalise(b)
    while b != "0":
        a, b = b, divide_whole(a, b)[1]
    return a


def _power_of_ten_exponent(denominator: str) -> int | None:
    """The least ``k`` with ``denominator`` dividing ``10**k``, or None."""
    twos = fives = 0
    while denominator != "1":
        half, rest = divide_whole(denominator, "2")
        if rest == "0":
            denominator, twos = half, twos + 1
            continue
        fifth, rest = divide_whole(denominator, "5")
        if rest != "0":
            return None
        denominator, fives = fifth, fives + 1
    return max(twos, fives)


@dataclass(frozen=True)
class Rational:
    """An exact signed value: ``-numerator/denominator`` when ``negative``."""
    numerator: str
    denominator: str = "1"
    negative: bool = False

    @classmethod
    def from_decimal(cls, whole: str, fraction: str = "") -> "Rational":
        """The value written ``whole.fraction``."""
        return cls(normalise(whole + fraction), shift("1", len(fraction)))

    def is_whole(self) -> bool:
        return divide_whole(self.numerator, self.denominator)[1] == "0"

    def is_zero(self) -> bool:
        return normalise(self.numerator) == "0"

    def __add__(self, other: "Rational") -> "Rational":
        left = multiply(self.numerator, other.denominator)
        right = multiply(other.numerator, self.denominator)
        denominator = multiply(self.denominator, other.denominator)
        if self.negative == other.negative:
            return Rational(add(left, right), denominator, self.negative)
        if compare(left, right) >= 0:
            return Rational(subtract(left, right), denominator, self.negative)
        return Rational(subtract(right, left), denominator, other.negative)

    def __mul__(self, other: "Rational") -> "Rational":
        return Rational(multiply(self.numerator, other.numerator),
                        multiply(self.denominator, other.denominator),
                        self.negative != other.negative)

    def __truediv__(self, other: "Rational") -> "Rational":
        return Rational(multiply(self.numerator, other.denominator),
                        multiply(self.denominator, other.numerator),
                        self.negative != other.negative)

    def __neg__(self) -> "Rational":
        return Rational(self.numerator, self.denominator, not self.negative)

    def scaled(self, places: int) -> "Rational":
        """This value times ten to the power ``places``."""
        return Rational(shift(self.numerator, places), self.denominator, self.negative)

    def canonical(self) -> str:
        """The canonical string: a whole number, a decimal or a fraction in
        lowest terms, with no "-0"."""
        common = gcd(self.numerator, self.denominator)
        numerator = divide_whole(self.numerator, common)[0]
        denominator = divide_whole(self.denominator, common)[0]
        sign = "-" if self.negative and numerator != "0" else ""
        places = _power_of_ten_exponent(denominator)
        if places is None:
            return f"{sign}{numerator}/{denominator}"
        digits = multiply(numerator, divide_whole(shift("1", places), denominator)[0])
        if places == 0:
            return sign + digits
        # In lowest terms with the least power of ten, the last digit is never 0.
        digits = digits.rjust(places + 1, "0")
        return f"{sign}{digits[:-places]}.{digits[-places:]}"


def divide(a: str, b: str) -> str:
    """The canonical string of ``a / b`` for magnitudes."""
    return Rational(a, b).canonical()
