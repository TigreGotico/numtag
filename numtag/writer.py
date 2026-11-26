"""Write a number as words from the ``writer`` block of a lexicon.

The block holds rule sets in the text syntax of ICU rule-based number
formatting (the CLDR RBNF files) and says which rule set speaks each form.
``Writer`` parses the rules once and runs them on digit strings: no value
passes through ``int``, ``float`` or ``Decimal``, and no rule or branch names
a language. docs/lexicon-format.md specifies the block.
"""
from dataclasses import dataclass
from enum import Enum
from functools import cache

from numtag import digits
from numtag.mention import Scale
from numtag.lexicon import UnsupportedLanguageError, load, writer_block
from numtag.tagger import lexicon_name

SOFT_HYPHEN = "­"
QUOTIENT, REMAINDER, CALL = "←", "→", "="
# Past this many integer digits a reading that repeats a scale word is no reading.
BIG = 15


class SpokenForm(str, Enum):
    """What the words say about the number."""
    CARDINAL = "cardinal"  # "twenty-one"
    ORDINAL = "ordinal"    # "twenty-first"
    YEAR = "year"          # "nineteen ninety-nine"; a language with no year rules reads the cardinal
    DIGITS = "digits"      # "two one": each digit of the written number


class SpellingReason(str, Enum):
    """Why a spelling stands at its rank."""
    STANDARD = "standard"                  # the spelling the writer gives by default
    NO_CONJUNCTION = "no_conjunction"      # the same without the optional joiner
    YEAR_PAIRS = "year_pairs"              # a year read in groups of two digits
    PLAIN = "plain"                        # the cardinal reading of a form that has a special one
    COUNTING = "counting"                  # the form that counts with no noun after it
    VARIANT_SPELLING = "variant_spelling"  # a second spelling of the same word


@dataclass(frozen=True)
class Spelling:
    """One way to write a number as words. Rank 0 is the default."""
    text: str
    reason: SpellingReason
    rank: int


@dataclass(frozen=True)
class _Rule:
    base: str
    divisor: str
    tokens: tuple


class _Ruleset:
    def __init__(self, name: str, rules: list[dict]):
        self.name = name
        self.negative = None
        self.rules: list[_Rule] = []
        for spec in rules:
            tokens = _parse(spec["text"], f"{name} {spec['value']!r}")
            if spec["value"] == "-x":
                self.negative = tokens
            else:
                self.rules.append(_Rule(spec["value"], _divisor(spec["value"], spec.get("radix", 10)), tokens))
        self.rules.sort(key=lambda rule: (len(rule.base), rule.base))

    def find(self, number: str) -> _Rule:
        found = None
        for rule in self.rules:
            if digits.compare(rule.base, number) > 0:
                break
            found = rule
        if found is None:
            raise ValueError(f"rule set {self.name!r} has no rule for {number}")
        return found


def _divisor(base: str, radix: int) -> str:
    """The radix to the exponent of the base: 1000 for the base 1500 at radix 10."""
    divisor, step = "1", str(radix)
    while digits.compare(digits.multiply(divisor, step), base) <= 0:
        divisor = digits.multiply(divisor, step)
    return divisor


def _parse(text: str, where: str) -> tuple:
    """The tokens of a rule text: ("lit", s), ("quo", set), ("rem", set), ("call", set), ("opt", tokens)."""
    text = text.removesuffix(";")
    tokens: list = []
    stack: list[list] = []
    literal = ""
    k = 0
    while k < len(text):
        char = text[k]
        if char in (QUOTIENT, REMAINDER, CALL):
            end = text.find(char, k + 1)
            inner = text[k + 1:end] if end > k else "?"
            if inner and not inner.startswith("%") or char == CALL and not inner:
                raise ValueError(f"{where}: unsupported rule text {text!r}")
            if literal:
                tokens.append(("lit", literal))
                literal = ""
            tokens.append(({QUOTIENT: "quo", REMAINDER: "rem", CALL: "call"}[char], inner[1:] or None))
            k = end
        elif char == "[":
            if literal:
                tokens.append(("lit", literal))
                literal = ""
            stack.append(tokens)
            tokens = []
        elif char == "]":
            if not stack:
                raise ValueError(f"{where}: unbalanced bracket in {text!r}")
            if literal:
                tokens.append(("lit", literal))
                literal = ""
            inner, tokens = tokens, stack.pop()
            tokens.append(("opt", tuple(inner)))
        elif char in "$#<>":
            raise ValueError(f"{where}: unsupported rule text {text!r}")
        else:
            literal += char
        k += 1
    if stack:
        raise ValueError(f"{where}: unbalanced bracket in {text!r}")
    if literal:
        tokens.append(("lit", literal))
    return tuple(tokens)


