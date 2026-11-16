"""The result type of the tagger: one number found in a text."""
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple


class Kind(str, Enum):
    """What the number counts or names."""
    CARDINAL = "cardinal"   # "duas dúzias", "21"
    ORDINAL = "ordinal"     # "vigésimo primeiro", "21st"
    FRACTION = "fraction"   # "um terço", "três quartos"
    DECIMAL = "decimal"     # "dois vírgula cinco", "2,5"


class Scale(str, Enum):
    """Short scale: a billion is a thousand millions. Long scale: a million millions."""
    SHORT = "short"
    LONG = "long"


class Reason(str, Enum):
    """Why a mention has a low confidence."""
    ARTICLE = "article"      # also an article or an indefinite pronoun: "comprei uma casa"
    HOMOGRAPH = "homograph"  # also a common word that is no number: "segunda", "second"


class Form(str, Enum):
    """How the number is written."""
    WORDS = "words"         # "dois milhões"
    DIGITS = "digits"       # "2000000"
    MIXED = "mixed"         # "2 milhões"


_WHOLE = r"-?(?:0|[1-9][0-9]*)"
_CANONICAL = re.compile(
    rf"{_WHOLE}"                          # whole number
    rf"|-?(?:0|[1-9][0-9]*)\.[0-9]*[1-9]"  # decimal, no trailing zero
    rf"|-?[1-9][0-9]*/[1-9][0-9]*")       # fraction
_NEGATIVE_ZERO = re.compile(r"-0(?:\.0*)?$")


def is_canonical_value(value: str) -> bool:
    """True when ``value`` is in one of the three canonical forms.

    A whole number has no leading zero and is never "-0"; a decimal has no
    trailing zero in its fraction part; a fraction has no zero part. Lowest
    terms and the rule that a fraction with a finite decimal form is written
    as a decimal need arithmetic, so the tagger's own value code keeps them.
    """
    return bool(_CANONICAL.fullmatch(value)) and not _NEGATIVE_ZERO.match(value)


@dataclass(frozen=True)
class NumberMention:
    """One number inside a longer text.

    ``char_span`` is the half-open ``(start, end)`` character extent in the
    original text, so ``text[start:end] == mention.text``. ``value`` is a
    canonical digit string ("1002", "-2.5", "1/3"); ``int()``,
    ``decimal.Decimal()`` and ``fractions.Fraction()`` read it. ``gender``
    is set when the words show it ("duas" is feminine). ``confidence`` is a
    deterministic score in ``(0, 1]`` that the words are a number at all
    (low for an article such as "uma casa"); it is not a probability and it
    is left out of equality. ``number_scale``, a keyword-only field, is the
    scale that gave the value, set only when the value depends on it: the
    words hold a scale word whose value differs between the long and the
    short scale ("bilião", "billion" and up). It is None for "mil", "milhão",
    "million", digits alone and every smaller number. ``reasons``, a
    keyword-only field left out of equality, says why the confidence is low:
    empty for a sure number.
    """
    char_span: Tuple[int, int]
    text: str
    value: str
    kind: Kind
    form: Form
    gender: Optional[str] = None
    confidence: float = field(default=1.0, compare=False)
    number_scale: Optional[Scale] = field(default=None, kw_only=True)
    reasons: frozenset[Reason] = field(default=frozenset(), compare=False, kw_only=True)

    def __post_init__(self):
        start, end = self.char_span
        if not 0 <= start < end or end - start != len(self.text):
            raise ValueError(f"char_span {self.char_span} does not fit text {self.text!r}")
        if not is_canonical_value(self.value):
            raise ValueError(f"value {self.value!r} is not a canonical digit string")
        if self.number_scale is not None and not isinstance(self.number_scale, Scale):
            raise ValueError(f"number_scale {self.number_scale!r} is not a Scale")
        if not isinstance(self.reasons, frozenset) or not all(isinstance(r, Reason) for r in self.reasons):
            raise ValueError(f"reasons {self.reasons!r} is not a frozenset of Reason")
