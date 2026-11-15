"""Load a language's number words from its JSON file.

Each entry names a word, its role and its value, with the facts the form
shows (gender, plural, ambiguous) and the source of the rule. Each setting
and word list is an object with its value and its source. A file may name a
base file in "extends"; its settings and lists then replace those of the
base, and an entry replaces the base entry with the same word and role.

A language that inflects its numbers lists, in "inflection", classes of
suffixes, and gives an entry "stems": each stem joins each suffix of its
classes into one more form of the entry ("kahde" and "lle" make "kahdelle").
A class may mark its forms as ordinal or as naming the parts of a fraction
("fraction_case": "üç" and "te" make "üçte", as in "üçte bir").
"""
import json
from dataclasses import dataclass, field, replace
from enum import Enum
from functools import cache
from pathlib import Path

from numtag.mention import Scale

_HERE = Path(__file__).parent


class Joiner(str, Enum):
    """Where the joiner word ("e", "and") may go between two parts."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    NEVER = "never"


# Roles whose value is a digit string. A "teen" adds ten to the unit before
# it in the same word ("yksi" "toista"); a "value_word" is a whole number on
# its own, also one that is not whole ("puolitoista" is 3/2).
VALUE_ROLES = ("unit", "ten", "hundred", "collective", "denominator", "ordinal", "teen", "value_word")
# Roles whose value is a power of ten. A "ten_multiplier" counts tens
# ("kaksi" "kymmentä" is 20), as a hundred multiplier counts hundreds.
SCALE_ROLES = ("hundred_multiplier", "scale_numeral", "scale_noun", "ten_multiplier")
# Roles of the words a cardinal is made of.
CARDINAL_ROLES = ("unit", "ten", "hundred", "teen") + SCALE_ROLES


@dataclass(frozen=True)
class Entry:
    """One reading of a word."""
    role: str
    value: str = ""
    exponent: int = 0
    gender: str | None = None
    plural: bool = False
    # The word has a common meaning that is no number ("segundo", "quarto").
    ambiguous: bool = False
    # A cardinal may follow the collective after the joiner ("four score and seven").
    addend: bool = False
    # The form stands only before the rest of the number ("cento e um").
    bound: bool = False
    # The power of ten differs between the long and the short scale ("bilião").
    scale_dependent: bool = False
    # The word names a place in a sequence ("viides", "beşinci"): a number
    # whose last word is ordinal is an ordinal.
    ordinal: bool = False
    # A case ending or a suffix closes the number ("beşte", "ötöt"): no
    # word of the number follows the form.
    final: bool = False
    # A ten that takes a unit after it although it is not a round ten from
    # twenty up ("on beş", "tizenöt").
    takes_unit: bool = False
    # A case form that names the parts when a count follows it: Turkish
    # "üçte bir" is one third.
    fraction_case: bool = False
    # A teen that also follows the ordinal form of its unit ("yhdes"
    # "toista" is 11th; Estonian "teine" "teist" is no number).
    ordinal_unit: bool = False


@dataclass(frozen=True)
class Lexicon:
    lang: str
    scale: Scale
    group_mark: str
    decimal_mark: str
    # Digits may also be grouped by a space ("1 000 000").
    space_groups: bool
    plural_scale_needs_count: bool
    scale_noun_agrees: bool
    joiner_tens_units: Joiner
    joiner_after_hundred: Joiner
    joiner_between_groups: Joiner
    # "mil e quinhentos": a round hundred may follow the joiner after a thousand.
    joiner_before_round_hundred: bool
    # "every_word": "vigésimo primeiro"; "last_word": "twenty-first".
    ordinal_style: str
    readings: dict[str, tuple[Entry, ...]]
    joiners: frozenset[str]
    decimal_markers: frozenset[str]
    minus_words: frozenset[str]
    minus_idioms: tuple[tuple[str, ...], ...]
    articles: frozenset[str]
    of_words: frozenset[str]
    denominator_particles: frozenset[str]
    # "um terço de dúzia": the word between a fraction and a collective.
    fraction_of_words: frozenset[str]
    # "milhar" in "duas dezenas de milhar": a singular noun that names a class.
    class_nouns: frozenset[str]
    # "quilo" in "meio quilo": a unit that a half before it halves.
    half_units: frozenset[str]
    # "dez" in "3 dez. 2025": a word that a period makes an abbreviation.
    abbreviations: frozenset[str]
    # "." in ".5": a mark that makes the digits after it decimals.
    lone_decimal_marks: frozenset[str]
    range_cues: frozenset[str]
    ordinal_suffixes: dict[str, str | None] = field(default_factory=dict)
    # A word with no space between its numbers ("kaksikymmentäviisi") is
    # read as the chain of number words it is made of.
    compound_words: bool = False
    # The letters I and İ are two letters with the lower-case forms ı and i.
    dotted_i: bool = False
    # A denominator after a numerator above one takes its plural form
    # ("dois terços"); False where it keeps one form ("két harmad").
    fraction_agreement: bool = True
    # After a decimal marker a numerator and a power-of-ten denominator
    # give the decimals ("öt egész két tized" is 5.2).
    decimal_fraction: bool = False
    # A period right after a digit string makes it an ordinal when a
    # lower-case word or a digit follows ("a 2. emelet").
    dot_ordinal: bool = False
    # Marks that glue a case ending to a digit string ("5-öt", "5'te").
    digit_suffix_marks: frozenset[str] = frozenset()
    # Month names before which the period after digits ends the year of a
    # date, not an ordinal ("2008. február").
    date_months: frozenset[str] = frozenset()
    # Every form an entry lists as having a common meaning that is no
    # number, also a number written as one word ("üksteist", each other).
    ambiguous_words: frozenset[str] = frozenset()

    def of(self, word: str, role: str) -> tuple[Entry, ...]:
        return tuple(e for e in self.readings.get(word, ()) if e.role == role)


def _read(lang: str) -> dict:
    path = _HERE / f"{lang}.json"
    if not path.is_file():
        raise ValueError(f"no lexicon for language {lang!r}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if "extends" not in data:
        return data
    base = _read(data["extends"])
    entries = {(e["word"], e["role"]): e for e in base.get("entries", [])}
    entries.update({(e["word"], e["role"]): e for e in data.get("entries", [])})
    return {"settings": {**base["settings"], **data.get("settings", {})},
            "words": {**base["words"], **data.get("words", {})},
            "inflection": {**base.get("inflection", {}), **data.get("inflection", {})},
            "entries": list(entries.values())}


def _forms(spec: dict, inflection: dict, suffix_ends: bool) -> list[tuple[str, bool, bool, bool]]:
    """(word, ordinal, final, fraction_case) of every form of an entry: the
    word itself, and each stem joined to each suffix of its classes. A
    suffix closes the number where the language puts case endings only on
    the last word."""
    ordinal, final = spec.get("ordinal", False), spec.get("final", False)
    forms = {spec["word"].casefold(): (ordinal, final, False)}
    for stem, classes in spec.get("stems", {}).items():
        for name in classes:
            suffixes = inflection[name]
            for suffix in suffixes["value"]:
                forms.setdefault((stem + suffix).casefold(), (
                    ordinal or suffixes.get("ordinal", False), final or (suffix_ends and suffix != ""),
                    suffixes.get("fraction_case", False)))
    excluded = {w.casefold() for w in spec.get("excluded_forms", [])}
    return [(word, *flags) for word, flags in forms.items() if word not in excluded]


def _illion_exponent(rank: int, scale: Scale) -> int:
    """The power of ten of the rank-th "-illion": 10**(3n+3) short, 10**(6n) long."""
    return 3 * rank + 3 if scale == Scale.SHORT else 6 * rank


@cache
def load(lang: str, scale: Scale | None = None) -> Lexicon:
    data = _read(lang)
    settings = {key: item["value"] for key, item in data["settings"].items()}
    words = {key: item["value"] for key, item in data["words"].items()}
    scale = Scale(scale or settings["scale"])
    readings: dict[str, list[Entry]] = {}
    suffixes: dict[str, str | None] = {}
    inflection = data.get("inflection", {})
    suffix_ends = settings.get("inflection_position", "every") == "last"

    ambiguous_words: set[str] = set()

    def put(spec: dict, entry: Entry) -> None:
        ambiguous = {w.casefold() for w in spec.get("ambiguous_forms", [])}
        ambiguous_words.update(ambiguous)
        for word, ordinal, final, fraction_case in _forms(spec, inflection, suffix_ends):
            readings.setdefault(word, []).append(replace(
                entry, ordinal=ordinal, final=final, fraction_case=fraction_case,
                ambiguous=entry.ambiguous or word in ambiguous))

    # Ordinal scale words come last: each takes its power of ten from the
    # cardinal scale word it names.
    entries = sorted(data["entries"], key=lambda e: e["role"] == "ordinal_scale")
    for spec in entries:
        role = spec["role"]
        facts = dict(gender=spec.get("gender"), plural=spec.get("plural", False),
                     ambiguous=spec.get("ambiguous", False))
        if role in VALUE_ROLES:
            put(spec, Entry(role, spec["value"], addend=spec.get("addend", False),
                            bound=spec.get("bound", False), takes_unit=spec.get("takes_unit", False),
                            ordinal_unit=spec.get("ordinal_unit", False), **facts))
        elif role in SCALE_ROLES:
            if "value" in spec:
                put(spec, Entry(role, exponent=spec["value"], **facts))
            else:
                rank = spec["rank"]
                dependent = _illion_exponent(rank, Scale.SHORT) != _illion_exponent(rank, Scale.LONG)
                put(spec, Entry(role, exponent=_illion_exponent(rank, scale),
                                scale_dependent=dependent, **facts))
        elif role == "half":
            put(spec, Entry(role, "1", bound=spec.get("bound", False), **facts))
        elif role == "ordinal_scale":
            cardinal = [e for e in readings[spec["value"]] if e.role in SCALE_ROLES]
            put(spec, Entry(role, exponent=cardinal[0].exponent,
                            scale_dependent=cardinal[0].scale_dependent, **facts))
        elif role == "ordinal_suffix":
            suffixes[spec["word"].casefold()] = spec.get("gender")
        else:
            raise ValueError(f"{lang}: unknown role {role!r} for {spec['word']!r}")

    return Lexicon(
        lang=lang, scale=scale,
        group_mark=settings["group_mark"], decimal_mark=settings["decimal_mark"],
        space_groups=settings["space_groups"],
        plural_scale_needs_count=settings["plural_scale_needs_count"],
        scale_noun_agrees=settings["scale_noun_agrees"],
        joiner_tens_units=Joiner(settings["joiner_tens_units"]),
        joiner_after_hundred=Joiner(settings["joiner_after_hundred"]),
        joiner_between_groups=Joiner(settings["joiner_between_groups"]),
        joiner_before_round_hundred=settings["joiner_before_round_hundred"],
        ordinal_style=settings["ordinal_style"],
        readings={w: tuple(e) for w, e in readings.items()},
        joiners=frozenset(words["joiner"]),
        decimal_markers=frozenset(words["decimal_marker"]),
        minus_words=frozenset(words["minus"]),
        minus_idioms=tuple(tuple(p.split()) for p in words["minus_idioms"]),
        articles=frozenset(words["article_one"]),
        of_words=frozenset(words["of"]),
        denominator_particles=frozenset(words["denominator_particle"]),
        fraction_of_words=frozenset(words["fraction_of"]),
        class_nouns=frozenset(words["class_noun"]),
        half_units=frozenset(words["half_unit"]),
        abbreviations=frozenset(words["abbreviation"]),
        lone_decimal_marks=frozenset(words["lone_decimal_mark"]),
        range_cues=frozenset(words["range_cue"]),
        ordinal_suffixes=suffixes,
        compound_words=settings.get("compound_words", False),
        dotted_i=settings.get("dotted_i", False),
        fraction_agreement=settings.get("fraction_agreement", True),
        decimal_fraction=settings.get("decimal_fraction", False),
        dot_ordinal=settings.get("dot_ordinal", False),
        digit_suffix_marks=frozenset(words.get("digit_suffix_mark", [])),
        date_months=frozenset(w.casefold() for w in words.get("date_month", [])),
        ambiguous_words=frozenset(ambiguous_words),
    )