def _called(tokens: tuple):
    """The names of the rule sets that a rule text calls."""
    for kind, value in tokens:
        if kind == "opt":
            yield from _called(value)
        elif kind != "lit" and value:
            yield value


def _tidy(text: str) -> str:
    return " ".join(text.replace(SOFT_HYPHEN, "").split())


class Writer:
    """The writer of one lexicon."""

    def __init__(self, name: str, block: dict, scale: str):
        self.name = name
        self.block = block
        self.rulesets = {key: _Ruleset(key, spec["rules"]) for key, spec in block["rulesets"].items()}
        for ruleset in self.rulesets.values():
            for rule in ruleset.rules:
                for name in _called(rule.tokens):
                    if name not in self.rulesets:
                        raise ValueError(f"{self.name}: rule set {ruleset.name!r} calls the unknown rule set {name!r}")
        self.forms = block["forms"]
        self.decimal = block["decimal"]
        self.scale = scale

    def render(self, ruleset: str, number: str, negative: bool = False) -> str:
        """The words of a whole number (digits, no sign) in a rule set; ``negative`` applies its minus rule."""
        return _tidy(self._run(self.rulesets[ruleset], number, negative))

    def _run(self, ruleset: _Ruleset, number: str, negative: bool = False) -> str:
        number = digits.normalise(number)
        if negative:
            if ruleset.negative is None:
                raise ValueError(f"rule set {ruleset.name!r} has no rule for negative numbers")
            return self._fill(ruleset.negative, ruleset, number, "1", number)
        rule = ruleset.find(number)
        quotient, remainder = digits.divide_whole(number, rule.divisor)
        return self._fill(rule.tokens, ruleset, number, quotient, remainder)

    def _fill(self, tokens: tuple, ruleset: _Ruleset, number: str, quotient: str, remainder: str) -> str:
        out = ""
        for kind, value in tokens:
            if kind == "lit":
                out += value
            elif kind == "opt":
                if digits.normalise(remainder) != "0":
                    out += self._fill(value, ruleset, number, quotient, remainder)
            else:
                target = self.rulesets[value] if value else ruleset
                out += self._run(target, {"quo": quotient, "rem": remainder, "call": number}[kind])
        return out

    def minus(self, ruleset: str) -> str:
        """The minus word of a rule set: the text of its minus rule apart from the number."""
        return _tidy("".join(value for kind, value in self.rulesets[ruleset].negative if kind == "lit"))

    def spec(self, form: SpokenForm, scale: str | None = None) -> dict:
        """The form, with the sub-form of the scale in place of the base."""
        spec = self.forms.get(form.value)
        if spec is None and form in (SpokenForm.YEAR, SpokenForm.DIGITS):
            spec = self.forms["cardinal"]
        if spec is None:
            raise ValueError(f"{self.name}: no {form.value} form")
        return spec.get("scale", {}).get(scale or self.scale, spec)

    def variants(self, form: SpokenForm, gender: str | None, case: str | None, scale: str | None = None) -> list[dict]:
        spec = self.spec(form, scale)
        if case is not None:
            if case not in spec.get("case", {}):
                raise ValueError(f"{self.name}: no case {case!r}; it has {sorted(spec.get('case', {}))}")
            return spec["case"][case]
        return spec.get("gender", {}).get(gender, spec["variants"])


@cache
def _writer(name: str) -> Writer:
    block = writer_block(name)
    if block is None:
        raise UnsupportedLanguageError(f"no writer for language {name!r}")
    return Writer(name, block, load(name).scale.value)


