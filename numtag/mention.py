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
    ROMAN = "roman"         # "XIV", "Ⅻ"


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


class Role(str, Enum):
    """What a part of a number does in it."""
    COUNT = "count"                # "três", "sessenta e seis", "2,5", "a" in "a dozen"
    SCALE = "scale"                # "mil", "milhões", "million", "thousandth"
    COLLECTIVE = "collective"      # "dúzias", "dezena", "a dozen" after "half"
    OF = "of"                      # "de" in "duas dúzias de milhar"
    JOINER = "joiner"              # "e", "and" between two parts
    HALF = "half"                  # "meia", "meio", "half", "a half"
    DENOMINATOR = "denominator"    # "terços", "quarter", "doze avos"
    MINUS = "minus"                # "menos", "minus"
    DECIMAL_MARK = "decimal_mark"  # "vírgula", "point"
    DECIMALS = "decimals"          # "zero cinco" after "vírgula"
    MANTISSA = "mantissa"          # "6.02", "1,5", "um vírgula cinco"
    TIMES = "times"                # "e", "E", "×", "·", "x", "*", "vezes"
    BASE = "base"                  # "10", "dez", "ten"
    EXPONENT = "exponent"          # "-23", "⁻²³", "^-3", "elevado a menos três"


#: The roles of words that name no number: their parts have no value.
NO_VALUE_ROLES = frozenset({Role.JOINER, Role.OF, Role.MINUS, Role.DECIMAL_MARK, Role.TIMES})


@dataclass(frozen=True)
class Part:
    """One piece of a mention in reading order. ``char_span`` indexes the
    input text, as the mention's does, so ``text[start:end] == part.text``.
    ``value`` is the canonical value of the part's words alone, or None
    for a role in ``NO_VALUE_ROLES``."""
    role: Role
    char_span: Tuple[int, int]
    text: str
    value: Optional[str] = None

    def __post_init__(self):
        start, end = self.char_span
        if not isinstance(self.role, Role):
            raise ValueError(f"role {self.role!r} is not a Role")
        if not 0 <= start < end or end - start != len(self.text):
            raise ValueError(f"char_span {self.char_span} does not fit text {self.text!r}")
        if (self.value is None) != (self.role in NO_VALUE_ROLES):
            raise ValueError(f"a {self.role.value} part takes {'no' if self.role in NO_VALUE_ROLES else 'a'} value")
        if self.value is not None and not is_canonical_value(self.value):
            raise ValueError(f"value {self.value!r} is not a canonical digit string")


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
    empty for a sure number. ``parts``, a keyword-only field left out of
    equality, lists the pieces of the mention in reading order; the value
    stays the one answer, and a caller does not add the parts up.
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
    parts: Tuple[Part, ...] = field(default=(), compare=False, kw_only=True)

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
        reached = start  # the end of the parts so far
        for part in self.parts:
            if not isinstance(part, Part):
                raise ValueError(f"part {part!r} is not a Part")
            part_start, part_end = part.char_span
            if not start <= part_start < part_end <= end \
                    or self.text[part_start - start:part_end - start] != part.text:
                raise ValueError(f"part {part!r} is not inside {self.text!r} at {self.char_span}")
            # two parts overlap only by the letter that two words of a compound share ("ettusen")
            shared = self.text[part_start - start:reached - start]
            if part_end <= reached or len(shared) > 1 or (shared and not shared.isalpha()):
                raise ValueError(f"part {part!r} is out of reading order")
            reached = part_end


class VagueKind(str, Enum):
    """What a vague quantity states."""
    MAGNITUDE = "magnitude"  # "millions", "dezenas": a scale, no value
    AMOUNT = "amount"        # "several", "muitos": no value, no scale, no bound


@dataclass(frozen=True)
class VagueQuantity:
    """Words that state an amount but no exact number.

    ``char_span`` and ``text`` work as in ``NumberMention``. A MAGNITUDE
    has a ``scale``, the canonical digit string of its scale word
    ("1000000" for "millions"), and a ``lower_bound`` when the scale word is
    plural: two of the scale ("2000000"). An AMOUNT has neither.
    ``confidence`` and the keyword-only ``reasons`` work as in
    ``NumberMention`` and are left out of equality.
    """
    char_span: Tuple[int, int]
    text: str
    kind: VagueKind
    scale: Optional[str] = None
    lower_bound: Optional[str] = None
    confidence: float = field(default=1.0, compare=False)
    reasons: frozenset[Reason] = field(default=frozenset(), compare=False, kw_only=True)

    def __post_init__(self):
        start, end = self.char_span
        if not 0 <= start < end or end - start != len(self.text):
            raise ValueError(f"char_span {self.char_span} does not fit text {self.text!r}")
        if not isinstance(self.kind, VagueKind):
            raise ValueError(f"kind {self.kind!r} is not a VagueKind")
        if self.kind is VagueKind.AMOUNT and (self.scale is not None or self.lower_bound is not None):
            raise ValueError("an amount takes no scale and no lower bound")
        if self.kind is VagueKind.MAGNITUDE and self.scale is None:
            raise ValueError("a magnitude takes a scale")
        for value in (self.scale, self.lower_bound):
            if value is not None and not is_canonical_value(value):
                raise ValueError(f"value {value!r} is not a canonical digit string")
        if not isinstance(self.reasons, frozenset) or not all(isinstance(r, Reason) for r in self.reasons):
            raise ValueError(f"reasons {self.reasons!r} is not a frozenset of Reason")
