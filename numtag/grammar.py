"""The number grammar: one engine, driven by a language's lexicon.

Each rule takes a token position and returns every way it can read a number
part that starts there, as parses that record where they end. The tagger keeps
the longest parse at each position, so a number ends where no rule can take
the next word.

    number      := minus? (cardinal tail? | half-group | fraction | ordinal | digits-ordinal)
    cardinal    := group (joiner? group)*            group scales strictly descending
    group       := count? multiplier | small | small-decimal | digits
    multiplier  := scale-word
    count       := small | small-decimal | digits | cardinal of thousands   ("mil e quinhentos" milhões)
    small       := hundreds (joiner tens-units)? | tens-units      below 1000
    tens-units  := unit | ten (joiner unit)? | unit teen | unit ten-multiplier (joiner unit)?
    tail        := collective-tail | of-tail | half-tail | fraction-tail | decimal-tail
                 | half-collective-tail                              "cem e meia dúzia"

After a range cue ("entre", "between") the first number ends at a joiner that
splits the words into two numbers, the first smaller: "entre cem mil e um
milhão" is two numbers. Where two numbers could also split at another
joiner, the split with the fewest significant digits wins: "mil milhões e
mil e quinhentos milhões" is 1000000000 and 1500000000.
"""
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field, replace

from numtag import digits
from numtag.digits import Rational
from numtag.lexicon import CARDINAL_ROLES, MARK_ROLES, SCALE_ROLES, Entry, Joiner, Lexicon, TensOrder
from numtag.mention import Kind, Role
from numtag.tokenize import Token

ZERO = Rational("0")
ONE = Rational("1")
HALF = Rational("1", "2")
# The power of ten of "mil" and "thousand": the only scale whose cardinal
# counts a larger scale noun ("mil milhões", "mil biliões", "a thousand million").
THOUSAND = 3

# A part of a reading: its role, its first token, the token after it, and the
# value of its words alone (None for a word that names no number).
Piece = tuple[Role, int, int, Rational | None]
Pieces = tuple[Piece, ...]


def _piece(role: Role, start: int, end: int, value: Rational | None = None) -> Pieces:
    return ((role, start, end, value),)


def _joined(end: int, start: int) -> Pieces:
    """The joiner between a part that ends at ``end`` and one that starts
    at ``start``: a joiner token when there is one between them."""
    return _piece(Role.JOINER, end, start) if start > end else ()


def _add_count(parts: Pieces, start: int, end: int, value: Rational) -> Pieces:
    """``parts`` and the words from ``start`` to ``end``, which add ``value``.
    A count below the next scale word is one part, with its joiners: the
    words join a count right before them ("twenty first", "hundred and
    first"), and after a scale word they are a count of their own."""
    last = len(parts) - 1 if parts and parts[-1][0] == Role.JOINER else len(parts)
    if last and parts[last - 1][0] == Role.COUNT:
        _, first, _, count = parts[last - 1]
        return parts[:last - 1] + _piece(Role.COUNT, first, end, count + value)
    return parts + _piece(Role.COUNT, start, end, value)


def _times_power(parts: Pieces, at: int, exponent: int) -> Pieces:
    """``parts`` and the scale ordinal at ``at``, which multiplies the count
    right before it: "two hundredth" is one count, as "two hundred" is, and
    "six thousandth" is a count and a scale, as "six thousand" is."""
    word = ONE.scaled(exponent)
    if exponent >= THOUSAND:
        return parts + _piece(Role.SCALE, at, at + 1, word)
    if parts and parts[-1][0] == Role.COUNT and parts[-1][2] == at:
        _, first, _, count = parts[-1]
        return parts[:-1] + _piece(Role.COUNT, first, at + 1, count * word)
    return parts + _piece(Role.COUNT, at, at + 1, word)


def _from(parts: Pieces, start: int) -> Pieces:
    """``parts`` with the first one widened back to ``start``: a prefix or
    particle is in the part it introduces ("kedua", "wis sin")."""
    role, _, end, value = parts[0]
    return _piece(role, start, end, value) + parts[1:]


def _to(parts: Pieces, end: int) -> Pieces:
    """``parts`` with the last one widened to ``end``: an ending is in the
    part it ends ("hogeita batgarren")."""
    role, start, _, value = parts[-1]
    return parts[:-1] + _piece(role, start, end, value)


@dataclass(frozen=True)
class Parse:
    """A reading of the tokens from a start position up to ``end``."""
    end: int
    value: Rational
    # ORDINAL, or CARDINAL for every other reading: the tagger decides
    # between cardinal, decimal and fraction from the value.
    kind: Kind = Kind.CARDINAL
    # The value went through a decimal marker or a decimal digit string.
    decimal: bool = False
    # A word of the number has a common meaning that is no number.
    ambiguous: bool = False
    # The position of the case form that names the parts ("üçte" in "üçte
    # bir"): the number goes on after it although its ending closes it.
    parts_at: int | None = None
    # The parts of the reading in order, from the rule that gave the value.
    parts: Pieces = field(default=(), compare=False)


@dataclass(frozen=True)
class Group:
    """``count`` times ten to the power ``exponent``."""
    end: int
    count: Rational
    exponent: int = 0
    # The multiplier is a noun ("milhão"), not a numeral ("mil").
    noun: bool = False
    decimal: bool = False
    # A count that is itself a cardinal ("mil e quinhentos milhões") adds the
    # power of its largest scale to the place of the group, and a count of one
    # scale word ("mil milhões") also to the unit that a half after it halves.
    top: int = 0
    half_top: int = 0
    parts: Pieces = field(default=(), compare=False)

    @property
    def start(self) -> int:
        return self.parts[0][1]

    @property
    def order(self) -> int:
        return self.exponent + self.top

    @property
    def unit(self) -> int:
        return self.exponent + self.half_top


@dataclass(frozen=True)
class Count:
    end: int
    value: Rational
    # Written out, as opposed to the implicit one before "mil".
    explicit: bool = True
    # A count that only a multiplier or a collective can follow ("a", "meio").
    needs_multiplier: bool = False
    decimal: bool = False
    # For a count that is a cardinal: the power of its largest scale, and the
    # same power when the cardinal is one scale word with its count.
    top: int = 0
    half_top: int = 0
    parts: Pieces = field(default=(), compare=False)


def _sum(groups: tuple[Group, ...]) -> Rational:
    total = Rational("0")
    for group in groups:
        total = total + group.count.scaled(group.exponent)
    return total


def _run_parts(run: tuple[Group, ...]) -> Pieces:
    """The parts of a run of groups, with the joiners between them."""
    parts = run[0].parts
    for previous, group in zip(run, run[1:]):
        parts += _joined(previous.end, group.start) + group.parts
    return parts


