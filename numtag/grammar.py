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
from dataclasses import dataclass, replace

from numtag import digits
from numtag.digits import Rational
from numtag.lexicon import SCALE_ROLES, Entry, Joiner, Lexicon, TensOrder
from numtag.mention import Kind
from numtag.tokenize import Token

ZERO = Rational("0")
ONE = Rational("1")
HALF = Rational("1", "2")
# The power of ten of "mil" and "thousand": the only scale whose cardinal
# counts a larger scale noun ("mil milhões", "mil biliões", "a thousand million").
THOUSAND = 3


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


def _sum(groups: tuple[Group, ...]) -> Rational:
    total = Rational("0")
    for group in groups:
        total = total + group.count.scaled(group.exponent)
    return total


class Grammar:
    def __init__(self, lexicon: Lexicon, tokens: list[Token]):
        self.lex = lexicon
        self.tokens = tokens
        self._groups: dict[tuple[int, bool, bool], list[Group]] = {}
        self._cardinals: dict[tuple[int, bool, bool], list[tuple[Group, ...]]] = {}
        group, decimal = re.escape(lexicon.group_mark), re.escape(lexicon.decimal_mark)
        self._digit_pattern = re.compile(
            rf"-?(?:[0-9]{{1,3}}(?:{group}[0-9]{{3}})+|[0-9]+)(?:{decimal}([0-9]+))?")

    # Token access -----------------------------------------------------

    def _readings(self, i: int, role: str) -> tuple[Entry, ...]:
        if i >= len(self.tokens) or self.tokens[i].is_digits:
            return ()
        return self.lex.of(self.tokens[i].norm, role)

    def _is_word(self, i: int, words: frozenset[str]) -> bool:
        return i < len(self.tokens) and not self.tokens[i].is_digits and self.tokens[i].norm in words

    def _after_joiner(self, i: int, policy: Joiner) -> list[int]:
        """Positions where the next part may start after position ``i``."""
        joined = [i + 1] if policy != Joiner.NEVER and self._is_word(i, self.lex.joiners) else []
        return joined if policy == Joiner.REQUIRED else [i] + joined

    def _takes_multiplier(self, i: int) -> bool:
        return i < len(self.tokens) and not self.tokens[i].is_digits and any(
            e.role in SCALE_ROLES for e in self.lex.readings.get(self.tokens[i].norm, ()))

    def _agrees(self, noun: bool, plural: bool, count: Rational) -> bool:
        """Where a noun agrees with its count, a singular noun takes only a
        count below two: "um milhão", "meio milhão", "mil e um milhões"."""
        return not (noun and not plural and self.lex.scale_noun_agrees and _whole(count) not in ("0", "1"))

    def _takes_count(self, i: int, count: Rational, whole_group: bool = False) -> bool:
        """True when a multiplier at ``i`` takes ``count``: in "dois milhão"
        the "dois" stays a number. A ``whole_group`` count of a hundred or
        more is no count of "hundred": in "tusind hundrede" the thousand ends
        its group and "hundrede" is the next one."""
        scale_words = self.multipliers(i)
        if not scale_words:
            return self._takes_multiplier(i) and not (whole_group and len(_whole(count)) > 2)
        return any(self._agrees(noun, plural, count) for *_, noun, _, plural in scale_words)

    def starts_number(self, i: int) -> bool:
        if i >= len(self.tokens):
            return False
        token = self.tokens[i]
        return token.is_digits or any(
            e.role != "half" for e in self.lex.readings.get(token.norm, ()))

    def _digit_value(self, i: int) -> tuple[int, Rational, bool] | None:
        """End, value and whether it has decimals, of the digit string at
        ``i`` in the locale's marks; None when the marks do not fit. Where the
        locale groups digits with a space, "1 234 567,8" is one string."""
        token = self.tokens[i] if i < len(self.tokens) else None
        if token is None or not token.is_digits or token.suffix or token.period_ordinal:
            return None
        end, text = i + 1, self.tokens[i].text.replace("\u2212", "-")
        if text[0] in ".,":
            # a lone decimal mark (".5"): the tokenizer keeps only a listed one
            return end, Rational.from_decimal("0", text[1:]), True
        if self.lex.space_groups and re.fullmatch(r"-?[0-9]{1,3}", text):
            while end < len(self.tokens) and self._space_group(end):
                text += self.lex.group_mark + self.tokens[end].text
                end += 1
        match = self._digit_pattern.fullmatch(text)
        if not match:
            return None
        whole_text = text.split(self.lex.decimal_mark)[0] if match.group(1) else text
        whole = whole_text.lstrip("-").replace(self.lex.group_mark, "")
        value = Rational.from_decimal(whole, match.group(1) or "")
        return end, (-value if text.startswith("-") else value), bool(match.group(1))

    def _space_group(self, i: int) -> bool:
        """A group of three digits after a single space ("000" in "1 000")."""
        token = self.tokens[i]
        return (token.is_digits and not token.suffix and len(token.gap) == 1
                and re.fullmatch(rf"[0-9]{{3}}(?:{re.escape(self.lex.decimal_mark)}[0-9]+)?", token.text) is not None)

    # Below a thousand -------------------------------------------------

    def tens_units(self, i: int, nonzero: bool = False) -> list[tuple[int, str]]:
        units = [e.value for e in self._readings(i, "unit") if not (nonzero and e.value == "0")]
        found = [(i + 1, unit) for unit in units]
        for ten in self._readings(i, "ten"):
            found.append((i + 1, ten.value))
            # Only a round ten from twenty up takes a unit after it.
            if _round_ten(ten.value) and self.lex.tens_order != TensOrder.UNIT_TEN:
                for j in self._after_joiner(i + 1, self.lex.joiner_tens_units):
                    found += [(j + 1, ten.value[0] + unit.value)
                              for unit in self._readings(j, "unit") if unit.value != "0"]
        if self.lex.tens_order != TensOrder.TEN_UNIT:
            found += [(end, value) for end, value, _ in self._unit_tens(i, units, "ten")]
        return found

    def _unit_tens(self, i: int, units: list[str], role: str) -> list[tuple[int, str, Entry]]:
        """A unit, the joiner and a round ten of ``role`` after it:
        "einundzwanzig" is 21, "enogtyvende" the ordinal 21."""
        found = []
        for unit in units:
            if unit == "0":
                continue
            for j in self._after_joiner(i + 1, self.lex.joiner_unit_ten):
                found += [(j + 1, ten.value[0] + unit, ten) for ten in self._readings(j, role)
                          if _round_ten(ten.value)]
        return found

    def hundreds(self, i: int) -> list[tuple[int, str, bool]]:
        """(end, value, bound): a bound form stands only before the rest of
        the number ("cento e um", never "cento" alone)."""
        found = [(i + 1, e.value, e.bound) for e in self._readings(i, "hundred")]
        counts = self.tens_units(i, nonzero=True)
        if self._is_word(i, self.lex.articles):
            counts.append((i + 1, "1"))
        for end, count in counts:
            for multiplier in self._readings(end, "hundred_multiplier"):
                if not multiplier.plural:
                    found.append((end + 1, digits.shift(count, multiplier.exponent), False))
        return found

    def small(self, i: int, nonzero: bool = False) -> list[tuple[int, str]]:
        found = self.tens_units(i, nonzero)
        for end, hundreds, bound in self.hundreds(i):
            if not bound:
                found.append((end, hundreds))
            for j in self._after_joiner(end, self.lex.joiner_after_hundred):
                found += [(e, digits.add(hundreds, rest)) for e, rest in self.tens_units(j, nonzero=True)]
        return found

    def decimal_digits(self, i: int) -> list[tuple[int, str]]:
        """Digits after a decimal marker, one reading per end: each word
        gives its own digits ("vírgula zero cinco" is .05). Where the words
        split in more than one way, the reading with the fewest parts wins,
        so "point twenty five" is .25 and not .205."""
        if not self._is_word(i, self.lex.decimal_markers):
            return []
        best = {i + 1: (0, "")}
        for position in range(i + 1, len(self.tokens)):
            if position not in best:
                continue
            parts, written = best[position]
            for end, chunk in self.small(position):
                if end not in best or parts + 1 < best[end][0]:
                    best[end] = (parts + 1, written + chunk)
        return [(end, written) for end, (parts, written) in best.items() if parts]

    # Groups -----------------------------------------------------------

    def counts(self, i: int, first: bool) -> list[Count]:
        smalls = self.small(i)
        found = [Count(end, Rational(value)) for end, value in smalls]
        if self._is_word(i, self.lex.articles):
            found.append(Count(i + 1, ONE, needs_multiplier=True))
        if self._readings(i, "half"):
            end = i + 2 if self._is_word(i + 1, self.lex.articles) else i + 1
            found.append(Count(end, HALF, needs_multiplier=True))
        # "a half million"
        if self._is_word(i, self.lex.articles) and self._readings(i + 1, "half"):
            found.append(Count(i + 2, HALF, needs_multiplier=True))
        found += [Count(i + 1, Rational(*e.value.split("/"))) for e in self._readings(i, "fraction")]
        for end, value in smalls:
            found += [Count(e, Rational.from_decimal(value, fraction), decimal=True)
                      for e, fraction in self.decimal_digits(end)]
            # "zweieinhalb Millionen"
            if value != "0" and self._is_word(end, self.lex.and_a_half):
                found.append(Count(end + 1, Rational(value) + HALF, needs_multiplier=True))
            # "two and a half million"
            for j in self._after_joiner(end, Joiner.REQUIRED):
                k = j + 1 if self._is_word(j, self.lex.articles) else j
                if value != "0" and self._readings(k, "half"):
                    found.append(Count(k + 1, Rational(value) + HALF, needs_multiplier=True))
        if first and (read := self._digit_value(i)):
            end, value, decimal = read
            found.append(Count(end, value, decimal=decimal))
        return found

    def multipliers(self, i: int, starts: bool = False) -> list[tuple[int, int, bool, bool, bool]]:
        """(end, exponent, noun, needs_count, plural) of each multiplier at ``i``.

        A noun needs a count, and so does a plural scale word when the
        language says so. A singular noun that ``starts`` the number counts
        one before "de": "milhão de pessoas" is 1000000."""
        found = []
        for role in ("scale_numeral", "scale_noun"):
            for entry in self._readings(i, role):
                noun = role == "scale_noun"
                needs_count = noun or (entry.plural and self.lex.plural_scale_needs_count)
                if starts and noun and not entry.plural and self._is_word(i + 1, self.lex.of_words):
                    needs_count = False
                found.append((i + 1, entry.exponent, noun, needs_count, entry.plural))
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
                                   half_top=run[0].exponent if single else 0))
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
                found.append(Group(count.end, count.value, decimal=count.decimal))
            if count.value.is_zero():
                continue
            for end, exponent, noun, needs_count, plural in self.multipliers(count.end, first and not count.explicit):
                if (needs_count and not count.explicit) or (count.top and exponent <= count.top):
                    continue
                if not self._agrees(noun, plural, count.value):
                    continue
                found.append(Group(end, count.value, exponent, noun, count.decimal,
                                   count.top, count.half_top))
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
                # Nor is the first word of a count below a thousand: "um milhão
                # e vinte e cinco milhões" is 1000000 and 25000000.
                # Only a count that may follow the group: in "mil e quinhentos
                # e dois mil", "e quinhentos e dois" is not well formed after
                # "mil", so the number is 1500 and "dois mil" starts the next.
                counts = {end for end, value in self.small(j) if self._takes_multiplier(end)
                          and self._well_formed_after(last, Rational(value))}
                for group in following:
                    if compound and not group.top and self._takes_count(group.end, group.count.scaled(group.exponent), whole_group=True):
                        continue
                    if compound and group.exponent == 0 and any(end > group.end for end in counts):
                        continue
                    if group.order < last.order and len(_whole(group.count.scaled(group.exponent))) <= room:
                        frontier.append(run + (group,))
        self._cardinals[key] = found
        return found

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

    def _lone_half(self, i: int) -> int | None:
        """End of "e meia" / "and a half" / "einhalb" at ``i`` when no number
        word follows."""
        if self._is_word(i, self.lex.and_a_half) and not self.starts_number(i + 1):
            return i + 1
        for j in self._after_joiner(i, Joiner.REQUIRED):
            k = j + 1 if self._is_word(j, self.lex.articles) else j
            # "um milhão e meio quilo": the half is half a kilo
            if (self._readings(k, "half") and not self.starts_number(k + 1)
                    and not self._is_word(k + 1, self.lex.half_units)):
                return k + 1
        return None

    def collective_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        last = run[-1]
        if last.noun:
            return []
        split = max((n + 1 for n, g in enumerate(run) if g.noun), default=0)
        prefix, counted = _sum(run[:split]), _sum(run[split:])
        found = []
        for entry in self._readings(last.end, "collective"):
            found += self._collective(prefix, counted, entry, last.end, may_take_of=split == 0)
        decimal = any(g.decimal for g in run)
        return [replace(p, decimal=decimal) for p in found]

    def _collective(self, prefix: Rational, count: Rational, entry: Entry, at: int,
                    may_take_of: bool) -> list[Parse]:
        size = Rational(entry.value)
        value = prefix + count * size
        end = at + 1
        found = [Parse(end, value)]
        if (half_end := self._lone_half(end)) is not None:
            found.append(Parse(half_end, value + size * HALF))
        if entry.addend:
            for j in self._after_joiner(end, Joiner.REQUIRED):
                found += [Parse(e, value + Rational(v)) for e, v in self.small(j, nonzero=True)]
        if may_take_of:
            found += self._collective_of(value, end)
        return found

    def _collective_of(self, value: Rational, i: int) -> list[Parse]:
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
        found = [Parse(at + 1, value * Rational(e.value))
                 for e in self._readings(at, "collective") if e.plural]
        class_noun = self._is_word(at, self.lex.class_nouns)
        for noun in self._readings(at, "scale_noun"):
            if not (noun.plural or class_noun):
                continue
            scaled = value.scaled(noun.exponent)
            found += [Parse(at + 1, scaled)] + self._of(scaled, at + 1)
            for j in self._after_joiner(at + 1, Joiner.REQUIRED):
                for e, v in self.small(j, nonzero=True):
                    collectives = self._readings(e, "collective")
                    found += [Parse(e + 1, scaled + Rational(v) * Rational(c.value)) for c in collectives]
                    if not collectives and not self._takes_multiplier(e):
                        found.append(Parse(e, scaled + Rational(v)))
        return found

    def of_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"dois milhões de dúzias": de and a plural noun multiply a cardinal
        that ends in a scale noun."""
        last = run[-1]
        if not last.noun:
            return []
        return self._of(last.count.scaled(last.exponent), last.end, prefix=_sum(run[:-1]))

    def _of(self, total: Rational, i: int, prefix: Rational = ZERO) -> list[Parse]:
        """"de dúzias", "de milhões" at ``i`` multiply ``total``, the last
        group, and add ``prefix``, the groups before it: "um bilião e dois
        milhões de dúzias" is 10^12 + 2 x 10^6 x 12."""
        if not self._is_word(i, self.lex.of_words):
            return []
        at = i + 1
        found = [Parse(at + 1, prefix + total * Rational(e.value))
                 for e in self._readings(at, "collective") if e.plural]
        found += [Parse(at + 1, prefix + total.scaled(e.exponent))
                  for e in self._readings(at, "scale_noun") if e.plural]
        return found

    def half_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"um milhão e meio" adds half the noun, and "de dúzias" after it
        multiplies the whole ("um milhão e meio de dúzias"); "mil e meio" and
        "dois e meio" add a half of one."""
        last = run[-1]
        end = self._lone_half(last.end)
        if end is None or last.decimal:
            return []
        if last.noun:
            group = last.count.scaled(last.exponent) + ONE.scaled(last.unit) * HALF
            prefix = _sum(run[:-1])
            return [Parse(end, prefix + group)] + self._of(group, end, prefix=prefix)
        return [Parse(end, _sum(run) + HALF)]

    def decimal_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"um milhão vírgula cinco" is 1000000.5."""
        last = run[-1]
        if last.exponent == 0:
            return []
        return [Parse(end, _sum(run) + Rational.from_decimal("0", fraction), decimal=True)
                for end, fraction in self.decimal_digits(last.end)]

    def fraction_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"dois e um terço" is 7/3."""
        last = run[-1]
        if last.decimal:
            return []
        found = []
        for j in self._after_joiner(last.end, Joiner.REQUIRED):
            found += [replace(f, value=_sum(run) + f.value) for f in self.fractions(j)]
            # "dois mil e terço", "dois milhões e quarto"
            found += [Parse(j + 1, _sum(run) + Rational("1", e.value), ambiguous=e.ambiguous)
                      for e in self._readings(j, "denominator") if not e.plural]
        return found

    # Other numbers ----------------------------------------------------

    def fractions(self, i: int) -> list[Parse]:
        """A numerator and a denominator: "dois terços", "a third",
        "doze vinte e cinco avos", "doze avos"."""
        numerators = [(end, value) for end, value in self.small(i, nonzero=True)]
        found = [Parse(end + 1, Rational("1", value)) for end, value in numerators
                 if _above_ten(value) and self._is_word(end, self.lex.denominator_particles)]
        if self._is_word(i, self.lex.articles):
            numerators.append((i + 1, "1"))
        for end, numerator in numerators:
            for entry in self._readings(end, "denominator"):
                # "um terço", "dois terços"; "dois milésimo" is the ordinal 2000.º
                if entry.plural == (numerator == "1"):
                    continue
                found.append(Parse(end + 1, Rational(numerator, entry.value), ambiguous=entry.ambiguous))
            for after, denominator in self.small(end, nonzero=True):
                if _above_ten(denominator) and self._is_word(after, self.lex.denominator_particles):
                    found.append(Parse(after + 1, Rational(numerator, denominator)))
        return found

    def fraction_of_collective(self, fraction: Parse) -> list[Parse]:
        """"um terço de dúzia", "one third of a dozen": that part of the collective."""
        if not self._is_word(fraction.end, self.lex.fraction_of_words):
            return []
        at = fraction.end + 2 if self._is_word(fraction.end + 1, self.lex.articles) else fraction.end + 1
        return [Parse(at + 1, fraction.value * Rational(entry.value))
                for entry in self._readings(at, "collective") if not entry.plural]

    def half_collectives(self, i: int) -> list[Parse]:
        """"meia dúzia", "half a dozen", "a half dozen"."""
        found = []
        if self._readings(i, "half"):
            at = i + 2 if self._is_word(i + 1, self.lex.articles) else i + 1
            found += [Parse(at + 1, HALF * Rational(entry.value))
                      for entry in self._readings(at, "collective") if not entry.plural]
        if self._is_word(i, self.lex.articles) and self._readings(i + 1, "half"):
            found += [Parse(i + 3, HALF * Rational(entry.value))
                      for entry in self._readings(i + 2, "collective") if not entry.plural]
        return found

    def half_collective_tail(self, run: tuple[Group, ...]) -> list[Parse]:
        """"cem e meia dúzia" is 106, as "um milhão e duas dúzias" adds its
        dozens."""
        if run[-1].decimal:
            return []
        found = []
        for j in self._after_joiner(run[-1].end, Joiner.REQUIRED):
            found += [replace(p, value=_sum(run) + p.value) for p in self.half_collectives(j)]
        return found

    def half_numbers(self, i: int) -> list[Parse]:
        """"meia dúzia" and "meia dúzia de milhar", "dúzia e meia", and a
        half alone."""
        found = [Parse(i + 1, HALF, ambiguous=half.ambiguous) for half in self._readings(i, "half")]
        for parse in self.half_collectives(i):
            found += [parse] + self._collective_of(parse.value, parse.end)
        for entry in self._readings(i, "collective"):
            if not entry.plural and (end := self._lone_half(i + 1)) is not None:
                found.append(Parse(end, Rational(entry.value) * Rational("3", "2")))
        return found

    def ordinals(self, i: int) -> list[Parse]:
        """"vigésimo primeiro", "dois milésimo", "twenty-first", "two hundredth"."""
        prefixes: list[tuple[int, Rational | None, Joiner, tuple[Group, ...]]] = [(i, None, Joiner.NEVER, ())]
        prefixes += [(run[-1].end, _sum(run), self._joiner_after(run[-1]), run) for run in self.cardinals(i)
                     if not run[-1].decimal]
        found = []
        for start, prefix, policy, run in prefixes:
            positions = [start] if prefix is None or self.lex.ordinal_style == "every_word" \
                else self._after_joiner(start, policy)
            last_group_counts = len(run) > 1 and not run[-1].exponent
            for j in positions:
                found += self._ordinal_words(j, prefix, scales=j == start and not last_group_counts)
            if not last_group_counts:
                continue
            # "six thousand nine hundredth": the scale ordinal counts only the
            # last group, 6000 + 9 x 100, when it fits below the group before
            for scale in self._readings(start, "ordinal_scale"):
                count = run[-1].count.scaled(scale.exponent)
                if not scale.plural and len(_whole(count)) <= _room(run[-2]):
                    found += self._ordinal_rest(start + 1, _sum(run[:-1]) + count, scale.ambiguous)
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

    def _ordinal_words(self, j: int, prefix: Rational | None, scales: bool = True) -> list[Parse]:
        """The ordinal words at ``j`` after the cardinal ``prefix``, with the
        scale ordinals that multiply the whole prefix when ``scales``; no
        joiner stands before a scale ordinal ("two hundredth", not "two and
        hundredth")."""
        found = []
        one_is_fraction = self.lex.one_before_ordinal_scale_is_fraction
        for scale in self._readings(j, "ordinal_scale") if scales else ():
            if scale.plural or (one_is_fraction and prefix is not None and prefix.canonical() == "1"):
                continue  # "dois milésimos" and "um milésimo" are fractions
            value = (prefix or ONE).scaled(scale.exponent)
            found += self._ordinal_rest(j + 1, value, scale.ambiguous)
        words = [(j + 1, entry.value, entry) for entry in self._readings(j, "ordinal")]
        if self.lex.tens_order != TensOrder.TEN_UNIT:
            units = [e.value for e in self._readings(j, "unit")]
            words += self._unit_tens(j, units, "ordinal")
        for end, value, entry in words:
            if prefix is None:
                found += self._ordinal_rest(end, Rational(value), entry.ambiguous)
            elif self.lex.ordinal_style == "last_word" and _room_for(prefix, value) \
                    and not (len(value) == 1 and prefix.numerator.endswith("10")):
                # a unit ordinal joins no "ten": "ten third" is 10 and 3rd
                found.append(Parse(end, prefix + Rational(value), Kind.ORDINAL))
        return found

    def _ordinal_rest(self, j: int, value: Rational, ambiguous: bool) -> list[Parse]:
        """The parse so far, and in "every_word" style each smaller ordinal
        word that adds to it."""
        found = [Parse(j, value, Kind.ORDINAL, ambiguous=ambiguous)]
        if self.lex.ordinal_style == "every_word":
            for entry in self._readings(j, "ordinal"):
                if _room_for(value, entry.value):
                    found += self._ordinal_rest(j + 1, value + Rational(entry.value), False)
        return found

    def digit_ordinal(self, i: int) -> list[Parse]:
        token = self.tokens[i]
        if not (token.is_digits and (token.suffix or token.period_ordinal)) or not token.digits.isdigit():
            return []
        return [Parse(i + 1, Rational(digits.normalise(token.digits)), Kind.ORDINAL)]

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
        return self._fewest_digits(
            (left, inner, digits) for left, right, inner, digits in self._splits(i)
            if _less(left[0].value, right.value))

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
        no split."""
        plain = self._numbers(i)
        default = max(plain, key=lambda p: p.end).end if plain else None
        for k in range(i + 1, len(self.tokens)):
            if not self._number_word(k - 1):
                break
            if not self._is_word(k, self.lex.joiners):
                continue
            inner = self._inner(i, k)
            if inner and k != default:
                continue
            left = [p for p in Grammar(self.lex, self.tokens[:k])._numbers(i) if p.end == k]
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

    def _number_word(self, i: int) -> bool:
        token = self.tokens[i]
        return token.is_digits or token.norm in self.lex.readings or token.norm in (
            self.lex.joiners | self.lex.of_words | self.lex.decimal_markers | self.lex.articles)

    def _numbers(self, i: int) -> list[Parse]:
        fractions = self.fractions(i)
        found = self.digit_ordinal(i) + self.half_numbers(i) + self.ordinals(i) + fractions
        for fraction in fractions:
            found += self.fraction_of_collective(fraction)
        if self._is_word(i, self.lex.articles):
            for entry in self._readings(i + 1, "collective"):
                if not entry.plural:
                    found += [replace(p, ambiguous=entry.ambiguous) for p in
                              self._collective(Rational("0"), ONE, entry, i + 1, may_take_of=True)]
        for run in self.cardinals(i):
            found.append(Parse(run[-1].end, _sum(run), decimal=any(g.decimal for g in run)))
            found += self.collective_tail(run) + self.of_tail(run) + self.half_tail(run)
            found += self.decimal_tail(run) + self.fraction_tail(run) + self.half_collective_tail(run)
        return found


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


def _room(group: Group) -> int:
    """How many digits the groups after ``group`` may fill: the place of the
    group and the trailing zeros of its count. "mil e quinhentos milhões"
    leaves 8, so "e seiscentos milhões" is a new number; "meio milhão", a
    count that is not whole, leaves 6, so "e duzentos mil" adds to it."""
    if not group.count.is_whole():
        return group.exponent
    whole = _whole(group.count)
    return group.exponent + len(whole) - len(whole.rstrip("0"))


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