def _split(value: str, keep_zeros: bool = False) -> tuple[bool, str, str]:
    """The sign, whole digits and fraction digits of a decimal digit string; ``keep_zeros`` keeps the
    trailing zeros of written decimals that are not all zeros."""
    negative = value.startswith("-")
    whole, point, fraction = value.removeprefix("-").partition(".")
    if not _is_digits(whole) or point and not _is_digits(fraction):
        raise ValueError(f"{value!r} is not a digit string")
    return negative, digits.normalise(whole), fraction if keep_zeros and fraction.strip("0") else fraction.rstrip("0")


def _is_digits(text: str) -> bool:
    return text.isascii() and text.isdigit()


def _round(whole: str, fraction: str, places: int) -> tuple[str, str]:
    """Whole and fraction digits rounded half away from zero to ``places`` decimals."""
    if len(fraction) <= places:
        return whole, fraction
    kept = whole + fraction[:places]
    if fraction[places] >= "5":
        kept = digits.add(kept, "1")
    kept = kept.rjust(places + 1, "0")
    return digits.normalise(kept[:len(kept) - places]), kept[len(kept) - places:].rstrip("0") if places else ""


def spell(value: str, lang: str, *, form: SpokenForm = SpokenForm.CARDINAL, gender: str | None = None,
          case: str | None = None, scale=None, places: int | None = None,
          scientific: bool = False, decimals: str | None = None) -> tuple[Spelling, ...]:
    """Every accepted spelling of ``value`` in the language, best first.

    ``value`` is a canonical digit string ("21", "-2.5") or a fraction "n/m".
    ``gender`` and ``scale`` select a reading only where the lexicon lists one,
    and any other lexicon ignores them; a ``scale`` other than short or long
    raises ``ValueError``. With no ``scale`` the form reads at
    the lexicon's ``scale`` setting. ``case`` raises ``ValueError`` where
    the lexicon has no such case. ``places`` is the count of decimals read,
    default the lexicon's. ``scientific`` reads the exponent form where the
    lexicon has one. ``decimals`` is "digits" (one word per decimal) or
    "number" (the decimals as one number, with the trailing zeros as
    written: "1.80" reads eighty), default the lexicon's.
    """
    writer = _writer(lexicon_name(lang))
    form = SpokenForm(form)
    if decimals not in (None, "digits", "number"):
        raise ValueError(f"decimals is 'digits' or 'number', not {decimals!r}")
    scale = scale and Scale(scale).value
    spec = writer.spec(form, scale)
    spellings: list[Spelling] = []
    for variant in writer.variants(form, gender, case, scale):
        text = _speak(writer, variant["ruleset"], value, form, places, scientific,
                      decimals or writer.decimal.get("read", "digits"), spec)
        if all(text != seen.text for seen in spellings):
            spellings.append(Spelling(text, SpellingReason(variant["reason"]), len(spellings)))
    return tuple(spellings)


def _speak(writer: Writer, ruleset: str, value: str, form: SpokenForm, places: int | None, scientific: bool,
           decimals: str, spec: dict) -> str:
    if "/" in value:
        return _fraction(writer, ruleset, value)
    negative, whole, fraction = _split(value, keep_zeros=decimals == "number")
    places = writer.decimal["places"] if places is None else places
    if form is SpokenForm.ORDINAL:
        return _ordinal(writer, ruleset, negative, whole, fraction, spec)
    if form is SpokenForm.DIGITS:
        return _each_digit(writer, ruleset, negative, whole, fraction)
    if scientific and (text := _exponent(writer, ruleset, negative, whole, fraction, places, decimals)):
        return text
    if (maximum := spec.get("maximum")) and digits.compare(whole, maximum) > 0:
        if text := _exponent(writer, ruleset, negative, whole, fraction, places, decimals):
            return text
        raise ValueError(f"{writer.name}: no words name a number above {maximum}")
    if fraction and places <= 0 and digits.compare(whole, "1") < 0 and fraction[0] < "5":
        negative, whole, fraction = False, "0", ""
    elif fraction and places > 0 and whole == "0" and _below_quantum(fraction, places):
        first = len(fraction) - len(fraction.lstrip("0")) + 1
        whole, fraction = _round(whole, fraction, first)
        places = first
    else:
        whole, fraction = _round(whole, fraction, max(places, 0))
    text = _plain(writer, ruleset, negative, whole, fraction, places, decimals)
    if not fraction and len(whole) > BIG and _padded(writer, ruleset, text):
        return _exponent(writer, ruleset, negative, whole, fraction, places, decimals) or text
    return text


