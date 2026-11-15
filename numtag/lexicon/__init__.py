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

_HERE = Path(__file__).parent


class Joiner(str, Enum):
    """Where the joiner word ("e", "and") may go between two parts."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    NEVER = "never"


# Roles whose value is a digit string. A "teen_suffix" adds its value to the
# unit before it ("dua belas" is 12).
VALUE_ROLES = ("unit", "ten", "hundred", "collective", "denominator", "ordinal", "teen_suffix")
# Roles whose value is a power of ten. A "ten_multiplier" multiplies the unit
# before it ("dua puluh" is 20).
SCALE_ROLES = ("hundred_multiplier", "scale_numeral", "scale_noun", "ten_multiplier")
# Roles with no value: a part of a word that makes the cardinal before it an
# ordinal ("ventitre|esimo", "bi|garren"), a word or part that makes the
# cardinal after it an ordinal ("ke|dua", "ke-2"), and a part that makes the
# cardinal after it a denominator ("se|per|enam belas").
MARK_ROLES = ("ordinal_ending", "ordinal_prefix", "denominator_prefix")


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
    # A ten that takes a number from ten to nineteen after it, as well as a
    # unit: "soixante-dix" is 70, "hogeita hamar" is 30.
    teens: bool = False
    # The word is read only as a piece of a longer word that the tokenizer
    # splits ("vent" in "ventuno", "se" in "seratus").
    part: bool = False
    # A denominator with one form for one and for more ("deux tiers").
    invariable: bool = False
    # An ordinal read only after an ordinal article ("a noua", not "noua
    # clădire").
    after_article: bool = False
    # A word with a common meaning that ends a phrase, as an adjective after
    # its noun ("un manteau neuf"): weak when no word follows it.
    weak_at_end: bool = False


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
    # Where the joiner may go before a half or a fraction after a whole
    # ("dua setengah", "tiga dua-pertiga", "two and a half").
    joiner_before_half: Joiner = Joiner.REQUIRED
    # Split a word that is no number word into number words ("ventitré").
    compound_words: bool = False
    # Letters that read as other letters ("ş" as "ș").
    fold: dict[str, str] = field(default_factory=dict)
    # Number words of several words, as tuples of their words ("quatre-vingts").
    phrases: frozenset[tuple[str, ...]] = frozenset()
    # "de" in "douăzeci de mii": a word between a count and its scale word.
    count_of: frozenset[str] = frozenset()
    # "bat" in "milioi bat": a word after a noun that counts one of it.
    one_after_noun: frozenset[str] = frozenset()
    # "a" in "a noua": the word before an ordinal that needs an article.
    ordinal_articles: frozenset[str] = frozenset()
    # The article follows its noun ("etxe bat"), so it is weak after a word.
    article_after_noun: bool = False
    # A fraction word after a scale word takes a part of it ("milioi erdi
    # bat" is 500000, "hiru milioi laurden" 750000).
    fraction_after_scale: bool = False

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


def exists(lang: str) -> bool:
    return (_HERE / f"{lang}.json").is_file()


@cache
def load(lang: str, scale: Scale | None = None) -> Lexicon:
    data = _read(lang)
    settings = {key: item["value"] for key, item in data["settings"].items()}
    words = {key: item["value"] for key, item in data["words"].items()}
    scale = Scale(scale or settings["scale"])
    fold = str.maketrans(settings.get("fold", {}))
    readings: dict[str, list[Entry]] = {}
    suffixes: dict[str, str | None] = {}

    def key(word: str) -> str:
        return word.casefold().translate(fold)

    def listed(name: str) -> frozenset[str]:
        return frozenset(key(w) for w in words.get(name, ()))

    def put(spec: dict, entry: Entry) -> None:
        readings.setdefault(key(spec["word"]), []).append(entry)

    # Ordinal scale words come last: each takes its power of ten from the
    # cardinal scale word it names.
    entries = sorted(data["entries"], key=lambda e: e["role"] == "ordinal_scale")
    for spec in entries:
        role = spec["role"]
        facts = dict(gender=spec.get("gender"), plural=spec.get("plural", False),
                     ambiguous=spec.get("ambiguous", False), part=spec.get("part", False))
        if role in VALUE_ROLES:
            put(spec, Entry(role, spec["value"], addend=spec.get("addend", False),
                            bound=spec.get("bound", False), teens=spec.get("teens", False),
                            invariable=spec.get("invariable", False),
                            after_article=spec.get("after_article", False),
                            weak_at_end=spec.get("weak_at_end", False), **facts))
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
        elif role in MARK_ROLES:
            put(spec, Entry(role, **facts))
        elif role == "ordinal_scale":
            cardinal = [e for e in readings[key(spec["value"])] if e.role in SCALE_ROLES]
            put(spec, Entry(role, exponent=cardinal[0].exponent,
                            scale_dependent=cardinal[0].scale_dependent,
                            after_article=spec.get("after_article", False), **facts))
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
        joiners=listed("joiner"),
        decimal_markers=listed("decimal_marker"),
        minus_words=listed("minus"),
        minus_idioms=tuple(tuple(key(p).split()) for p in words["minus_idioms"]),
        articles=listed("article_one"),
        of_words=listed("of"),
        denominator_particles=listed("denominator_particle"),
        fraction_of_words=listed("fraction_of"),
        class_nouns=listed("class_noun"),
        half_units=listed("half_unit"),
        abbreviations=listed("abbreviation"),
        lone_decimal_marks=frozenset(words["lone_decimal_mark"]),
        range_cues=frozenset(key(w) for w in words["range_cue"]),
        ordinal_suffixes=suffixes,
        joiner_before_half=Joiner(settings.get("joiner_before_half", Joiner.REQUIRED)),
        compound_words=settings.get("compound_words", False),
        fold=settings.get("fold", {}),
        phrases=frozenset(tuple(w.split("-")) for w in readings if "-" in w),
        count_of=listed("count_of"),
        one_after_noun=listed("one_after_noun"),
        ordinal_articles=listed("ordinal_article"),
        article_after_noun=settings.get("article_after_noun", False),
        fraction_after_scale=settings.get("fraction_after_scale", False),
    )