class Grammar:
    def __init__(self, lexicon: Lexicon, tokens: list[Token], unsigned: int | None = None):
        """``unsigned``: the index of a signed digit string that starts a
        number, read without its sign. The tagger negates that number."""
        self.lex = lexicon
        self.tokens = tokens
        self.unsigned = unsigned
        self._groups: dict[tuple[int, bool, bool], list[Group]] = {}
        self._cardinals: dict[tuple[int, bool, bool], list[tuple[Group, ...]]] = {}
        self._vague: dict[int, bool] = {}
        self._parses: dict[int, list[Parse]] = {}
        group, decimal = re.escape(lexicon.group_mark), re.escape(lexicon.decimal_mark)
        self._digit_pattern = re.compile(
            rf"(?:[1-9][0-9]{{0,2}}(?:{group}[0-9]{{3}})+|[0-9]+)(?:{decimal}([0-9]+))?")
        # SI 5.4.4 "43 279.168 29": where the comma marks decimals and a mark
        # other than "." groups digits, a point after the groups marks them too
        self._group_point = re.compile(rf"([1-9][0-9]{{0,2}}(?:{group}[0-9]{{3}})+)\.([0-9]+)") \
            if lexicon.decimal_mark == "," and lexicon.group_mark != "." else None

    # Token access -----------------------------------------------------
    # A position before the first token reads as no word: "i - 1" at the
    # first token must not wrap to the last one.

    def _readings(self, i: int, role: str) -> tuple[Entry, ...]:
        if not 0 <= i < len(self.tokens) or self.tokens[i].is_digits:
            return ()
        entries = self.lex.of(self.tokens[i].norm, role)
        return entries if self.tokens[i].part else tuple(e for e in entries if not e.part)

    def _is_word(self, i: int, words: frozenset[str]) -> bool:
        return 0 <= i < len(self.tokens) and not self.tokens[i].is_digits and self.tokens[i].norm in words

    def _after_vague(self, i: int) -> bool:
        """A vague quantity ("nekoliko") stands before position ``i``: right
        before it, with one clitic between, or before a scale word or
        collective that itself follows one ("nekoliko stotina tisuća"). Only
        a space or a hyphen joins the words."""
        if not self.lex.vague_quantifiers:
            return False
        path = []
        while i not in self._vague:
            path.append(i)
            found, i = self._vague_step(i)
            if found is not None:
                break
        else:
            found = self._vague[i]
        self._vague.update(dict.fromkeys(path, found))
        return found

    def _vague_step(self, i: int) -> tuple[bool | None, int]:
        """(True, i) when a vague phrase ends before ``i``; (False, i) when
        nothing does; (None, j) when the chain goes on at ``j``."""
        end = i
        if 0 < i < len(self.tokens) and self.tokens[i].links_to_previous():
            if self._is_word(i - 1, self.lex.vague_clitics) and self.tokens[i - 1].links_to_previous():
                end = i - 1
        else:
            return False, i
        for phrase in self.lex.vague_quantifiers:
            start = end - len(phrase)
            if start >= 0 and all(t.norm == w and not t.is_digits for t, w in zip(self.tokens[start:end], phrase)) \
                    and not (start > 0 and self.starts_number(start - 1)
                             and (not self.tokens[start - 1].is_digits or self._plural_scale(start))):
                return True, i
        before = end - 1
        if before >= 0 and not self.tokens[before].is_digits and any(
                e.role in SCALE_ROLES or e.role == "collective"
                for e in self.lex.readings.get(self.tokens[before].norm, ())):
            return None, before
        return False, i

    def _plural_scale(self, i: int) -> bool:
        """"milhões": a plural scale word or collective. With a count before it
        ("3 milhões") it is a number, not a vague quantity."""
        return not self.tokens[i].is_digits and any(
            (e.role in SCALE_ROLES or e.role == "collective") and e.plural
            for e in self.lex.readings.get(self.tokens[i].norm, ()))

    def _goes_on(self, i: int, hundred: Entry) -> bool:
        """A hundred word that takes no count ("cento", "cem", never "dois
        cem") and goes on as a number: a bound form ("alguns cento e vinte")
        or one before a scale word ("algumas cem mil")."""
        return not self._readings(i, "hundred_multiplier") and (hundred.bound or self._takes_multiplier(i + 1))

    def _joined_after(self, i: int) -> bool:
        """A joiner and a number or a half follow position ``i``, past any
        scale words: "mil milhões e duzentos mil" and "mil milhões e meio" go
        on after "mil"."""
        while i < len(self.tokens) and not self.tokens[i].is_digits and any(
                e.role in SCALE_ROLES for e in self.lex.readings.get(self.tokens[i].norm, ())):
            i += 1
        return self._is_word(i, self.lex.joiners) and (
            self.starts_number(i + 1) or bool(self._readings(i + 1, "half")))

    def _after_joiner(self, i: int, policy: Joiner) -> list[int]:
        """Positions where the next part may start after position ``i``."""
        joined = [i + 1] if policy != Joiner.NEVER and self._is_word(i, self.lex.joiners) else []
        return joined if policy == Joiner.REQUIRED else [i] + joined

    def _takes_multiplier(self, i: int) -> bool:
        return i < len(self.tokens) and not self.tokens[i].is_digits and not self.closes(i - 1) and any(
            e.role in SCALE_ROLES for e in self.lex.readings.get(self.tokens[i].norm, ()))

    def closes(self, i: int) -> bool:
        """True when the word at ``i`` takes a case ending that closes the
        number: "ikide" (at two) counts no "yüz" after it."""
        if i < 0 or i >= len(self.tokens) or self.tokens[i].is_digits:
            return False
        entries = self.lex.readings.get(self.tokens[i].norm, ())
        # the parts after a decimal marker leave it open: "iki tam onda beş"
        if self.lex.decimal_fraction and self._is_word(i - 1, self.lex.decimal_markers) \
                and any(e.fraction_case for e in entries):
            return False
        return bool(entries) and all(e.final for e in entries)

    def _ordinal_form(self, i: int) -> bool:
        """True when every reading of the word at ``i`` that can be part of
        a cardinal is an ordinal form ("viides", "kolmannesta")."""
        entries = [e for e in self.lex.readings.get(self.tokens[i].norm, ()) if e.role in CARDINAL_ROLES] \
            if i < len(self.tokens) and not self.tokens[i].is_digits else []
        return bool(entries) and all(e.ordinal for e in entries)

    def _agrees(self, noun: bool, plural: bool, count: Rational, words: bool = False) -> bool:
        """Where a noun agrees with its count, a singular noun takes only a
        count below two: "um milhão", "meio milhão", "mil e um milhões". A
        plural noun takes no count of one or a half written in words: "meio
        milhões" and "um milhões" are not one number."""
        if not (noun and self.lex.scale_noun_agrees):
            return True
        if plural:
            return not (words and count in (ONE, HALF))
        return _whole(count) in ("0", "1")

    def _takes_count(self, i: int, count: Rational, count_exponent: int = 0, whole_group: bool = False) -> bool:
        """True when a multiplier at ``i`` takes ``count``, whose own scale
        word has ``count_exponent``: a larger scale word that agrees with the
        count. In "dois milhão" the "dois" stays a number, and in "cinquenta
        bilhões mil" the "mil" counts no billions. Where the lexicon says so,
        a hundred or ten multiplier counts no group of thousands: "bin yüz"
        is 1100, and "kaksituhatta kymmenen" is 2010. Nor does a hundred multiplier count
        a hundred word: "yüz yüze" is 100 and 100. Where a bare hundred word
        follows a scale word, a ``whole_group`` count of a hundred or more is
        no count of "hundred": in "tusind hundrede" the thousand ends its
        group and "hundrede" is the next one. A multiplier that starts a
        glued denominator takes no count: in "hét százezred" it is the
        "száz" of "százezred"."""
        if self._glued_denominators(i):
            return False
        scale_words = self.multipliers(i)
        if not scale_words:
            small = self._readings(i, "hundred_multiplier") + self._readings(i, "ten_multiplier")
            if self._readings(i - 1, "hundred") and self._readings(i, "hundred_multiplier"):
                return False
            if self.lex.small_multiplier_starts_group and any(e.exponent <= count_exponent for e in small):
                return False
            # Where the lexicon says so, a hundred multiplier takes no count
            # of a thousand or more: in "dvou tisíc sta" (2100) "sta" is 100.
            if self.lex.hundred_counts_below_thousand and len(_whole(count)) > 3:
                return False
            return self._takes_multiplier(i) and not (
                whole_group and self.lex.bare_hundred_after_scale and len(_whole(count)) > 2)
        return any(self._agrees(noun, plural, count) and count_exponent < exponent
                   for _, exponent, _, noun, _, plural in scale_words)

    def _homograph(self, i: int) -> bool:
        readings = () if self.tokens[i].is_digits else self.lex.readings.get(self.tokens[i].norm, ())
        return bool(readings) and all(e.ambiguous for e in readings)

    def starts_number(self, i: int) -> bool:
        if not 0 <= i < len(self.tokens):
            return False
        token = self.tokens[i]
        return token.is_digits or any(
            e.role != "half" and e.role not in MARK_ROLES and (token.part or not e.part)
            for e in self.lex.readings.get(token.norm, ()))

    def _digit_value(self, i: int) -> tuple[int, Rational, bool] | None:
        """End, value and whether it has decimals, of the digit string at
        ``i`` in the locale's marks; None when the marks do not fit. Where the
        locale groups digits with a space, "1 234 567,8" is one string."""
        token = self.tokens[i] if i < len(self.tokens) else None
        if token is None or not token.is_digits or token.suffix or token.period_ordinal:
            return None
        end, text = i + 1, self.tokens[i].latin
        if text[0] in "-\u2212":
            # a sign starts a number and never stands inside one: the tagger
            # reads a signed number without its sign and negates it
            if i != self.unsigned:
                return None
            text = text[1:]
        if text[0] in ".,":
            # a lone decimal mark (".5"): the tokenizer keeps only a listed one
            return end, Rational.from_decimal("0", text[1:]), True
        if self.lex.space_groups and re.fullmatch(r"[1-9][0-9]{0,2}", text):
            while end < len(self.tokens) and self._space_group(end):
                group = self.tokens[end].latin
                if self.lex.decimal_mark == "," and "." in group:
                    # SI 5.4.4 "43 279.168 29": a space group and a point are no two group marks
                    head, fraction = group.split(".")
                    return end + 1, Rational.from_decimal(text.replace(self.lex.group_mark, "") + head, fraction), True
                text += self.lex.group_mark + group
                end += 1
        match = self._digit_pattern.fullmatch(text)
        if not match and self._group_point and (si := self._group_point.fullmatch(text)):
            return end, Rational.from_decimal(si[1].replace(self.lex.group_mark, ""), si[2]), True
        if not match:
            # where the comma marks decimals, a point that cannot group digits
            # marks them: "1.5", "3.14159", "0.500". A time of day also
            # takes the point ("14.30", "24.00"), so that shape reads no
            # number.
            point = re.fullmatch(r"(0|[1-9][0-9]*)\.([0-9]+)", text) if self.lex.decimal_mark != "." else None
            if point is None or (re.fullmatch(r"[1-9][0-9]{0,2}", point[1]) and len(point[2]) == 3) \
                    or re.fullmatch(r"(?:1?[0-9]|2[0-3])\.[0-5][0-9]|24\.00", text):
                return None
            return end, Rational.from_decimal(point[1], point[2]), True
        whole_text = text.split(self.lex.decimal_mark)[0] if match.group(1) else text
        whole = whole_text.replace(self.lex.group_mark, "")
        return end, Rational.from_decimal(whole, match.group(1) or ""), bool(match.group(1))

    def _space_group(self, i: int) -> bool:
        """A group of three digits after a single space ("000" in "1 000")."""
        token = self.tokens[i]
        marks = re.escape(self.lex.decimal_mark) + ("." if self.lex.decimal_mark == "," else "")
        return (token.is_digits and not token.suffix and token.gap.isspace() and len(token.gap) == 1
                and re.fullmatch(rf"[0-9]{{3}}(?:[{marks}][0-9]+)?", token.latin) is not None)

    # Below a thousand -------------------------------------------------

    def tens_units(self, i: int, nonzero: bool = False) -> list[tuple[int, str]]:
        """Below a hundred. A bound unit stands only before a teen word or a
        ten ("أحد عشر"); a teen word after a unit adds ten to it ("ثلاثة
        عشر", "שלושה עשר"), and where numbers are written as one word only
        in that word ("yksitoista"); a unit before a ten reads unit first
        where the language says so ("einundzwanzig", "خمسة وعشرون")."""
        units = self._readings(i, "unit")
        found = [(i + 1, e.value) for e in units if not e.bound and not (nonzero and e.value == "0")]
        tens = [(i + 1, ten.value, ten.bound, ten.takes_unit or bool(ten.takes_units), ten.takes_units)
                for ten in self._readings(i, "ten")]
        # a teen is written in one word with its unit: "yksitoista" is 11,
        # "yksi toista" (one the other) is no number
        glued = i + 1 < len(self.tokens) and self.tokens[i + 1].glued
        teens = self._readings(i + 1, "teen") if glued or not self.lex.compound_words else ()
        for unit in units:
            if unit.value == "0":
                continue
            # "yksi" "toista" is 11; "kaksi" "kymmentä" is 20.
            found += [(i + 2, digits.add(teen.value, unit.value)) for teen in teens
                      if teen.ordinal_unit or not unit.ordinal]
            tens += [(i + 2, unit.value + "0", False, True, frozenset())
                     for m in self._readings(i + 1, "ten_multiplier") if m.exponent == 1]
            # "dua belas": a word after the unit that makes it a teen
            found += [(i + 2, digits.add(unit.value, suffix.value)) for suffix in self._readings(i + 1, "teen_suffix")]
        for end, value, bound, takes_unit, only in tens:
            if not bound:
                found.append((end, value))
            # A round ten from twenty up takes a unit after it, and so does
            # a ten whose entry says so ("on beş", "tizenöt").
            if self.lex.tens_order != TensOrder.UNIT_TEN and (bound or takes_unit or _round_ten(value)):
                for j in self._after_joiner(end, self.lex.joiner_tens_units):
                    found += [(j + 1, digits.add(value, unit.value))
                              for unit in self._readings(j, "unit") if unit.value != "0" and (not only or unit.value in only)]
        # "soixante-dix": a ten marked so also takes a number from ten to nineteen
        for ten in self._readings(i, "ten"):
            if ten.teens and _round_ten(ten.value):
                for j in self._after_joiner(i + 1, self.lex.joiner_tens_units):
                    found += [(j + 1, digits.add(ten.value, teen.value))
                              for teen in self._readings(j, "ten") if _teen(teen.value)]
        if self.lex.tens_order != TensOrder.TEN_UNIT:
            found += [(end, value) for end, value, _ in self._unit_tens(i, [u.value for u in units], "ten")]
        found += [(end, ten[0] + unit) for end, ten, unit in self._inverted(i, "ten")]
        return found

    def _inverted(self, i: int, role: str) -> list[tuple[int, str, str]]:
        """(end, ten, unit) of "pet|in|dvajset", a unit before a round ten
        of ``role`` in one compound word, where the language reads them so."""
        if self.lex.inverted_tens is None:
            return []
        found = []
        for unit in self._readings(i, "unit"):
            if unit.value == "0":
                continue
            for j in self._after_joiner(i + 1, self.lex.inverted_tens):
                if all(t.glued for t in self.tokens[i + 1:j + 1]):
                    found += [(j + 1, ten.value, unit.value) for ten in self._readings(j, role)
                              if len(ten.value) == 2 and ten.value[1] == "0" and ten.value != "10"]
        return found

    def _unit_tens(self, i: int, units: list[str], role: str) -> list[tuple[int, str, Entry]]:
        """A unit, the joiner and a round ten of ``role`` after it:
        "einundzwanzig" is 21, "enogtyvende" the ordinal 21. Where the
        lexicon writes them as one word, only the parts of one word count:
        "zwei und vierzig" is 2 and 40."""
        found = []
        for unit in units:
            if unit == "0":
                continue
            for j in self._after_joiner(i + 1, self.lex.joiner_unit_ten):
                if self.lex.unit_ten_one_word and not all(t.glued for t in self.tokens[i + 1:j + 1]):
                    continue
                found += [(j + 1, ten.value[0] + unit, ten) for ten in self._readings(j, role)
                          if _round_ten(ten.value)]
        return found

    def hundreds(self, i: int, multiplied: bool = True) -> list[tuple[int, str, bool]]:
        """(end, value, bound): a bound form stands only before the rest of
        the number ("cento e um", never "cento" alone). Without
        ``multiplied``, no hundreds from a count and a multiplier ("two
        hundred")."""
        # "birkaç yüz": a vague quantity right before the hundred stands where
        # its one would; after "birkaç bin" the hundred starts a lower group
        found = [(i + 1, e.value, e.bound) for e in self._readings(i, "hundred")
                 if e.value != "100" or self._goes_on(i, e) or not self._vague_step(i)[0]]
        if not multiplied:
            return found
        counts = self.tens_units(i, nonzero=True) + self._bound_units(i)
        if self._is_word(i, self.lex.articles):
            counts.append((i + 1, "1"))
        for end, count in counts:
            for multiplier in self._readings(end, "hundred_multiplier"):
                if not multiplier.plural or multiplier.counted:
                    found.append((end + 1, digits.shift(count, multiplier.exponent), False))
        return found

    def _bound_units(self, i: int) -> list[tuple[int, str]]:
        """A bound unit as the count of a multiplier ("telt" in "telt-mya")."""
        return [(i + 1, e.value) for e in self._readings(i, "unit") if e.bound and e.value != "0"]

    def small(self, i: int, nonzero: bool = False, multiplied: bool = True) -> list[tuple[int, str]]:
        found = self.tens_units(i, nonzero)
        for end, hundreds, bound in self.hundreds(i, multiplied):
            if not bound:
                found.append((end, hundreds))
            for j in self._after_joiner(end, self.lex.joiner_after_hundred):
                found += [(e, digits.add(hundreds, rest)) for e, rest in self.tens_units(j, nonzero=True)]
        return found

    def decimal_digits(self, i: int) -> list[tuple[int, int, str]]:
        """(start, end, digits) after a decimal marker, one reading per end: each word
        gives its own digits ("vírgula zero cinco" is .05). Where the words
        split in more than one way, the reading with the fewest parts wins,
        so "point twenty five" is .25 and not .205.

        The fractional part follows the grammar of the whole part (a
        structural ruling, no external source): a hundreds word never
        follows another part, as "cem" never follows units in a cardinal,
        so "zero vírgula vinte e cinco cem" is 0.25 and 100. A multiplier
        ("hundred") makes no digits: it multiplies the decimal number, so
        "one point two hundred" is 120."""
        if not self._is_word(i, self.lex.decimal_markers):
            return []
        starts = self._after_joiner(i + 1, self.lex.joiner_after_decimal_marker)
        fractions = [(i + 1, end, written) for end, written in self._decimal_fractions(i + 1)] \
            if self.lex.decimal_fraction else []
        best = {start: (0, "", start) for start in starts}
        digit_ends: set[int] = set()
        for position in range(min(starts), len(self.tokens)):
            if position not in best:
                continue
            parts, written, origin = best[position]
            # "oh" is the digit 0 after the marker only: "one point oh five"
            zeros = [(position + 1, "0") for _ in self._readings(position, "decimal_zero")[:1]]
            # "2 point 5": digits after the marker, alone. Before a part word
            # they are its numerator ("2 целых 5 сотых" is 2.05), or no
            # decimal digits at all ("2 целых 3 пятых").
            written_digits = self._plain_digits(position)
            digits_after = [(position + 1, written_digits)] if written_digits and not parts \
                and not self._readings(position + 1, "denominator") else []
            if position in digit_ends:
                continue
            digit_ends.update(end for end, _ in digits_after)
            for end, chunk in self.small(position, multiplied=False) + zeros + digits_after:
                if parts and len(chunk) == 3:
                    continue
                if end not in best or parts + 1 < best[end][0]:
                    best[end] = (parts + 1, written + chunk, origin)
        # a fraction reading wins over digits that end at the same word
        taken = {end for _, end, _ in fractions}
        found = fractions + [(origin, end, written) for end, (parts, written, origin) in best.items()
                             if parts and end not in taken]
        if self.lex.decimal_fractions:
            for start in starts:
                found += [(start, end, written) for end, written in self._decimal_fraction(start)]
        return found

    def _plain_digits(self, i: int) -> str | None:
        """The ASCII digits of a digit string at ``i`` with no mark, suffix
        or ordinal period: "5" in "2 point 5"."""
        token = self.tokens[i] if i < len(self.tokens) else None
        if token and token.is_digits and not token.suffix and not token.period_ordinal and token.latin.isdigit():
            return token.latin
        return None

    def _decimal_parts(self, i: int, start: int, end: int, fraction: str) -> Pieces:
        """The marker at ``i``, a joiner after it, and the decimals from
        ``start`` to ``end``."""
        return _piece(Role.DECIMAL_MARK, i, i + 1) + _joined(i + 1, start) \
            + _piece(Role.DECIMALS, start, end, Rational.from_decimal("0", fraction))

    def _glued_denominators(self, i: int) -> list[tuple[int, str, bool]]:
        """(end, value, ambiguous) of a denominator of a hundred or more glued
        to the count before it in one word: the count multiplies it, as it
        multiplies the scale word ("tízezred" is a ten-thousandth, as
        "tízezer" is ten thousand; "kétszázad" is a two-hundredth). After a
        hyphen the count is the second member of a range: "egy-kétszázad" is
        one or two hundredths."""
        if not self.lex.glued_denominators or i >= len(self.tokens) or self.tokens[i].glued \
                or self.tokens[i].gap.strip() in ("-", "–", "—"):
            return []
        found = []
        for end, count in self.small(i, nonzero=True):
            if not all(t.glued for t in self.tokens[i + 1:end + 1]):
                continue
            found += [(end + 1, digits.multiply(count, e.value), e.ambiguous) for e in self._readings(end, "denominator")
                      if not e.plural and len(e.value) > 2 and e.value == digits.shift("1", len(e.value) - 1)]
        return found

    def _lone_glued_denominator(self, i: int) -> list[Parse]:
        """"tízezred" with no number before it is one part of the product,
        one ten-thousandth. A number or a decimal marker before the word
        leaves it to the readings that fold that count in."""
        if not self.lex.glued_denominator_alone or i > 0 and (
                not self.tokens[i].gap.strip()
                and (self.starts_number(i - 1) or self._is_word(i - 1, self.lex.decimal_markers))):
            return []
        return [Parse(stop, Rational("1", value), ambiguous=self.lex.glued_denominator_alone_ambiguous,
                      parts=_piece(Role.DENOMINATOR, i, stop, Rational(value)))
                for stop, value, _ in self._glued_denominators(i)]

    def _lone_denominator(self, i: int) -> list[Parse]:
        """A part word that is also one part alone is a weak number: the bare
        noun also starts a compound noun that names no number, as a
        quarter-final. A number, a decimal marker or a joiner before the word
        leaves it to the readings that fold that count in: after a joiner
        with no number before it, the part adds to a whole that is no number
        word, as the hour of a time."""
        if i >= len(self.tokens) or i > 0 and not self.tokens[i].gap.strip() and (
                self.starts_number(i - 1) or self._is_word(i - 1, self.lex.decimal_markers | self.lex.joiners)):
            return []
        return [Parse(i + 1, Rational("1", e.value), ambiguous=True,
                      parts=_piece(Role.DENOMINATOR, i, i + 1, Rational(e.value)))
                for e in self._readings(i, "denominator") if e.weak_alone]

    def _inside_glued_denominator(self, i: int) -> bool:
        """True when the denominator at ``i`` ends a glued one ("ezred" in
        "tízezred"): it is no denominator of its own."""
        if i >= len(self.tokens) or not self.tokens[i].glued:
            return False
        start = i
        while start > 0 and self.tokens[start].glued:
            start -= 1
        return any(end == i + 1 for end, _, _ in self._glued_denominators(start))

    def _decimal_fraction(self, i: int) -> list[tuple[int, str]]:
        """"пять десятых", "двадцать пять сотых" after a decimal marker: the
        numerator written in as many digits as the denominator has zeros."""
        found = []
        written = self._plain_digits(i)
        numerators = self.small(i, nonzero=True) + ([(i + 1, written)] if written else [])
        for end, numerator in numerators:
            for entry in self._readings(end, "denominator"):
                zeros = len(entry.value) - 1
                if entry.value == digits.shift("1", zeros) and 0 < len(numerator) <= zeros:
                    found.append((end + 1, numerator.rjust(zeros, "0")))
        return found

    def _decimal_fractions(self, i: int) -> list[tuple[int, str]]:
        """"két tized" after "egész" is .2: a numerator below a denominator
        that is a power of ten gives that many decimal places. With the parts
        in a case that names them, the parts come first: "onda beş" after
        "tam" is .5."""
        found = []
        small = set(self.small(i, nonzero=True))
        # a numerator of a thousand or more is a whole cardinal: "kétezer-ötszáz tízezred" is .2500
        numerators = small | {
            (run[-1].end, _whole(_sum(run))) for run in self.cardinals(i)
            if not run[-1].decimal and _sum(run).is_whole() and _whole(_sum(run)) != "0"}
        for end, numerator in sorted(numerators):
            readings = () if self._inside_glued_denominator(end) else self._readings(end, "denominator")
            denominators = [(end + 1, e.value) for e in readings] \
                + [(stop, value) for stop, value, _ in self._glued_denominators(end)]
            for stop, value in denominators:
                places = len(value) - 1
                if value == digits.shift("1", places) and len(numerator) <= places:
                    found.append((stop, numerator.rjust(places, "0")))
            places = len(numerator) - 1
            last = self.tokens[end - 1]
            if places and (end, numerator) in small and numerator == digits.shift("1", places) and not last.is_digits \
                    and any(e.fraction_case for e in self.lex.readings.get(last.norm, ())):
                found += [(stop, count.rjust(places, "0")) for stop, count in self.small(end, nonzero=True)
                          if len(count) <= places]
        return found

    # Groups -----------------------------------------------------------

    def counts(self, i: int, first: bool) -> list[Count]:
        def count(end: int, value: Rational, **kwargs) -> Count:
            return Count(end, value, parts=_piece(Role.COUNT, i, end, value), **kwargs)

        smalls = self.small(i)
        found = [count(end, Rational(value)) for end, value in smalls]
        # "полтора", "półtora": one word with a value that is no whole number
        found += [count(i + 1, Rational(*e.value.split("/"))) for e in self._readings(i, "rational")]
        if self._is_word(i, self.lex.articles):
            found.append(count(i + 1, ONE, needs_multiplier=True))
        if self._readings(i, "half"):
            # "half a million": the article is in the scale part, as in "a million"
            end = i + 2 if self._is_word(i + 1, self.lex.articles) else i + 1
            found.append(Count(end, HALF, needs_multiplier=True, parts=_piece(Role.HALF, i, i + 1, HALF)))
        # "a half million"
        if self._is_word(i, self.lex.articles) and self._readings(i + 1, "half"):
            found.append(Count(i + 2, HALF, needs_multiplier=True, parts=_piece(Role.HALF, i, i + 2, HALF)))
        # "puolitoista" miljoonaa: a word that is a number on its own
        found += [count(i + 1, _rational(e.value)) for e in self._readings(i, "value_word")]
        found += [count(i + 1, Rational(*e.value.split("/"))) for e in self._readings(i, "fraction")]
        for end, value in smalls:
            whole = _piece(Role.COUNT, i, end, Rational(value))
            for start, e, fraction in self.decimal_digits(end):
                decimal = Rational.from_decimal(value, fraction)
                parts = whole + self._decimal_parts(end, start, e, fraction)
                found.append(Count(e, decimal, decimal=True, parts=parts))
                # "one point two hundred": a multiplier after the decimals
                found += [Count(e + 1, decimal.scaled(m.exponent), decimal=True,
                                parts=parts + _piece(Role.SCALE, e, e + 1, ONE.scaled(m.exponent)))
                          for m in self._readings(e, "hundred_multiplier") if not m.plural or m.counted]
            # "two and a half million", "zweieinhalb Millionen", "iki buçuk milyon"
            if value != "0":
                found += [Count(e, Rational(value) + HALF, needs_multiplier=True, parts=whole + half)
                          for half, e in self._halves_after(end)]
        found += [count(end, Rational(value), needs_multiplier=True) for end, value in self._bound_units(i)]
        # "δυόμισι": a unit and a half in one word
        found += [count(i + 1, Rational(e.value) + HALF) for e in self._readings(i, "unit_and_half")]
        if read := self._digit_value(i):
            # after the first group, digits only count a scale word: "2
            # milhões e 500 mil" is one number, "2 milhões e 500" two
            end, value, decimal = read
            found.append(count(end, value, needs_multiplier=not first, decimal=decimal))
            # "2 and a half million": digits before the half, as words are
            if not decimal and not value.is_zero():
                whole = _piece(Role.COUNT, i, end, value)
                # only a half after a joiner: a year before "полмиллиона" is its own number
                found += [Count(e, value + HALF, needs_multiplier=True, parts=whole + half)
                          for half, e in self._halves_after(end) if half[0][0] == Role.JOINER]
            # a counted hundred noun takes digits below a thousand as it takes
            # a word count: "3 מאות" is 300, as "שלוש מאות" is
            if len(_whole(value)) <= 3:
                found += [count(end + 1, value.scaled(m.exponent), needs_multiplier=not first, decimal=decimal)
                          for m in self._readings(end, "hundred_multiplier") if m.counted]
            if not decimal:
                whole = _piece(Role.COUNT, i, end, value)
                for start, e, fraction in self.decimal_digits(end):
                    found.append(Count(e, Rational.from_decimal(value.numerator, fraction), decimal=True,
                                       needs_multiplier=not first,
                                       parts=whole + self._decimal_parts(end, start, e, fraction)))
        return found

    def multipliers(self, i: int, starts: bool = False) -> list[tuple[int, int, str, bool, bool, bool]]:
        """(end, exponent, dual, noun, needs_count, plural) of each multiplier at ``i``.

        A noun needs a count, and so does a plural scale word when the
        language says so. A singular noun that ``starts`` the number counts
        one before "de": "milhão de pessoas" is 1000000. A dual holds its
        count ("ألفان" is two thousand) and takes none."""
        if self.closes(i - 1):
            return []
        found = []
        for role in ("scale_numeral", "scale_noun"):
            for entry in self._readings(i, role):
                noun = role == "scale_noun"
                needs_count = not entry.count and (noun or (entry.plural and self.lex.plural_scale_needs_count))
                if starts and noun and not entry.plural and self._is_word(i + 1, self.lex.of_words):
                    needs_count = False
                found.append((i + 1, entry.exponent, entry.count, noun, needs_count, entry.plural))
        return found

    def cardinal_counts(self, i: int, first: bool) -> list[Count]:
        """A cardinal whose largest scale is the thousand counts a larger scale
        noun after it: "mil e quinhentos milhões" is 1500 x 10^6, "a thousand
        million" is 10^9. A larger noun closes its group, so "um milhão e dois
        bilhões" is two numbers. A count with "e" after "mil" that is not
        well formed ("mil e cento e vinte" milhões) counts no noun."""
        found = []
        for run in self.cardinals(i, first, compound=False):
            if len(run) > 1 and not self._well_formed_after(run[0], run[1].count):
                continue
            if run[0].exponent == THOUSAND:
                single = len(run) == 1
                found.append(Count(run[-1].end, _sum(run), needs_multiplier=True,
                                   decimal=any(g.decimal for g in run), top=run[0].exponent,
                                   half_top=run[0].exponent if single else 0, parts=_run_parts(run)))
        return found

    def groups(self, i: int, first: bool, compound: bool = True) -> list[Group]:
        key = (i, first, compound)
        if key in self._groups:
            return self._groups[key]
        found = []
        counts = self.counts(i, first) + [Count(i, ONE, explicit=False)]
        if compound:
            counts += self.cardinal_counts(i, first)
        for count in counts:
            if count.explicit and not count.needs_multiplier and (first or not count.value.is_zero()):
                found.append(Group(count.end, count.value, decimal=count.decimal, parts=count.parts))
            if count.value.is_zero():
                continue
            # "nekoliko milijuna": a vague quantity stands where the count would
            vague = not count.explicit and self._after_vague(i)
            # "douăzeci de mii": a word may stand between a count and its scale word
            starts = [count.end] + ([count.end + 1] if count.explicit and self._is_word(
                count.end, self.lex.count_of) else [])
            for start in starts:
                # the article of "half a million" is in the scale part, as in "a million"
                before = count.parts + _piece(Role.OF, count.end, start) if start > count.end else count.parts
                scale_from = before[-1][2] if before and start == count.end else start
                for end, exponent, dual, noun, needs_count, plural in self.multipliers(
                        start, first and not count.explicit):
                    if count.top and exponent <= count.top:
                        continue
                    # "alguns mil e duzentos" is still 1200: a group joined after the scale words goes on the number
                    if vague and not self._joined_after(end):
                        continue
                    # a dual holds its count ("ألفان"): its one part is the scale
                    scale = _piece(Role.SCALE, scale_from, end, ONE.scaled(exponent))
                    if needs_count and not count.explicit:
                        # "milioi bat": the count of one comes after the noun
                        if self._is_word(end, self.lex.one_after_noun):
                            found.append(Group(end + 1, ONE, exponent, noun,
                                               parts=scale + _piece(Role.COUNT, end, end + 1, ONE)))
                        continue
                    if dual and count.explicit:
                        continue
                    value = Rational(dual) if dual else count.value
                    if not self._agrees(noun, plural, value, words=not self.tokens[i].is_digits):
                        continue
                    found.append(Group(end, value, exponent, noun, count.decimal,
                                       count.top, count.half_top, parts=before + scale))
        self._groups[key] = found
        return found

    def cardinals(self, i: int, first: bool = True, compound: bool = True) -> list[tuple[Group, ...]]:
        """Every run of groups with strictly descending scales from ``i``.
        Without ``compound``, no count is itself a cardinal, and a run may end
        before a scale word: that run is the count of the scale word."""
        key = (i, first, compound)
        if key in self._cardinals:
            return self._cardinals[key]
        found: list[tuple[Group, ...]] = []
        frontier = [(g,) for g in self.groups(i, first, compound)]
        while frontier:
            run = frontier.pop()
            last = run[-1]
            # A count belongs to the scale word after it: "dois milhões e três
            # milhões" is two numbers, not 2000003 and a stray "milhões".
            if compound and last.exponent == 0 and self._takes_count(last.end, last.count):
                continue
            if not self._lacks_joiner(run):
                found.append(run)
            if last.exponent == 0 or last.decimal:
                continue
            room = _room(last)
            for j in self._after_joiner(last.end, self.lex.joiner_between_groups):
                following = self.groups(j, first=False, compound=compound)
                # A plain group right before a scale word is the count of that
                # word: "mil milhões e dois mil milhões" is two numbers, not
                # 1000002000 and "milhões". Any other plain group joins the
                # run, so "um milhão e quinhentos mil e dois milhões" is
                # 1500000 and 2000000.
                for group in following:
                    # A count right after a scale numeral with no joiner
                    # counts the collective after it: "treze mil duas
                    # centenas" is 13000 and 200 (Miro).
                    if group.exponent == 0 and j == last.end and self._readings(group.end, "collective") \
                            and self.lex.joiner_before_last_group == Joiner.REQUIRED:
                        continue
                    count = group.count.scaled(group.exponent)
                    # a group of hundreds after the thousands joins them,
                    # except after a range cue, where the joiner joins the limits
                    hundreds = self.lex.joiner_thousand_hundreds and len(_whole(count)) == 3 \
                        and not (i > 0 and self._is_word(i - 1, self.lex.range_cues))
                    if j > last.end and self.lex.joiner_thousand_one_only \
                            and not (last.exponent == THOUSAND
                                     and (_whole(last.count) == "1" == _whole(count) or hundreds)):
                        continue
                    if compound and not group.top and self._takes_count(group.end, count, group.exponent, whole_group=True):
                        continue
                    # a comma between classes stands only before a group of a
                    # hundred or more: "one thousand, two hundred", not
                    # "one thousand, fifty"
                    if j == last.end and self.tokens[j].gap.startswith(",") and len(_whole(count)) < 3:
                        continue
                    if group.order < last.order and len(_whole(count)) <= room:
                        frontier.append(run + (group,))
        self._cardinals[key] = found
        return found

    def _lacks_joiner(self, run: tuple[Group, ...]) -> bool:
        """True for a last group below a hundred or a round hundred with no
        joiner before it, where the language requires the joiner there:
        "mil duzentos" is 1000 and 200, "mil e duzentos" is 1200, and "mil
        duzentos e quatro" is 1204. The run may still go on: "dois milhões
        quinhentos mil e quatro" is 2500004."""
        if len(run) < 2 or self.lex.joiner_before_last_group != Joiner.REQUIRED:
            return False
        if self._is_word(run[-2].end, self.lex.joiners):
            return False
        whole = _whole(run[-1].count)
        return len(whole) < 3 or (len(whole) == 3 and whole.endswith("00"))

    def _well_formed_after(self, group: Group, count: Rational) -> bool:
        """False for a count below a thousand after the joiner after the
        thousands that is not below a hundred, or, where the lexicon allows
        it, a round hundred: "mil e quinhentos" and "mil e vinte" are well
        formed, "mil e cento e vinte" and "thousand and five hundred" are
        not."""
        if group.exponent != THOUSAND or not self._is_word(group.end, self.lex.joiners):
            return True
        whole = _whole(count)
        return len(whole) < 3 or (self.lex.joiner_before_round_hundred and whole.endswith("00"))

    # Tails after a cardinal -------------------------------------------

    def _halves_after(self, i: int) -> list[tuple[Pieces, int]]:
        """Parts and end of "e meia", "and a half", "einhalb" and a bound
        half ("buçuk") at ``i``."""
        alone = _piece(Role.HALF, i, i + 1, HALF)
        found = [(alone, i + 1)] if self._is_word(i, self.lex.and_a_half) else []
        for j in self._after_joiner(i, self.lex.joiner_before_half):
            k = j + 1 if self._is_word(j, self.lex.articles) else j
            found += [(_joined(i, j) + _piece(Role.HALF, j, k + 1, HALF), k + 1)
                      for _ in self._readings(k, "half")[:1]]
        return found + [(alone, i + 1) for half in self._readings(i, "half") if half.bound][:1]

    def _lone_half(self, i: int) -> tuple[Pieces, int] | None:
        """Parts and end of "e meia" / "and a half" / "einhalb" at ``i`` when
        no number word follows."""
        if self._is_word(i, self.lex.and_a_half) and not self.starts_number(i + 1):
            return _piece(Role.HALF, i, i + 1, HALF), i + 1
        for parts, end in self._halves_after(i):
            # "um milhão e meio quilo": the half is half a kilo
            if not self.starts_number(end) and not self._is_word(end, self.lex.half_units):
                return parts, end
        return None

    def collective_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        # a scale noun closes its group ("um milhão e duas dúzias", "dois
        # milhares e duas dúzias"). Where a group may follow with no joiner,
        # the thousand counts with the cardinal, as "mil" does: "one
        # thousand twenty-four dozen" is 1024 x 12
        joins_freely = self.lex.joiner_before_last_group != Joiner.REQUIRED
        closes = [g.noun and (g.exponent > THOUSAND or not joins_freely) for g in run]
        if closes[-1]:
            return []
        split = max((n + 1 for n, c in enumerate(closes) if c), default=0)
        last = run[-1]
        found = []
        for entry in self._readings(last.end, "collective"):
            # A collective of a place value counts only the group after the
            # joiner, where the product fits below the group before it:
            # "treze mil e duas centenas" is 13200 (Miro), "três mil e
            # quinhentas centenas" is 350000. Any other collective counts the
            # whole cardinal: "mil e duas dúzias" is 12024 (Miro).
            place = split < len(run) - 1 and entry.value.strip("0") == "1" and len(
                _whole(last.count * Rational(entry.value))) <= _room(run[-2])
            cut = len(run) - 1 if place else split
            found += self._collective(_sum(run[:cut]), _sum(run[cut:]), entry, last.end, may_take_of=cut == 0 or place,
                                      parts=_run_parts(run))
        decimal = any(g.decimal for g in run)
        return [replace(p, decimal=decimal) for p in found]

    def _collective(self, prefix: Rational, count: Rational, entry: Entry, at: int,
                    may_take_of: bool, parts: Pieces = ()) -> list[Parse]:
        """The collective at ``at`` after the words of ``parts``."""
        size = Rational(entry.value)
        value = prefix + count * size
        end = at + 1
        parts += _piece(Role.COLLECTIVE, at, end, size)
        found = [Parse(end, value, parts=parts)]
        if (half := self._lone_half(end)) is not None:
            found.append(Parse(half[1], value + size * HALF, parts=parts + half[0]))
        if entry.addend:
            for j in self._after_joiner(end, Joiner.REQUIRED):
                found += [Parse(e, value + Rational(v), parts=parts + _joined(end, j)
                                + _piece(Role.COUNT, j, e, Rational(v)))
                          for e, v in self.small(j, nonzero=True)]
        if may_take_of:
            found += self._collective_of(value, end, parts)
        return found

    def _collective_of(self, value: Rational, i: int, parts: Pieces) -> list[Parse]:
        """"de" and a plural noun after a collective multiply it ("três
        centenas de milhões", "uma dúzia de dúzias"), and so does a class
        noun ("duas dezenas de milhar"). After the scale noun the number goes
        on as after any scale noun: "de dúzias" multiplies it, and after the
        joiner a smaller number adds to it ("duas centenas de milhar e
        quinhentos"), with a collective that counts only that number ("duas
        dezenas de milhar e três dúzias" is 20036)."""
        if not self._is_word(i, self.lex.of_words):
            return []
        at = i + 1
        parts += _piece(Role.OF, i, at)
        found = [Parse(at + 1, value * Rational(e.value),
                       parts=parts + _piece(Role.COLLECTIVE, at, at + 1, Rational(e.value)))
                 for e in self._readings(at, "collective") if e.plural]
        class_noun = self._is_word(at, self.lex.class_nouns)
        for noun in self._readings(at, "scale_noun"):
            if not (noun.plural or class_noun):
                continue
            scaled = value.scaled(noun.exponent)
            scale = parts + _piece(Role.SCALE, at, at + 1, ONE.scaled(noun.exponent))
            found += [Parse(at + 1, scaled, parts=scale)] + self._of(scaled, at + 1, parts=scale)
            for j in self._after_joiner(at + 1, Joiner.REQUIRED):
                for e, v in self.small(j, nonzero=True):
                    added = scale + _joined(at + 1, j) + _piece(Role.COUNT, j, e, Rational(v))
                    collectives = self._readings(e, "collective")
                    found += [Parse(e + 1, scaled + Rational(v) * Rational(c.value),
                                    parts=added + _piece(Role.COLLECTIVE, e, e + 1, Rational(c.value)))
                              for c in collectives]
                    if not collectives and not self._takes_multiplier(e):
                        found.append(Parse(e, scaled + Rational(v), parts=added))
        return found

    def of_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"dois milhões de dúzias": de and a plural noun multiply a cardinal
        that ends in a scale noun."""
        last = run[-1]
        if not last.noun:
            return []
        return self._of(last.count.scaled(last.exponent), last.end, prefix=_sum(run[:-1]), parts=_run_parts(run))

    def _of(self, total: Rational, i: int, prefix: Rational = ZERO, parts: Pieces = ()) -> list[Parse]:
        """"de dúzias", "de milhões" at ``i`` multiply ``total``, the last
        group, and add ``prefix``, the groups before it: "um bilião e dois
        milhões de dúzias" is 10^12 + 2 x 10^6 x 12."""
        if not self._is_word(i, self.lex.of_words):
            return []
        at = i + 1
        parts += _piece(Role.OF, i, at)
        found = [Parse(at + 1, prefix + total * Rational(e.value),
                       parts=parts + _piece(Role.COLLECTIVE, at, at + 1, Rational(e.value)))
                 for e in self._readings(at, "collective") if e.plural]
        found += [Parse(at + 1, prefix + total.scaled(e.exponent),
                        parts=parts + _piece(Role.SCALE, at, at + 1, ONE.scaled(e.exponent)))
                  for e in self._readings(at, "scale_noun") if e.plural]
        return found

    def half_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"um milhão e meio" adds half the noun, and "de dúzias" after it
        multiplies the whole ("um milhão e meio de dúzias"); "mil e meio" and
        "dois e meio" add a half of one."""
        last = run[-1]
        half = self._lone_half(last.end)
        if half is None or last.decimal:
            return []
        parts, end = _run_parts(run) + half[0], half[1]
        if last.noun or (self.lex.half_of_scale and last.exponent):
            group = last.count.scaled(last.exponent) + ONE.scaled(last.unit) * HALF
            prefix = _sum(run[:-1])
            return [Parse(end, prefix + group, parts=parts)] + self._of(group, end, prefix=prefix, parts=parts)
        return [Parse(end, _sum(run) + HALF, parts=parts)]

    def decimal_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"um milhão vírgula cinco" is 1000000.5."""
        last = run[-1]
        if last.exponent == 0:
            return []
        return [Parse(end, _sum(run) + Rational.from_decimal("0", fraction), decimal=True,
                      parts=_run_parts(run) + self._decimal_parts(last.end, start, end, fraction))
                for start, end, fraction in self.decimal_digits(last.end)]

    def fraction_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"dois e um terço" is 7/3, and "tiga dua-pertiga" 11/3 where the
        language puts no joiner before a part. Digits take no part without
        the joiner."""
        last = run[-1]
        if last.decimal:
            return []
        found = []
        starts = self._after_joiner(last.end, self.lex.joiner_before_half)
        if self.lex.joiner_after_decimal_marker != Joiner.NEVER and self._is_word(last.end, self.lex.decimal_markers):
            # "три целых и шесть седьмых": the whole part, its marker, a joiner and a fraction
            starts += self._after_joiner(last.end + 1, Joiner.REQUIRED)
        for j in starts:
            # digits take no part without the joiner ("tiga dua-pertiga" is 11/3)
            if j == last.end and self.tokens[j - 1].is_digits:
                continue
            # "três e um quarto"; "три целых и шесть седьмых" has the marker before the joiner
            parts = _run_parts(run) + tuple(
                (Role.DECIMAL_MARK if self._is_word(k, self.lex.decimal_markers) else Role.JOINER, k, k + 1, None)
                for k in range(last.end, j))
            # the whole part before the joiner makes the fraction clear: "três e um quarto"
            lone = self._lone_glued_denominator(j)
            found += [replace(f, value=_sum(run) + f.value, ambiguous=f in lone and f.ambiguous, parts=parts + f.parts)
                      for f in self.fractions(j)]
            # "dois mil e terço", "dois milhões e quarto"
            if not self.lex.part_after_joiner_needs_article:
                found += [Parse(j + 1, _sum(run) + Rational("1", e.value),
                                parts=parts + _piece(Role.DENOMINATOR, j, j + 1, Rational(e.value)))
                          for e in self._readings(j, "denominator") if not e.plural]
        return found

    def case_fraction_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"üçte bir" is 1/3: a cardinal whose last word is a case form that
        names the parts, and after it a count of parts below that number, so
        "ikide yüz" (at two, a hundred) is no fraction."""
        last = run[-1]
        at = last.end - 1
        if last.decimal or self.tokens[at].is_digits or not any(
                e.fraction_case for e in self.lex.readings.get(self.tokens[at].norm, ())):
            return []
        shares = _sum(run)
        if _whole(shares) in ("0", "1"):
            return []
        denominator = _piece(Role.DENOMINATOR, run[0].start, last.end, shares)
        return [Parse(end, Rational(numerator, shares.canonical()), parts_at=at,
                      parts=denominator + _piece(Role.COUNT, last.end, end, Rational(numerator)))
                for end, numerator in self.small(last.end, nonzero=True) if _less(Rational(numerator), shares)]

    # Other numbers ----------------------------------------------------

    def fractions(self, i: int) -> list[Parse]:
        """A numerator and a denominator: "dois terços", "a third",
        "doze vinte e cinco avos", "doze avos"."""
        # an ordinal form counts no parts: "kahdennesta kymmenennestä" is 20th
        def below(start: int, end: int, denominator: str) -> Pieces:
            return _piece(Role.DENOMINATOR, start, end, Rational(denominator))

        numerators = [(end, value) for end, value in self.small(i, nonzero=True)
                      if not self._ordinal_form(end - 1)]
        # "1 sixth", "3 quarters": digits count the parts. A denominator that
        # is also a common noun takes no digits: "3 quartos" are three rooms.
        # A count equal to the denominator is a count of things ("2 вторых
        # места", "the 4 quarters"), and a digit after a slash is a term of
        # a slash fraction ("5 1/2 quarters"). A digit right after a decimal
        # marker with a number before it is a decimal digit ("2 point 5
        # quarters"); with none, the marker word is a noun ("at that point 3
        # quarters").
        if ((read := self._digit_value(i)) and not read[2] and not read[1].is_zero()
                and self.tokens[i].gap.strip() != "/"
                and not (self._is_word(i - 1, self.lex.decimal_markers) and self.starts_number(i - 2))
                and not any(e.ambiguous or e.value == read[1].numerator
                            for e in self._readings(read[0], "denominator"))):
            numerators.append((read[0], read[1].numerator))
        # "doze avos": the particle is in the denominator
        found = [Parse(end + 1, Rational("1", value), parts=below(i, end + 1, value)) for end, value in numerators
                 if _above_ten(value) and self._is_word(end, self.lex.denominator_particles)]
        # "ربع" alone is a quarter, "ثلثان" two thirds
        found += [Parse(i + 1, Rational(e.numerator, e.value), ambiguous=e.ambiguous, parts=below(i, i + 1, e.value))
                  for e in self._readings(i, "denominator") if e.numerator]
        # "a décima parte", "uma quinta parte": an ordinal before a part noun
        # names the part
        if self._is_word(i + 1, self.lex.part_nouns):
            found += [Parse(i + 2, Rational("1", e.value), parts=below(i, i + 2, e.value))
                      for e in self._readings(i, "ordinal")]
        found += self._lone_glued_denominator(i) + self._lone_denominator(i)
        found += self._over_fractions(i)
        if self._is_word(i, self.lex.articles):
            numerators.append((i + 1, "1"))
        # "heren bat": one after the denominator
        found += [Parse(i + 2, Rational("1", e.value), ambiguous=e.ambiguous,
                        parts=below(i, i + 1, e.value) + _piece(Role.COUNT, i + 1, i + 2, ONE))
                  for e in self._readings(i, "denominator")
                  if not e.plural and self._is_word(i + 1, self.lex.one_after_noun)]
        for end, numerator in numerators:
            count = _piece(Role.COUNT, i, end, Rational(numerator))
            if self._is_word(end + 1, self.lex.part_nouns):
                found += [Parse(end + 2, Rational(numerator, e.value), parts=count + below(end, end + 2, e.value))
                          for e in self._readings(end, "ordinal")]
            # "um quinto andar" is the fifth floor, "um quinto do bolo" a fifth
            ordinal_after_article = end == i + 1 and self._is_word(i, self.lex.articles) \
                and bool(self._readings(end, "ordinal")) and bool(self.lex.partitives) \
                and end + 1 < len(self.tokens) \
                and not self._is_word(end + 1, self.lex.partitives | self.lex.joiners)
            # "egy tízezred": the count before a glued denominator
            found += [Parse(stop, Rational(numerator, value), ambiguous=ambiguous, parts=count + below(end, stop, value))
                      for stop, value, ambiguous in self._glued_denominators(end)]
            glued = self._inside_glued_denominator(end)
            for entry in () if glued else self._readings(end, "denominator"):
                # "um terço", "dois terços"; "dois milésimo" is the ordinal 2000.º
                if self.lex.fraction_agreement and not entry.invariant and entry.plural == (numerator == "1"):
                    continue
                if ordinal_after_article:
                    continue
                found.append(Parse(end + 1, Rational(numerator, entry.value), ambiguous=entry.ambiguous,
                                   parts=count + below(end, end + 1, entry.value)))
            for after, denominator in self.small(end, nonzero=True):
                if _above_ten(denominator) and self._is_word(after, self.lex.denominator_particles):
                    found.append(Parse(after + 1, Rational(numerator, denominator),
                                       parts=count + below(end, after + 1, denominator)))
            # "seperenam belas": the prefix makes the cardinal after it the
            # denominator, and the cardinal may go on past the word
            if self._readings(end, "denominator_prefix") and end + 1 < len(self.tokens) \
                    and self.tokens[end + 1].glued:
                found += [Parse(run[-1].end, Rational(numerator, _whole(_sum(run))),
                                parts=count + below(end, run[-1].end, _whole(_sum(run))))
                          for run in self.cardinals(end + 1)
                          if not run[-1].decimal and _sum(run).is_whole() and _whole(_sum(run)) != "0"]
        return found

    def _over_fractions(self, i: int) -> list[Parse]:
        """A cardinal, a word that reads "a/b" aloud, and a second cardinal:
        the first is the numerator and the second the denominator. The word
        belongs to the denominator part."""
        if not self.lex.fraction_over:
            return []
        found = []
        for top in self.cardinals(i):
            if top[-1].decimal or not _sum(top).is_whole() or not self._is_word(top[-1].end, self.lex.fraction_over):
                continue
            count = _piece(Role.COUNT, i, top[-1].end, _sum(top))
            found += [Parse(run[-1].end, Rational(_whole(_sum(top)), _whole(_sum(run))),
                            parts=count + _piece(Role.DENOMINATOR, top[-1].end, run[-1].end, _sum(run)))
                      for run in self.cardinals(top[-1].end + 1)
                      if not run[-1].decimal and _sum(run).is_whole() and _whole(_sum(run)) != "0"]
        return found

    def scale_fractions(self, i: int) -> list[Parse]:
        """A fraction word after a scale word takes that part of it: "milioi
        erdi bat" is 500000 and "hiru milioi laurden" 750000. With no count,
        the scale word and the fraction word make one compound noun, with or
        without the one after it."""
        if not self.lex.fraction_after_scale:
            return []
        found = []
        for end, exponent, _, _, _, plural in self.multipliers(i):
            if plural:
                continue
            scale = _piece(Role.SCALE, i, end, ONE.scaled(exponent))
            one = _piece(Role.COUNT, end + 1, end + 2, ONE) if self._is_word(end + 1, self.lex.one_after_noun) else ()
            for share, piece in self._parts(end):
                found.append(Parse(end + 1, ONE.scaled(exponent) * share, parts=scale + piece))
                if one:
                    found.append(Parse(end + 2, ONE.scaled(exponent) * share, parts=scale + piece + one))
        for run in self.cardinals(i):
            if run[-1].exponent and not run[-1].decimal:
                found += [Parse(run[-1].end + 1, _sum(run) * share, parts=_run_parts(run) + piece)
                          for share, piece in self._parts(run[-1].end)]
        return found

    def _parts(self, i: int) -> list[tuple[Rational, Pieces]]:
        """The share that a singular half or denominator at ``i`` names, and its part."""
        return [(HALF, _piece(Role.HALF, i, i + 1, HALF)) for _ in self._readings(i, "half")] + [
            (Rational("1", e.value), _piece(Role.DENOMINATOR, i, i + 1, Rational(e.value)))
            for e in self._readings(i, "denominator") if not e.plural]

    def fraction_of_collective(self, fraction: Parse) -> list[Parse]:
        """"um terço de dúzia", "one third of a dozen": that part of the collective."""
        if not self._is_word(fraction.end, self.lex.fraction_of_words):
            return []
        at = fraction.end + 2 if self._is_word(fraction.end + 1, self.lex.articles) else fraction.end + 1
        parts = fraction.parts + _piece(Role.OF, fraction.end, fraction.end + 1)
        return [Parse(at + 1, fraction.value * Rational(entry.value),
                      parts=parts + _piece(Role.COLLECTIVE, fraction.end + 1, at + 1, Rational(entry.value)))
                for entry in self._readings(at, "collective") if not entry.plural]

    def fraction_of_scale(self, fraction: Parse) -> list[Parse]:
        """"um quarto de milhão", "a quarter of a million": that part of the
        singular scale noun. A scale numeral ("mil") is no noun: "um quarto
        de mil euros" is a quarter and a thousand."""
        if not self.lex.fraction_of_scale or not self._is_word(fraction.end, self.lex.fraction_of_words):
            return []
        start = fraction.end + 1
        at = start + 1 if self._is_word(start, self.lex.articles) else start
        parts = fraction.parts + _piece(Role.OF, fraction.end, start)
        # a scale word that starts a longer number ("mil milhões", "milhar de
        # milhões", "um milhão e meio") is not the whole part
        longest = max((p.end for i in {start, at} for p in self._numbers(i)), default=at)
        return [Parse(end, fraction.value * ONE.scaled(exponent),
                      parts=parts + _piece(Role.SCALE, start, end, ONE.scaled(exponent)))
                for end, exponent, dual, noun, _, plural in self.multipliers(at)
                if noun and not dual and not plural and end >= longest]

    def half_collectives(self, i: int) -> list[Parse]:
        """"meia dúzia", "half a dozen", "a half dozen". The article of "half
        a dozen" is in the collective part, as in "a dozen"."""
        found = []
        if self._readings(i, "half"):
            at = i + 2 if self._is_word(i + 1, self.lex.articles) else i + 1
            found += [Parse(at + 1, HALF * Rational(entry.value),
                            parts=_piece(Role.HALF, i, i + 1, HALF)
                            + _piece(Role.COLLECTIVE, i + 1, at + 1, Rational(entry.value)))
                      for entry in self._readings(at, "collective") if not entry.plural]
        if self._is_word(i, self.lex.articles) and self._readings(i + 1, "half"):
            found += [Parse(i + 3, HALF * Rational(entry.value),
                            parts=_piece(Role.HALF, i, i + 2, HALF)
                            + _piece(Role.COLLECTIVE, i + 2, i + 3, Rational(entry.value)))
                      for entry in self._readings(i + 2, "collective") if not entry.plural]
        return found

    def half_collective_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"cem e meia dúzia" is 106, as "um milhão e duas dúzias" adds its
        dozens."""
        if run[-1].decimal:
            return []
        found = []
        for j in self._after_joiner(run[-1].end, Joiner.REQUIRED):
            parts = _run_parts(run) + _joined(run[-1].end, j)
            found += [replace(p, value=_sum(run) + p.value, parts=parts + p.parts) for p in self.half_collectives(j)]
        return found

    def half_numbers(self, i: int) -> list[Parse]:
        """"meia dúzia" and "meia dúzia de milhar", "dúzia e meia", and a
        half alone."""
        halves = [half for half in self._readings(i, "half") if not half.bound]
        half_part = _piece(Role.HALF, i, i + 1, HALF)
        found = [Parse(i + 1, HALF, ambiguous=half.ambiguous, parts=half_part) for half in halves]
        # "erdi bat": one after the half, as after a denominator
        if self._is_word(i + 1, self.lex.one_after_noun):
            found += [Parse(i + 2, HALF, ambiguous=half.ambiguous,
                            parts=half_part + _piece(Role.COUNT, i + 1, i + 2, ONE)) for half in halves]
        for parse in self.half_collectives(i):
            found += [parse] + self._collective_of(parse.value, parse.end, parse.parts)
        for entry in self._readings(i, "collective"):
            if not entry.plural and (half := self._lone_half(i + 1)) is not None:
                found.append(Parse(half[1], Rational(entry.value) * Rational("3", "2"),
                                   parts=_piece(Role.COLLECTIVE, i, i + 1, Rational(entry.value)) + half[0]))
        return found

    def ordinals(self, i: int) -> list[Parse]:
        """"vigésimo primeiro", "dois milésimo", "twenty-first", "two hundredth"."""
        prefixes: list[tuple[int, Rational | None, Joiner, tuple[Group, ...]]] = [(i, None, Joiner.NEVER, ())]
        prefixes += [(run[-1].end, _sum(run), self._joiner_after(run[-1]), run) for run in self.cardinals(i)
                     if not run[-1].decimal]
        found = []
        by_place = self.lex.ordinal_joiner_by_place
        # "the one hundredth" is the ordinal, "one hundredth" the fraction
        one_is_fraction = self.lex.one_before_ordinal_scale_is_fraction and not (
            self.lex.ordinal_articles and self._after_article(i))
        for start, prefix, policy, run in prefixes:
            run_parts = _run_parts(run) if run else ()
            # after a ten, the joiner is the one between a ten and a unit:
            # "forty and eighth" is 40 and 8th, as "forty and eight" is 40 and 8
            tens = bool(run) and not run[-1].exponent and not _whole(run[-1].count).endswith("00")
            positions = [start] if prefix is None or self.lex.ordinal_style == "every_word" \
                else self._after_joiner(start, policy if by_place or tens else Joiner.OPTIONAL)
            last_group_counts = by_place and len(run) > 1 and not run[-1].exponent
            # "soixante-dixième": a ten that takes a teen takes a teen ordinal
            teens = any(t.teens for t in self._readings(start - 1, "ten")) and bool(run)
            for j in positions:
                found += self._ordinal_words(j, run, run_parts + _joined(start, j),
                                             scales=not by_place or (j == start and not last_group_counts),
                                             teens=teens, one_is_fraction=one_is_fraction)
            if not last_group_counts:
                continue
            # "six thousand nine hundredth": the scale ordinal counts only the
            # last group, 6000 + 9 x 100, when it fits below the group before
            for scale in self._readings(start, "ordinal_scale"):
                count = run[-1].count.scaled(scale.exponent)
                if not scale.plural and len(_whole(count)) <= _room(run[-2]):
                    found += self._ordinal_rest(start + 1, _sum(run[:-1]) + count, scale.ambiguous,
                                                _times_power(run_parts, start, scale.exponent))
        found += self._ordinal_affixes(i)
        if not self.lex.ordinal_articles or self._after_article(i):
            return found
        # "noua clădire" is "the new building": "a noua" is the ordinal
        return [p for p in found if not any(
            e.after_article for e in self.lex.readings.get(self.tokens[p.end - 1].norm, ())
            if e.role in ("ordinal", "ordinal_scale"))]

    def _ordinal_affixes(self, i: int) -> list[Parse]:
        """A cardinal with an ordinal ending on its last word ("ventitreesimo",
        "hogeita batgarren"), or an ordinal prefix on its first ("kedua",
        "ke-2")."""
        found = [Parse(run[-1].end + 1, _sum(run), Kind.ORDINAL, parts=_to(_run_parts(run), run[-1].end + 1))
                 for run in self.cardinals(i)
                 if not run[-1].decimal and self._readings(run[-1].end, "ordinal_ending")
                 and self.tokens[run[-1].end].glued]
        prefixes = self._readings(i, "ordinal_prefix")
        if prefixes and i + 1 < len(self.tokens) and (
                self.tokens[i + 1].glued or self.tokens[i + 1].gap == "-"):
            # "kedua pihak": a prefixed word that starts the phrase, before a
            # word, may count a group ("both sides"); after a word it is an
            # ordinal ("anaknya yang kedua", "terbesar kedua di dunia")
            weak = i == 0 and self.tokens[i + 1].glued and any(p.ambiguous for p in prefixes)
            found += [Parse(run[-1].end, _sum(run), Kind.ORDINAL,
                            ambiguous=weak and run[-1].end < len(self.tokens), parts=_from(_run_parts(run), i))
                      for run in self.cardinals(i + 1) if not run[-1].decimal and _sum(run).is_whole()]
        return found


    def _joiner_after(self, last: Group) -> Joiner:
        """Where a joiner may stand before the ordinal word that ends a
        number, by the place of the cardinal word before it: after a scale
        word as between groups, after a round hundred as after "hundred",
        else as between a ten and a unit ("tjueførste", never "tjue og
        første")."""
        if last.exponent:
            return self.lex.joiner_between_groups
        if _whole(last.count).endswith("00"):
            return self.lex.joiner_after_hundred
        return self.lex.joiner_tens_units

    def _ordinal_words(self, j: int, run: tuple[Group, ...], before: Pieces, scales: bool = True,
                       teens: bool = False, one_is_fraction: bool = True) -> list[Parse]:
        """The ordinal words at ``j`` after the cardinal ``run``, with the
        scale ordinals that multiply its last group when ``scales``. Where the
        joiner goes by place, no joiner stands before a scale ordinal ("to
        og hundrede" is 2 and 100th). Where an ordinal is its cardinal with the last word made
        ordinal, a scale ordinal below the power of ten of the run's last
        group adds one of its own when its cardinal word names a number by
        itself: "duizendhonderdste" is 1100, as "duizend honderd" is 1100.
        With ``teens``, a teen ordinal follows the ten ("soixante-dix-septième").
        ``before`` holds the parts of the run and of a joiner after it."""
        prefix = _sum(run) if run else None
        top = run[-1].exponent if run else 0
        found = []
        for scale in self._readings(j, "ordinal_scale") if scales else ():
            if scale.plural and not self.tokens[j].glued \
                    or one_is_fraction and prefix is not None and prefix.canonical() == "1":
                # "cinque centesimi" and "um milésimo" are fractions; one
                # word ("duemillesimi") is the ordinal
                continue
            if prefix is not None and scale.exponent < top and scale.alone and self.lex.ordinal_style == "last_word":
                value = prefix + ONE.scaled(scale.exponent)
                parts = before + _piece(Role.SCALE if scale.exponent >= THOUSAND else Role.COUNT, j, j + 1,
                                        ONE.scaled(scale.exponent))
            else:
                value = _ordinal_scale_value(run, scale.exponent)
                if value is None:
                    continue
                parts = _times_power(before, j, scale.exponent)
            found += self._ordinal_rest(j + 1, value, scale.ambiguous, parts)
        words = [(j + 1, entry.value, entry) for entry in self._readings(j, "ordinal")]
        if self.lex.tens_order != TensOrder.TEN_UNIT:
            units = [e.value for e in self._readings(j, "unit")]
            words += self._unit_tens(j, units, "ordinal")
        words += [(end, digits.add(ten, unit), Entry("ordinal", digits.add(ten, unit)))
                  for end, ten, unit in self._inverted(j, "ordinal")]
        for end, value, entry in words:
            if prefix is None:
                rest = self._ordinal_rest(end, Rational(value), entry.ambiguous,
                                          _piece(Role.COUNT, j, end, Rational(value)))
                if entry.bound:
                    found += rest[1:]
                elif value in self.lex.bound_ordinal_values:
                    found += rest[:1]
                else:
                    found += rest
            elif entry.standalone:
                continue  # "dix premiers" is 10 and 1st, never 11th
            elif self.lex.ordinal_style == "last_word" \
                    and (_room_for(prefix, value) or (teens and _teen(value))) \
                    and (self.lex.ten_joins_unit_ordinal
                         or not (len(value) == 1 and prefix.numerator.endswith("10"))):
                # a unit ordinal joins no "ten": "ten third" is 10 and 3rd
                found.append(Parse(end, prefix + Rational(value), Kind.ORDINAL,
                                   parts=_add_count(before, j, end, Rational(value))))
            elif self.lex.ordinal_style == "tail_words" and _room_for(prefix, value):
                found += self._ordinal_rest(end, prefix + Rational(value), False,
                                            _add_count(before, j, end, Rational(value)))
        return found

    def _ordinal_rest(self, j: int, value: Rational, ambiguous: bool, parts: Pieces) -> list[Parse]:
        """The parse so far, and in "every_word" and "tail_words" style each
        smaller ordinal word that adds to it."""
        found = [Parse(j, value, Kind.ORDINAL, ambiguous=ambiguous, parts=parts)]
        if self.lex.ordinal_style == "first_word" and len(value.numerator) == 1 and value.denominator == "1":
            # "الحادي عشر", "الخامس والعشرون": the ordinal unit, then the
            # teen word or the joiner and a cardinal ten
            unit = value.numerator
            if self._readings(j, "teen"):
                found.append(Parse(j + 1, Rational("1" + unit), Kind.ORDINAL, ambiguous=ambiguous,
                                   parts=_add_count(parts, j, j + 1, Rational("10"))))
            for k in self._after_joiner(j, self.lex.joiner_tens_units):
                found += [Parse(k + 1, Rational(ten.value[0] + unit), Kind.ORDINAL, ambiguous=ambiguous,
                                parts=_add_count(parts + _joined(j, k), k, k + 1, Rational(ten.value)))
                          for ten in self._readings(k, "ten") if _round_ten(ten.value)]
        if self.lex.ordinal_style in ("every_word", "tail_words"):
            for entry in self._readings(j, "ordinal"):
                if _room_for(value, entry.value):
                    found += self._ordinal_rest(j + 1, value + Rational(entry.value), False,
                                                _add_count(parts, j, j + 1, Rational(entry.value)))
        return found

    def digit_ordinal(self, i: int) -> list[Parse]:
        token = self.tokens[i]
        if not (token.is_digits and (token.suffix or token.period_ordinal)) or not token.digits.isdigit():
            return []
        value = Rational(digits.normalise(token.digits))
        return [Parse(i + 1, value, Kind.ORDINAL, parts=_piece(Role.COUNT, i, i + 1, value))]

    # The whole number -------------------------------------------------

    def numbers(self, i: int) -> list[Parse]:
        """Every reading from ``i``. Among readings of the same length the
        first wins, so "a million and a half" takes the half of the noun
        before the half of one. After a range cue the first number ends at
        the range joiner. Where the words split into two numbers at more
        than one joiner, the split with the fewest significant digits wins."""
        left = self._range_left(i)
        if left is None:
            left = self._split_left(i)
        return self._numbers(i) if left is None else left

    def _range_left(self, i: int) -> list[Parse] | None:
        """After a range cue ("entre", "between"), the readings of the first
        number when a joiner splits the words into two numbers, the left one
        smaller: "entre cem mil e um milhão" is 100000 and 1000000."""
        if i == 0 or not self._is_word(i - 1, self.lex.range_cues):
            return None
        signed = i == self.unsigned
        splits = [(left, right, inner, digits) for left, right, inner, digits in self._splits(i)
                  if _less(-left[0].value if signed else left[0].value, right.value)]
        if signed and splits:
            # a negative first limit is below any right side, so only the
            # right limit that reaches furthest leaves two numbers: "entre -2
            # milhões e meio e 3 milhões" does not split at the first "e"
            furthest = max(right.end for _, right, _, _ in splits)
            splits = [split for split in splits if split[1].end == furthest]
        return self._fewest_digits((left, inner, digits) for left, _, inner, digits in splits)

    def _split_left(self, i: int) -> list[Parse] | None:
        """With no range cue, where the longest number from ``i`` and the
        number right after it could also split at a joiner, the readings of
        the first number of the split with the fewest significant digits:
        "mil milhões e mil e quinhentos milhões" is 1000000000 and
        1500000000, not 1000001000 and 500000000. None when the longest
        reading wins."""
        plain = self._numbers(i)
        if not plain:
            return None
        first = max(plain, key=lambda p: p.end)
        joined = self._is_word(first.end, self.lex.joiners)
        start = first.end + 1 if joined else first.end
        after = self._numbers(start) if start < len(self.tokens) else []
        if not after:
            return None
        second = max(after, key=lambda p: p.end)
        digits = _significant_digits(first.value) + _significant_digits(second.value)
        splits = [(left, inner, n) for left, right, inner, n in self._splits(i)
                  if right.end == second.end and left[0].end != first.end]
        best = self._fewest_digits([([first], joined and self._inner(i, first.end), digits)] + splits)
        return None if best[0] is first else best

    def _splits(self, i: int) -> Iterator[tuple[list[Parse], Parse, bool, int]]:
        """Each joiner that splits the words from ``i`` into two numbers:
        the readings of the first, the longest reading of the second, True
        for a joiner inside a number below a thousand, and the significant
        digits of both. A joiner inside a number below a thousand ("sessenta
        e sete") splits only where the words read as two numbers there with
        no split. A first number never ends past the longest reading from
        ``i``, so the search stops there: a run of number words with no
        joiner ("um um um") is a list, and the search stays linear."""
        plain = self._numbers(i)
        if not plain:
            return
        default = max(plain, key=lambda p: p.end).end
        for k in range(i + 1, min(default + 1, len(self.tokens) - 1)):
            if not self._number_word(k - 1):
                break
            if not self._is_word(k, self.lex.joiners):
                continue
            inner = self._inner(i, k)
            if inner and k != default:
                continue
            left = [p for p in Grammar(self.lex, self.tokens[:k], self.unsigned)._numbers(i) if p.end == k]
            right = self._numbers(k + 1)
            if not (left and right):
                continue
            longest = max(right, key=lambda p: p.end)
            yield left, longest, inner, _significant_digits(left[0].value) + _significant_digits(longest.value)

    def _inner(self, i: int, k: int) -> bool:
        """True when the joiner at ``k`` is inside a number below a thousand
        that starts at ``i`` or later: "sessenta e sete"."""
        return any(end > k + 1 for x in range(i, k) for end, _ in self.small(x))

    @staticmethod
    def _fewest_digits(splits: Iterable[tuple[list[Parse], bool, int]]) -> list[Parse] | None:
        """The first number of the split with the fewest significant digits
        across both numbers, and then the longest first number: "entre dois
        milhões e mil e quinhentos milhões" is 2000000 and 1500000000, not
        2001000 and 500000000; "dois milhões e mil e três milhões" is 2001000
        and 3000000. A split inside a number below a thousand wins only with
        fewer digits, so "between two thousand and one hundred and fifty
        thousand" is 2000 and 150000."""
        best = min(splits, key=lambda s: (s[2], s[1], -s[0][0].end), default=None)
        return None if best is None else best[0]

    def _weak_word(self, i: int) -> bool:
        """A cardinal word alone that may be another word: "sei" ("you
        are") anywhere, "neuf" ("new") when no word follows it ("un manteau
        neuf", not "neuf maisons"), hu "hat" ("takes effect") after "nem"
        and before "rám"."""
        if self.tokens[i].is_digits:
            return False
        entries = [e for e in self.lex.readings.get(self.tokens[i].norm, ())
                   if e.role in ("unit", "ten", "hundred")]
        # a hyphenated noun gives no token, so the word before it is not at the end ("hat ITF-tornán")
        at_end = not self.tokens[i].noun_after and (i + 1 == len(self.tokens) or self._is_word(i + 1, self.lex.joiners))
        joined = at_end and i + 1 < len(self.tokens) and self._number_at(i + 2)
        before = self.tokens[i - 1].norm if i > 0 else None
        after = self.tokens[i + 1].norm if i + 1 < len(self.tokens) else None
        return any(e.ambiguous or (e.weak_at_end and at_end and not (e.joined_count and joined))
                   or before in e.weak_after or after in e.weak_before for e in entries)

    def _number_at(self, i: int) -> bool:
        """Digits or a cardinal word, not an article, an ordinal or a form
        with another meaning ("egy", "első", "egyben")."""
        if i >= len(self.tokens):
            return False
        token = self.tokens[i]
        return token.is_digits or (token.norm not in self.lex.articles and token.norm not in self.lex.ambiguous_words
                                   and any(not e.ordinal for e in self.lex.readings.get(token.norm, ())))

    def _after_article(self, i: int) -> bool:
        """An ordinal article stands before ``i``, also inside a hyphenated
        word the tokenizer dropped ("cea de-a doua")."""
        if i > 0 and self._is_word(i - 1, self.lex.ordinal_articles):
            return True
        words = re.findall(r"[^\W\d_]+", self.tokens[i].gap)
        return bool(words) and words[-1].casefold() in self.lex.ordinal_articles
    def _ambiguous_cardinal(self, i: int) -> bool:
        """True when every cardinal reading of the word at ``i`` is also a
        common word that is no number: "семью" is 7 and "family"."""
        cardinal = [e for role in ("unit", "ten", "hundred") for e in self._readings(i, role)]
        return bool(cardinal) and all(e.ambiguous for e in cardinal)

    def _number_word(self, i: int) -> bool:
        token = self.tokens[i]
        return token.is_digits or token.norm in self.lex.readings or token.norm in (
            self.lex.joiners | self.lex.of_words | self.lex.decimal_markers | self.lex.articles)

    def _numbers(self, i: int) -> list[Parse]:
        if i in self._parses:
            return list(self._parses[i])
        fractions = self.fractions(i)
        found = self.digit_ordinal(i) + self.half_numbers(i) + self.ordinals(i) + fractions
        # "wis sin", "tis tlata": a particle makes the cardinal after it an ordinal
        if self._is_word(i, self.lex.ordinal_particles):
            found += [Parse(run[-1].end, _sum(run), Kind.ORDINAL, parts=_from(_run_parts(run), i))
                      for run in self.cardinals(i + 1) if not run[-1].decimal]
        for fraction in fractions:
            found += self.fraction_of_collective(fraction)
            found += self.fraction_of_scale(fraction)
        if self._is_word(i, self.lex.articles):
            for entry in self._readings(i + 1, "collective"):
                if not entry.plural:
                    found += [replace(p, ambiguous=entry.ambiguous) for p in
                              self._collective(Rational("0"), ONE, entry, i + 1, may_take_of=True,
                                               parts=_piece(Role.COUNT, i, i + 1, ONE))]
        if self.lex.bare_noun_counts_one and not self._after_vague(i):
            # "дюжина яиц", "четверть часа": the noun alone is one of it
            for entry in self._readings(i, "collective"):
                if not entry.plural:
                    found += [replace(p, ambiguous=entry.ambiguous)
                              for p in self._collective(ZERO, ONE, entry, i, may_take_of=True)]
            found += [Parse(i + 1, Rational("1", e.value), ambiguous=e.ambiguous,
                            parts=_piece(Role.DENOMINATOR, i, i + 1, Rational(e.value)))
                      for e in self._readings(i, "denominator") if not e.plural]
        # "dozena bat": the count of one after the collective
        for entry in self._readings(i, "collective"):
            if not entry.plural and self._is_word(i + 1, self.lex.one_after_noun):
                found += [replace(p, end=p.end + 1, parts=p.parts + _piece(Role.COUNT, p.end, p.end + 1, ONE))
                          for p in self._collective(Rational("0"), ONE, entry, i, may_take_of=False)
                          if p.end == i + 1]
        found += self.scale_fractions(i)
        for run in self.cardinals(i):
            # a lone homograph ("نه": nine or "no", "семью": 7 or "family",
            # "neuf" at the end: new) is a low-confidence number
            lone = run[-1].end == i + 1 and (
                self._homograph(i) or self._ambiguous_cardinal(i) or self._weak_word(i))
            found.append(Parse(run[-1].end, _sum(run), decimal=any(g.decimal for g in run), ambiguous=lone,
                               parts=_run_parts(run)))
            found += self.collective_tail(run) + self.of_tail(run) + self.half_tail(run)
            found += self.decimal_tail(run) + self.fraction_tail(run) + self.half_collective_tail(run)
            found += self.case_fraction_tail(run)
        self._parses[i] = found
        return list(found)


def _rational(value: str) -> Rational:
    """The value of a lexicon string, "12" or "3/2"."""
    numerator, _, denominator = value.partition("/")
    return Rational(numerator, denominator or "1")


def _whole(value: Rational) -> str:
    return digits.divide_whole(value.numerator, value.denominator)[0]


def _round_ten(value: str) -> bool:
    """True for 20, 30, ... 90: a ten that a unit can join."""
    return len(value) == 2 and value[1] == "0" and value != "10"


def _significant_digits(value: Rational) -> int:
    """The digits of a value without its leading and trailing zeros: a limit
    of a range is most often a round number."""
    return len(value.canonical().lstrip("-").replace(".", "").strip("0"))


def _less(a: Rational, b: Rational) -> bool:
    difference = b + -a
    return not difference.negative and not difference.is_zero()


def _ordinal_scale_value(run: tuple[Group, ...], exponent: int) -> Rational | None:
    """An ordinal scale word multiplies only the last group of its prefix
    and adds the groups before it: "six thousand two hundredth" is 6200th,
    and "one million two hundred thousandth" is 1200000th. None when the
    product does not fit below the group before it."""
    if not run:
        return ONE.scaled(exponent)
    last = run[-1].count.scaled(run[-1].exponent + exponent)
    if len(run) > 1 and len(_whole(last)) > _room(run[-2]):
        return None
    return _sum(run[:-1]) + last


def _room(group: Group) -> int:
    """How many digits the groups after ``group`` may fill: the place of the
    group and the trailing zeros of its count. "mil e quinhentos milhões"
    leaves 8, so "e seiscentos milhões" is a new number; "meio milhão", a
    count that is not whole, leaves 6, so "e duzentos mil" adds to it."""
    if not group.count.is_whole():
        return group.exponent
    whole = _whole(group.count)
    return group.exponent + len(whole) - len(whole.rstrip("0"))


def _teen(value: str) -> bool:
    """True for a digit string from ten to nineteen."""
    return len(value) == 2 and value[0] == "1"


def _above_ten(value: str) -> bool:
    """True for a digit string above ten: "avos" takes only such a
    denominator ("doze avos"; "dez avos" is ten grandparents)."""
    return len(value) > 2 or (len(value) == 2 and value != "10")


def _room_for(total: Rational, addend: str) -> bool:
    """True when ``addend`` fits in the trailing zeros of the whole ``total``
    ("vigésimo" + "primeiro", not "vigésimo" + "décimo")."""
    if total.denominator != "1":
        return False
    zeros = len(total.numerator) - len(total.numerator.rstrip("0"))
    return zeros >= len(addend)