def _below_quantum(fraction: str, places: int) -> bool:
    """Whether 0.<fraction> is under half of the last place that ``places`` reads."""
    zeros = len(fraction) - len(fraction.lstrip("0"))
    return zeros > places or zeros == places and fraction[zeros] < "5"


def _plain(writer: Writer, ruleset: str, negative: bool, whole: str, fraction: str, places: int,
           decimals: str = "digits") -> str:
    if digits.normalise(whole) == "0" and not fraction:
        negative = False
    text = writer.render(ruleset, whole, negative)
    if fraction:
        fraction = fraction[:places]
        if decimals == "number":
            zeros = len(fraction) - len(fraction.lstrip("0"))
            spoken = [writer.render(ruleset, "0")] * zeros + [writer.render(ruleset, fraction[zeros:])]
        else:
            spoken = [writer.render(ruleset, d) for d in fraction]
        text += " " + " ".join([writer.decimal["word"], *spoken])
    return text


def _each_digit(writer: Writer, ruleset: str, negative: bool, whole: str, fraction: str) -> str:
    words = [writer.render(ruleset, d) for d in whole]
    if fraction:
        words += [writer.decimal["word"], *[writer.render(ruleset, d) for d in fraction]]
    return " ".join(([writer.minus(ruleset)] if negative else []) + words)


def _ordinal(writer: Writer, ruleset: str, negative: bool, whole: str, fraction: str, spec: dict) -> str:
    minimum = spec.get("minimum", "0")
    if negative and writer.rulesets[ruleset].negative is not None and not fraction:
        return writer.render(ruleset, whole, negative=True)
    if negative or fraction or digits.compare(whole, minimum) < 0:
        raise ValueError(f"ordinals must be whole numbers from {minimum}")
    maximum = spec.get("maximum")
    if maximum and digits.compare(whole, maximum) > 0:
        raise ValueError(f"{writer.name}: no ordinal words name a number above {maximum}")
    return writer.render(ruleset, whole)


def _padded(writer: Writer, ruleset: str, text: str) -> bool:
    """Whether a reading repeats a word that is no digit word: a rule table past its last scale word."""
    digit_words = {writer.render(ruleset, d) for d in "0123456789"}
    words = text.split()
    return any(a == b and a not in digit_words for a, b in zip(words, words[1:]))


def _exponent(writer: Writer, ruleset: str, negative: bool, whole: str, fraction: str, places: int,
              decimals: str) -> str | None:
    """The scientific reading, or None when the exponent is 0 or the lexicon has no such form."""
    spec = writer.block.get("scientific")
    figures = (whole + fraction).lstrip("0")
    if spec is None or not figures:
        return None
    exponent = len(whole) - 1 if whole != "0" else -(len(fraction) - len(fraction.lstrip("0")) + 1)
    figures = figures.rstrip("0") or "0"
    if len(figures) - 1 > places:
        kept = figures[:places + 1]
        if figures[places + 1] >= "5":
            kept = digits.add(kept, "1")
            if len(kept) > places + 1:
                kept, exponent = kept[:-1], exponent + 1
        figures = kept.rstrip("0") or "0"
    if exponent == 0:
        return None
    mantissa = _plain(writer, ruleset, False, figures[0], figures[1:], places, decimals)
    sign = writer.minus(ruleset) + " " if negative else ""
    power = writer.render(ruleset, str(abs(exponent)))
    sign_power = writer.minus(ruleset) + " " if exponent < 0 else ""
    return f"{sign}{mantissa} {spec['times']} {sign_power}{power}"


