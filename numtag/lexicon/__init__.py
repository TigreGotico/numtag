"""Load a language's number words from its JSON file.

Each entry names a word, its role and its value, with the facts the form
shows (gender, plural, ambiguous) and the source of the rule. Each setting
and word list is an object with its value and its source. A file may name a
base file in "extends"; its settings and lists then replace those of the
base, and an entry replaces the base entry with the same word and role.
"""
import json
from dataclasses import dataclass, field
from enum import Enum
from functools import cache
from pathlib import Path

from numtag.mention import Scale
from numtag.tokenize import COMPOUND_MARK

_HERE = Path(__file__).parent


class Joiner(str, Enum):
    """Where the joiner word ("e", "and") may go between two parts."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    NEVER = "never"


# Roles whose value is a digit string.
VALUE_ROLES = ("unit", "ten", "hundred", "collective", "denominator", "ordinal")
# Roles whose value is a power of ten.
SCALE_ROLES = ("hundred_multiplier", "scale_numeral", "scale_noun")


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
    # "mil e duzentos": the joiner before a last group below a hundred or a
    # round hundred; where it is required, "mil duzentos" is two numbers.
    joiner_before_last_group: Joiner
    # "dois milhões, duzentos e trinta e seis mil": a comma may follow a
    # scale word between two classes of one number.
    comma_between_classes: bool
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
    # Words written in several parts ("dètz-e-sèt", "bint'i un"): the
    # tokenizer reads each as one token.
    compounds: frozenset[str] = frozenset()

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
            "entries": list(entries.values())}


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

    def put(spec: dict, entry: Entry) -> None:
        readings.setdefault(spec["word"].casefold(), []).append(entry)

    # Ordinal scale words come last: each takes its power of ten from the
    # cardinal scale word it names.
    entries = sorted(data["entries"], key=lambda e: e["role"] == "ordinal_scale")
    for spec in entries:
        role = spec["role"]
        facts = dict(gender=spec.get("gender"), plural=spec.get("plural", False),
                     ambiguous=spec.get("ambiguous", False))
        if role in VALUE_ROLES:
            put(spec, Entry(role, spec["value"], addend=spec.get("addend", False),
                            bound=spec.get("bound", False), **facts))
        elif role in SCALE_ROLES:
            if "value" in spec:
                put(spec, Entry(role, exponent=spec["value"], **facts))
            else:
                rank = spec["rank"]
                dependent = _illion_exponent(rank, Scale.SHORT) != _illion_exponent(rank, Scale.LONG)
                put(spec, Entry(role, exponent=_illion_exponent(rank, scale),
                                scale_dependent=dependent, **facts))
        elif role == "half":
            put(spec, Entry(role, "1", **facts))
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
        joiner_before_last_group=Joiner(settings["joiner_before_last_group"]),
        comma_between_classes=settings["comma_between_classes"],
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
        compounds=frozenset(w for w in readings if COMPOUND_MARK.search(w)),
    )