def _fraction(writer: Writer, ruleset: str, value: str) -> str:
    spec = writer.block.get("fraction")
    top, _, bottom = value.partition("/")
    terms = top.removeprefix("-"), bottom.removeprefix("-")
    if not all(map(_is_digits, terms)):
        raise ValueError(f"{value!r} is not a fraction of two whole numbers")
    negative = top.startswith("-") != bottom.startswith("-")
    top, bottom = map(digits.normalise, terms)
    if bottom == "0":
        raise ZeroDivisionError(f"denominator is zero: {value}")
    whole, rest = digits.divide_whole(top, bottom)
    text = None
    if spec and spec.get("mixed") is False:
        if bottom == "1":
            raise ValueError(f"{writer.name}: a fraction over 1 has no counted reading: {value}")
        text = _counted(writer, ruleset, spec, top, bottom)
    elif spec and rest != "0" and digits.compare("2", bottom) <= 0 and digits.compare(bottom, str(spec["limit"])) <= 0:
        text = _mixed(writer, ruleset, spec, whole, rest, bottom)
    if text is None:
        text = f"{writer.render(ruleset, top)} {_ordinal_of(writer, bottom)}"
    return f"{writer.minus(ruleset)} {text}" if negative else text


def _counted(writer: Writer, ruleset: str, spec: dict, top: str, bottom: str) -> str:
    """The numerator and the word of the denominator: a named word, the reading of the ``ruleset``
    when the spec names one, else a one-word ordinal or the ``denominator`` text. A named word, an
    ordinal and a ``ruleset`` reading take the plural ending after a numerator other than 1."""
    count = writer.render(spec.get("numerator", ruleset), top)
    if bottom not in spec["named"] and "ruleset" in spec:
        word = writer.render(spec["ruleset"], bottom)
        return f"{count} {_capital(spec, word if top == '1' else _plural(word, spec['plural']))}"
    word = spec["named"].get(bottom) or _ordinal_of(writer, bottom)
    if " " in word:
        word = spec["denominator"].replace("{cardinal}", writer.render(ruleset, bottom))
        if "{numerator}" in word:  # a template that places the numerator itself: "trei pe douăzeci și cinci"
            return word.replace("{numerator}", writer.render(ruleset, top))
    elif top != "1":
        word = _plural(word, spec["plural"])
    return f"{count} {_capital(spec, word)}"


def _capital(spec: dict, word: str) -> str:
    return word[:1].upper() + word[1:] if spec.get("capitalise") else word


def _plural(word: str, plural: str | dict) -> str:
    """A string is a suffix; a map replaces the first matching ending ("o" to "i": "terzo", "terzi")."""
    if isinstance(plural, str):
        return word + plural
    end = next((end for end in plural if word.endswith(end)), "")
    return word[:len(word) - len(end)] + plural.get(end, "")


def _ordinal_of(writer: Writer, number: str) -> str:
    return writer.render(writer.variants(SpokenForm.ORDINAL, None, None)[0]["ruleset"], number)


def _mixed(writer: Writer, ruleset: str, spec: dict, whole: str, numerator: str, denominator: str) -> str:
    lead = [writer.render(ruleset, whole)] if whole != "0" else []
    if denominator in spec["named"]:
        return " ".join([*lead, spec["named"][denominator]])
    word = spec["denominator"].replace("{cardinal}", writer.render(ruleset, denominator))
    if numerator == "1" and not lead:
        return spec["single"].replace("{denominator}", word)
    return " ".join([*lead, writer.render(ruleset, numerator), word])


def as_fraction(value: str) -> str:
    """A decimal digit string as the fraction in lowest terms: "0.75" is "3/4".
    A whole number and a fraction stay as they are."""
    if "/" in value:
        return value
    negative, whole, fraction = _split(value)
    if not fraction:
        return value
    top, bottom = digits.normalise(whole + fraction), "1" + "0" * len(fraction)
    divisor = digits.gcd(top, bottom)
    top, bottom = digits.divide_whole(top, divisor)[0], digits.divide_whole(bottom, divisor)[0]
    return f"{'-' if negative else ''}{top}/{bottom}"
