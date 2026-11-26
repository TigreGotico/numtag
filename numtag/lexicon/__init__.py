"""Load a language's number words from its JSON file.

The file format is specified in docs/lexicon-format.md and by
lexicon.schema.json. Every file names its ``format_version``. The loader
refuses a file with a version it does not know, and a key that it does not
read, by name.

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
import hashlib
import json
from dataclasses import dataclass, field, replace
from enum import Enum
from functools import cache, cached_property
from pathlib import Path

from numtag.mention import Scale
from numtag.tokenize import COMPOUND_MARK, Script, fold

_HERE = Path(__file__).parent

FORMAT_VERSION = 2
# A version 1 file stays valid; only a version 2 file may hold a ``writer`` block.
READABLE_VERSIONS = (1, 2)
WRITER_VERSION = 2


class UnsupportedLanguageError(ValueError):
    """No lexicon reads the language. A caller can tell it apart from a bad
    ``scale``, which raises a plain ``ValueError``."""


class Joiner(str, Enum):
    """Where the joiner word ("e", "and") may go between two parts."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    NEVER = "never"


class TensOrder(str, Enum):
    """The order of a ten and a unit: "twenty-one", "einundzwanzig" and
    "خمسة وعشرون", or both ("tjueen" and "enogtjue")."""
    TEN_UNIT = "ten_unit"
    UNIT_TEN = "unit_ten"
    BOTH = "both"


# Roles whose value is a digit string; a "fraction" word has a fraction
# ("3/2"). A "teen" adds ten to the unit before it ("yksi" "toista", "ثلاثة
# عشر"); a "value_word" is a whole number on its own, also one that is not
# whole ("puolitoista" is 3/2); a unit-and-half word is its value and a half
# ("δυόμισι"); a "rational" word is a number that is no whole number
# ("полтора" is 3/2); a "teen_suffix" adds its value to the unit before it
# ("dua belas" is 12); an "article_collective" is a collective that only the
# article counts ("a couple", never "one couple").
VALUE_ROLES = ("unit", "ten", "hundred", "collective", "article_collective", "denominator", "ordinal", "fraction",
               "teen", "decimal_zero", "value_word", "unit_and_half", "rational", "teen_suffix")
# Roles whose value is a power of ten. A "ten_multiplier" counts tens
# ("kaksi" "kymmentä" is 20), as a hundred multiplier counts hundreds.
SCALE_ROLES = ("hundred_multiplier", "scale_numeral", "scale_noun", "ten_multiplier")
# Roles of the words that count a quantity of ten's powers or of things.
AMOUNT_ROLES = SCALE_ROLES + ("collective",)
# Roles of the words a cardinal is made of.
CARDINAL_ROLES = ("unit", "ten", "hundred", "teen") + SCALE_ROLES
# Roles of the parts of a compound number word where the lexicon splits by
# role: a fraction noun or a collective is no part.
COMPOUND_ROLES = ("unit", "ten", "hundred", "ordinal", "ordinal_scale", "half", "rational") + SCALE_ROLES
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
    # The form stands only before the rest of the number ("cento e um",
    # "пол" in "полмиллиона").
    bound: bool = False
    # A scale word with its count in the form: the dual "ألفان" is 2 x 10^3.
    count: str = ""
    # A plural multiplier that a count takes, in words or in digits below a
    # thousand ("מאות" in "שלוש מאות" and "3 מאות").
    counted: bool = False
    # A denominator that stands alone as this numerator over it ("ربع" is 1/4).
    numerator: str = ""
    # A denominator with one form for every numerator ("سوم" in "دو سوم").
    invariant: bool = False
    # The cardinal word that a denominator ends in when its last word takes
    # a suffix: eu "hamarren" is the cardinal "hamar" with -(r)en, so
    # "hogeita hamarren" is the denominator 30.
    cardinal: str = ""
    # A denominator that also names one part alone, with no count, no
    # article and no one after it, at the score of a homograph: eu
    # "laurden" is 1/4, and also starts the compound "final laurden".
    weak_alone: bool = False
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
    # A ten that takes only these units after it, past the joiner: the old
    # spelling "diez y seis" is 16, and "diez y uno" is no number.
    takes_units: frozenset[str] = frozenset()
    # The grammatical cases the form stands in. Every word of a cardinal
    # declines, so a ten with no nominative form takes only a unit that
    # shares a case with it: Russian "двадцати девяти" is 29, and
    # "без двадцати девять" is 20 and 9. A ten with a nominative form takes
    # any unit: the animate accusative "двадцать одного" is 21.
    case: frozenset[str] = frozenset()
    # A case form that names the parts when a count follows it: Turkish
    # "üçte bir" is one third.
    fraction_case: bool = False
    # A teen that also follows the ordinal form of its unit ("yhdes"
    # "toista" is 11th; Estonian "teine" "teist" is no number).
    ordinal_unit: bool = False
    # The cardinal word of an ordinal scale word names a number by itself
    # ("tausend", "honderd"), not only after a count ("thousand").
    alone: bool = False
    # A ten that takes a number from ten to nineteen after it, as well as a
    # unit: "soixante-dix" is 70, "hogeita hamar" is 30.
    teens: bool = False
    # The word is read only as a piece of a longer word that the tokenizer
    # splits ("vent" in "ventuno", "se" in "seratus").
    part: bool = False
    # An ordinal read only after an ordinal article ("a noua", not "noua
    # clădire").
    after_article: bool = False
    # A word with a common meaning that ends a phrase, as an adjective after
    # its noun ("un manteau neuf"): weak when no word follows it.
    weak_at_end: bool = False
    # With weak_at_end: a joiner that a number follows does not end the
    # clause ("hat és hét" lists two numbers). An adjective goes before
    # "et deux chapeaux", so fr "neuf" leaves it out.
    joined_count: bool = False
    # Words before and after which the word is weak: Hungarian "hat" is
    # also the verb "to take effect", as in "nem hat" and "hat rám".
    weak_after: frozenset[str] = frozenset()
    weak_before: frozenset[str] = frozenset()
    # An ordinal that is never the last word of a longer ordinal: French
    # "premier" and "second" ("vingt et unième", "vingt-deuxième"),
    # Italian "secondo" ("ventiduesimo"). Only a hyphen joins it to a
    # number before it: ICU 78 wrote the Catalan 22nd "vint-i-segon".
    standalone: bool = False
    # Words after which the word has only its number reading: after "les"
    # the Catalan adjective "nou" ("new") is "noves", so "a les nou" is
    # nine o'clock.
    number_after: frozenset[str] = frozenset()


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
    tens_order: TensOrder
    # The joiner between a unit and the ten after it ("und" in "einundzwanzig").
    joiner_unit_ten: Joiner
    # A unit before the ten is one written word with it: "zwei und vierzig" is two numbers.
    unit_ten_one_word: bool
    # A count of one before an ordinal scale word makes a fraction ("um milésimo").
    one_before_ordinal_scale_is_fraction: bool
    # The joiner before an ordinal word stands where it stands before the
    # cardinal word in that place, and none before a scale ordinal: "tjue og
    # tredje" is 20 and 3rd, "hundre og femte" is 105th.
    ordinal_joiner_by_place: bool
    # A unit ordinal after "ten" adds to it ("ten fifth" is 15th); where the
    # teen ordinals are words of their own, it does not ("zehn dritte").
    ten_joins_unit_ordinal: bool
    # A hundred word after a group of a hundred or more starts the next group
    # ("tusind hundrede" is 1100), as the hundred word names 100 alone.
    bare_hundred_after_scale: bool
    # A hundred or ten multiplier after a group of thousands starts the next
    # group and counts no group ("bin yüz" is 1100, not 100000).
    small_multiplier_starts_group: bool
    # A hundred multiplier takes no count of a thousand or more ("dvou
    # tisíc sta" is 2100).
    hundred_counts_below_thousand: bool
    # Number words written together as one word ("zweihundert",
    # "kaksikymmentäviisi"): the tokenizer splits the word into the chain of
    # number words it is made of.
    compound_words: bool
    # Two parts of a compound share a doubled letter ("ettusen" is "ett" and "tusen").
    compound_shared_letter: bool
    # A period after digits makes an ordinal ("am 3. Mai") when a cue shows
    # it: a word before the digits ("zum 1000. Mal"), with
    # period_ordinal_lowercase any lower-case word after it ("17. mai"), or
    # a number of at most period_ordinal_free_digits digits.
    period_ordinals: bool
    period_ordinal_lowercase: bool
    # A number of at most this many digits needs no cue ("3. Platz").
    period_ordinal_free_digits: int
    # The marks that may stand between digits and an ordinal suffix ("." in "1.º").
    ordinal_suffix_marks: frozenset[str]
    readings: dict[str, tuple[Entry, ...]]
    joiners: frozenset[str]
    decimal_markers: frozenset[str]
    minus_words: frozenset[str]
    minus_idioms: tuple[tuple[str, ...], ...]
    # "per cent" in "vint per cent": a phrase whose last word is a number
    # word but names the percent sign after a number.
    percent_phrases: tuple[tuple[str, ...], ...]
    # "ни" in "ни одного": a particle that makes the word for one after it
    # a negative pronoun, "not a single".
    negative_particles: frozenset[str]
    # "número" in "o número um": a noun that names a number, so the article
    # word after it is the number.
    number_nouns: frozenset[str]
    # fa "سه شنبه" (Tuesday): a name whose first word is a number word, and
    # that names no number.
    number_names: tuple[tuple[str, ...], ...]
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
    # "einhalb" in "zweieinhalb": a word that adds a half to the number before it.
    and_a_half: frozenset[str]
    range_cues: frozenset[str]
    # "yüzde" in "yüzde yüz": a percent word before the number, which then is the amount, never a homograph.
    percent_before: frozenset[str]
    # "zum" in "zum 1000. Mal": a word before digits that makes their period an ordinal mark.
    period_ordinal_before: frozenset[str]
    # "ein" in "Er lud mich ein.": an article that alone at the end of a
    # clause is no numeral.
    article_needs_noun: frozenset[str]
    # "do" in "um quinto do bolo": a word after an article and a word that is
    # both a denominator and an ordinal that keeps the fraction. Any other
    # word there makes the ordinal ("um quinto andar"). Empty: always the
    # fraction.
    partitives: frozenset[str]
    # "parte" in "a décima parte": a noun that makes the ordinal before it a
    # fraction.
    part_nouns: frozenset[str]
    # "hét" in "öt hét" (five weeks): a number word that, right after a sure
    # cardinal, is the noun that the cardinal counts.
    nouns_after_count: frozenset[str]
    ordinal_suffixes: dict[str, str | None] = field(default_factory=dict)
    # The letters I and İ are two letters with the lower-case forms ı and i.
    dotted_i: bool = False
    # A denominator after a numerator above one takes its plural form
    # ("dois terços"); False where it keeps one form ("két harmad").
    fraction_agreement: bool = True
    # After a decimal marker a numerator and a power-of-ten denominator
    # give the decimals ("öt egész két tized" is 5.2).
    decimal_fraction: bool = False
    # A count glued to the part word of a hundred or more multiplies it, as
    # it multiplies the scale word ("kétszázad" is 1/200, as "kétszáz" is 200).
    glued_denominators: bool = False
    # The glued part word with no number before it is one part of the
    # product ("háromszázad" is 1/300); False where it names no number.
    glued_denominator_alone: bool = False
    # The lone reading has a second meaning, the count of parts, and has the
    # score of a homograph ("háromszázad másodperc" as 3/100).
    glued_denominator_alone_ambiguous: bool = False
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
    # "um" in "um 14.30": a word before an hour and minutes written with a
    # point, which then read as a time and no number.
    clock_before: frozenset[str] = frozenset()
    # "Uhr" in "14.30 Uhr": the same, as a word after them.
    clock_after: frozenset[str] = frozenset()
    # "kl" in "kl. 14.30": a clock word that is an abbreviation, so its period
    # joins it to the digits after it. It is also a clock_before word.
    clock_abbreviation: frozenset[str] = frozenset()
    # Spanish: an hour and minutes with a point are a decimal unless a clock
    # word stands beside them; elsewhere only an hour of "0" is.
    point_decimal: bool = False
    # A word between a numerator and a denominator cardinal, as "a/b" is
    # read aloud: eu "zati" in "hiru zati lau" (3/4).
    fraction_over: frozenset[str] = frozenset()
    # "wis" in "wis sin": a word that makes the cardinal after it an ordinal.
    ordinal_particles: frozenset[str] = frozenset()
    # Values whose ordinal has a bound form for compounds: in ar "الحادي
    # عشر" is the 11th, so "الأول" (1st) starts no compound.
    bound_ordinal_values: frozenset[str] = frozenset()
    # A half after any scale word is half of that scale ("אלף וחצי" is 1500).
    half_of_scale: bool = False
    # A half right before a number names the half hour before that hour:
    # German "halb drei" is 2:30, so the half is no number of its own.
    clock_half: bool = False
    script: Script = Script()
    # "petindvajset", "pětadvacet": a unit, then the joiner as this policy
    # says, then a round ten, all parts of one compound word.
    inverted_tens: Joiner | None = None
    # A compound number word splits only into words with a role inside a
    # cardinal or an ordinal, and the joiners ("petin|dvajset" is no split).
    compound_parts_by_role: bool = False
    # "дюжина яиц": a singular collective or fraction noun alone counts one.
    bare_noun_counts_one: bool = False
    # "две целых пять десятых": after a decimal marker, a fraction whose
    # denominator is a power of ten gives the decimals.
    decimal_fractions: bool = False
    # "две цяло и пет": the joiner after a decimal marker.
    joiner_after_decimal_marker: Joiner = Joiner.NEVER
    # Marks that join letters into one word ("п'ять").
    word_apostrophes: frozenset[str] = frozenset()
    # Where the joiner may go before a half or a fraction after a whole
    # ("dua setengah", "tiga dua-pertiga", "two and a half").
    joiner_before_half: Joiner = Joiner.REQUIRED
    # The joiner between two groups stands only between a thousand and a one
    # ("mil y una"); before any other group, the parts are two numbers.
    joiner_thousand_one_only: bool = False
    # Where joiner_thousand_one_only holds, the joiner also stands between
    # the thousands and a group of hundreds ("mil y quinientos"), except
    # after a range cue, where it joins the two limits.
    joiner_thousand_hundreds: bool = False
    # A percent phrase names the percent sign with no number before it too:
    # "tanto por ciento" holds no 100.
    percent_phrase_is_no_number: bool = False
    # A plural part word that is also a plural ordinal form takes no count
    # in digits: "3 пятых класса" is three fifth-grade classes, and a
    # fraction in digits is written "3/5".
    ordinal_form_part_takes_no_digits: bool = False
    # A part word after the joiner takes an article: "six and a quarter",
    # never "six and quarter" ("forty and eighth" is 40 and 8th).
    part_after_joiner_needs_article: bool = False
    # Number words of several words, as tuples of their words ("quatre-vingts").
    phrases: frozenset[tuple[str, ...]] = frozenset()
    # "de" in "douăzeci de mii": a word between a count and its scale word.
    count_of: frozenset[str] = frozenset()
    # "bat" in "milioi bat": a word after a noun that counts one of it.
    one_after_noun: frozenset[str] = frozenset()
    # "nekoliko" in "nekoliko milijuna ljudi": a word of vague quantity. Right
    # before a scale word it takes the place of a count, so the scale word
    # names no number. Entries of the role "vague_quantifier" fill the map: the
    # folded words of each phrase, and whether the phrase is also an ordinary
    # noun or adverb.
    vague_quantifiers: dict[tuple[str, ...], bool] = field(default_factory=dict)
    # "je" in "nekoliko je tisuća": a clitic that may stand between a vague
    # quantifier and the scale word.
    vague_clitics: frozenset[str] = frozenset()
    # "a" in "a noua": the word before an ordinal that needs an article.
    ordinal_articles: frozenset[str] = frozenset()
    # The article follows its noun ("etxe bat"), so it is weak after a word.
    article_after_noun: bool = False
    # A fraction word after a scale word takes a part of it ("milioi erdi
    # bat" is 500000, "hiru milioi laurden" 750000).
    fraction_after_scale: bool = False
    # A fraction below one, with its own count, glued to the whole number
    # before it adds to it ("zweieinviertel" is 2.25).
    part_glued_to_whole: bool = False
    # A fraction before "de" and a scale noun takes that part of it ("um
    # quarto de milhão" is 250000, "a quarter of a million" the same).
    fraction_of_scale: bool = False
    # Words written in several parts ("dètz-e-sèt", "bint'i un"): the
    # tokenizer reads each as one token.
    compounds: frozenset[str] = frozenset()
    # "século" in "século XIX": a noun that marks a place in a series, so
    # the Roman numeral beside it is an ordinal.
    roman_series_nouns: frozenset[str] = frozenset()
    # "rei" in "o rei Luís I": a regnal title before a name.
    roman_titles: frozenset[str] = frozenset()
    # "CD", "MIX": a Roman numeral that is also a word or a common
    # abbreviation, which reads only after a strong cue.
    roman_words: frozenset[str] = frozenset()
    # pt "vi": a word only in lower case, so "Felipe VI" reads like any numeral.
    roman_lower_words: frozenset[str] = frozenset()
    # "I" is a pronoun: a series noun before a single letter or a numeral
    # that is also a word counts only in title case ("Part I", not "the
    # part I like").
    roman_pronoun_letters: bool = False
    # A title-case word before a numeral is a cue ("Luís XIV"), unless the
    # language writes every noun in title case ("Größe XIV").
    roman_title_case_cue: bool = True

    def of(self, word: str, role: str, parts: bool = True) -> tuple[Entry, ...]:
        """The entries of ``word`` with ``role``; with ``parts`` False, only
        those that are no piece of a longer word."""
        return (self._by_role if parts else self._whole_by_role).get((word, role), ())

    @cached_property
    def _by_role(self) -> dict[tuple[str, str], tuple[Entry, ...]]:
        return _group_by_role(self.readings, skip_parts=False)

    @cached_property
    def _whole_by_role(self) -> dict[tuple[str, str], tuple[Entry, ...]]:
        return _group_by_role(self.readings, skip_parts=True)

    @cached_property
    def number_words(self) -> frozenset[str]:
        """Every word that may be part of a number."""
        return frozenset(self.readings) | self.joiners | self.and_a_half

    @cached_property
    def compound_parts(self) -> frozenset[str]:
        """The words a compound number word splits into: with
        compound_parts_by_role, every word with a role inside a cardinal or
        an ordinal, and the joiners; otherwise every number word."""
        if not self.compound_words:
            return frozenset()
        if not self.compound_parts_by_role:
            return self.number_words
        return frozenset(w for w, entries in self.readings.items()
                         if any(e.role in COMPOUND_ROLES for e in entries)) | self.joiners

    @cached_property
    def compound_last_parts(self) -> frozenset[str]:
        """The compound parts that close a number, so they are only the last
        part of a compound: fy "fiven" is no part of "fiventweintich"."""
        return frozenset(w for w in self.compound_parts
                         if (entries := self.readings.get(w)) and all(e.final for e in entries))


def _group_by_role(readings: dict[str, tuple[Entry, ...]], skip_parts: bool) -> dict[tuple[str, str], tuple[Entry, ...]]:
    found: dict[tuple[str, str], list[Entry]] = {}
    for word, entries in readings.items():
        for entry in entries:
            if not (skip_parts and entry.part):
                found.setdefault((word, entry.role), []).append(entry)
    return {key: tuple(entries) for key, entries in found.items()}


# Settings and word lists that a lexicon may leave out, with the value each then has.
DEFAULT_SETTINGS = {
    "tens_order": TensOrder.TEN_UNIT.value,
    "joiner_unit_ten": Joiner.REQUIRED.value,
    "one_before_ordinal_scale_is_fraction": True,
    "ordinal_joiner_by_place": False,
    "ten_joins_unit_ordinal": True,
    "bare_hundred_after_scale": False,
    "small_multiplier_starts_group": False,
    "hundred_counts_below_thousand": False,
    "compound_words": False,
    "compound_shared_letter": False,
    "period_ordinals": False,
    "period_ordinal_lowercase": False,
    "period_ordinal_free_digits": 0,
    "unit_ten_one_word": False,
    "ordinal_suffix_marks": ["", "."],
    "roman_pronoun_letters": False,
    "roman_title_case_cue": True,
    "dotted_i": False,
    "fraction_agreement": True,
    "decimal_fraction": False,
    "glued_denominators": False,
    "glued_denominator_alone": False,
    "glued_denominator_alone_ambiguous": False,
    "dot_ordinal": False,
    "point_decimal": False,
    "half_of_scale": False,
    "clock_half": False,
    "compound_parts_by_role": False,
    "bare_noun_counts_one": False,
    "decimal_fractions": False,
    "joiner_after_decimal_marker": Joiner.NEVER.value,
    "joiner_before_half": Joiner.REQUIRED.value,
    "part_after_joiner_needs_article": False,
    "ordinal_form_part_takes_no_digits": False,
    "joiner_thousand_one_only": False,
    "joiner_thousand_hundreds": False,
    "percent_phrase_is_no_number": False,
    "article_after_noun": False,
    "fraction_after_scale": False,
    "part_glued_to_whole": False,
    "fraction_of_scale": False,
    "inverted_tens": None,
    "inflection_position": "every",
    "native_digits": None,
    "fold_marks": False,
    "kept_marks": "",
    "letter_folds": {},
    "word_chars": "",
    "bidi_controls": False,
    "clitic_min_rest": 1,
}
DEFAULT_WORDS = {
    "and_a_half": [],
    "period_ordinal_before": [],
    "article_needs_noun": [],
    "partitive": [],
    "part_noun": [],
    "percent_phrase": [],
    "negative_particle": [],
    "noun_after_count": [],
    "number_noun": [],
    "number_name": [],
    "percent_before": [],
    "digit_suffix_mark": [],
    "date_month": [],
    "clock_before": [],
    "clock_abbreviation": [],
    "clock_after": [],
    "ordinal_particle": [],
    "fraction_over": [],
    "word_apostrophe": [],
    "count_of": [],
    "one_after_noun": [],
    "vague_clitic": [],
    "ordinal_article": [],
    "roman_series_noun": [],
    "roman_title": [],
    "roman_word": [],
    "roman_lower_word": [],
    "ordinal_suffix_mark": [],
    "joiner_prefix": [],
    "clitic_prefix": [],
}
# Settings and word lists that every lexicon without "extends" must hold.
REQUIRED_SETTINGS = frozenset((
    "scale", "group_mark", "decimal_mark", "space_groups", "plural_scale_needs_count", "scale_noun_agrees",
    "joiner_tens_units", "joiner_after_hundred", "joiner_between_groups", "joiner_before_round_hundred",
    "joiner_before_last_group", "comma_between_classes", "ordinal_style"))
REQUIRED_WORDS = frozenset((
    "joiner", "decimal_marker", "minus", "minus_idioms", "article_one", "of", "denominator_particle",
    "fraction_of", "class_noun", "half_unit", "abbreviation", "lone_decimal_mark", "range_cue"))
SETTINGS = REQUIRED_SETTINGS | frozenset(DEFAULT_SETTINGS)
WORDS = REQUIRED_WORDS | frozenset(DEFAULT_WORDS)

TOP_KEYS = frozenset(("format_version", "extends", "settings", "words", "inflection", "entries", "writer"))
WRITER_KEYS = frozenset(("source", "rulesets", "forms", "decimal", "scientific", "fraction"))
RULESET_KEYS = frozenset(("source", "rules"))
RULE_KEYS = frozenset(("value", "radix", "text", "source"))
FORM_KEYS = frozenset(("variants", "gender", "case", "minimum", "maximum", "scale"))
VARIANT_KEYS = frozenset(("ruleset", "reason", "source"))
DECIMAL_KEYS = frozenset(("word", "places", "read", "source"))
SCIENTIFIC_KEYS = frozenset(("times", "source"))
FRACTION_KEYS = frozenset(("limit", "named", "mixed_named", "denominator", "single", "mixed", "capitalise", "plural", "ruleset", "numerator", "source"))
ITEM_KEYS = frozenset(("value", "source"))
INFLECTION_KEYS = ITEM_KEYS | {"ordinal", "fraction_case"}
NATIVE_DIGITS_KEYS = frozenset(("digits", "decimal_mark", "group_mark"))

# The keys of an entry that the loader reads, by role. Every entry holds the
# keys that name and cite it and the keys that make its forms.
_FORM_KEYS = frozenset(("word", "role", "source", "stems", "excluded_forms", "ambiguous_forms", "weak_forms",
                        "ordinal", "final", "gender", "plural", "ambiguous", "part"))
_VALUE_KEYS = _FORM_KEYS | {"value", "addend", "bound", "takes_unit", "takes_units", "case", "ordinal_unit",
                            "numerator", "weak_alone", "invariant", "cardinal", "teens", "after_article",
                            "weak_at_end", "joined_count", "weak_after", "weak_before", "standalone",
                            "number_after"}
# A denominator that names a scale word takes its value from that word.
SCALE_OF_KEYS = _FORM_KEYS | {"scale_of"}
ENTRY_KEYS = {
    **dict.fromkeys(VALUE_ROLES, _VALUE_KEYS),
    **dict.fromkeys(SCALE_ROLES, _FORM_KEYS | {"value", "rank", "count", "counted"}),
    **dict.fromkeys(MARK_ROLES, _FORM_KEYS),
    "half": _FORM_KEYS | {"bound"},
    "ordinal_scale": _FORM_KEYS | {"value", "after_article"},
    "ordinal_suffix": frozenset(("word", "role", "source", "gender")),
    "vague_quantifier": frozenset(("word", "role", "source", "ambiguous")),
}


def _refuse(lang: str, where: str, found, allowed) -> None:
    if unknown := sorted(set(found) - allowed):
        raise ValueError(f"{lang}: unknown key {', '.join(map(repr, unknown))} in {where}")


def _check(lang: str, data: dict) -> None:
    """Refuse a file with an unknown format version or a key that the loader does not read."""
    if data.get("format_version") not in READABLE_VERSIONS:
        raise ValueError(f"{lang}: format_version {data.get('format_version')!r} is unknown; "
                         f"this loader reads versions {', '.join(map(str, READABLE_VERSIONS))}")
    _refuse(lang, "the lexicon", data, TOP_KEYS)
    if "writer" in data:
        if data["format_version"] < WRITER_VERSION:
            raise ValueError(f"{lang}: a writer block needs format_version {WRITER_VERSION}")
        if data["writer"] is not None:
            _check_writer(lang, data["writer"])
        elif "extends" not in data:
            raise ValueError(f"{lang}: a null writer block drops the writer of a base, and this file has no base")
    for section, allowed in (("settings", SETTINGS), ("words", WORDS)):
        _refuse(lang, section, data.get(section, ()), allowed)
        for name, item in data.get(section, {}).items():
            _refuse(lang, f"{section} {name!r}", item, ITEM_KEYS)
    for name, item in data.get("inflection", {}).items():
        _refuse(lang, f"inflection {name!r}", item, INFLECTION_KEYS)
    if native := data.get("settings", {}).get("native_digits"):
        _refuse(lang, "setting 'native_digits'", native["value"], NATIVE_DIGITS_KEYS)
    for spec in data.get("entries", ()):
        role = spec["role"]
        allowed = SCALE_OF_KEYS if role == "denominator" and "scale_of" in spec else ENTRY_KEYS.get(role)
        if allowed and not spec.keys() <= allowed:
            _refuse(lang, f"entry {spec['word']!r} of role {role!r}", spec, allowed)


def _check_writer(lang: str, writer: dict) -> None:
    """Refuse a key of the writer block that the writer does not read, and a rule set or form that is missing."""
    _refuse(lang, "the writer block", writer, WRITER_KEYS)
    for key in ("source", "rulesets", "forms", "decimal"):
        if key not in writer:
            raise ValueError(f"{lang}: the writer block has no {key!r}")
    for name, ruleset in writer["rulesets"].items():
        _refuse(lang, f"rule set {name!r}", ruleset, RULESET_KEYS)
        for rule in ruleset["rules"]:
            _refuse(lang, f"a rule of {name!r}", rule, RULE_KEYS)
            value = rule["value"]
            if value != "-x" and not (value.isascii() and value.isdigit() and (value == "0" or value[0] != "0")):
                raise ValueError(f"{lang}: the value {value!r} of a rule of {name!r} is not '-x' or a whole number "
                                 "with no leading zero")
    forms = list(writer["forms"].items())
    for name, form in writer["forms"].items():
        for scale, sub in form.get("scale", {}).items():
            if scale not in ("short", "long") or "scale" in sub:
                raise ValueError(f"{lang}: form {name!r} has the scale {scale!r}; a scale is 'short' or 'long' "
                                 "and holds no scale")
            forms.append((f"{name} {scale}", sub))
    for name, form in forms:
        _refuse(lang, f"form {name!r}", form, FORM_KEYS)
        lists = [form["variants"], *form.get("gender", {}).values()]
        for by_case in form.get("case", {}).values():  # a list, or a list for each gender
            lists += by_case.values() if isinstance(by_case, dict) else [by_case]
        for variants in lists:
            for variant in variants:
                _refuse(lang, f"a variant of form {name!r}", variant, VARIANT_KEYS)
                if variant["ruleset"] not in writer["rulesets"]:
                    raise ValueError(f"{lang}: form {name!r} names the unknown rule set {variant['ruleset']!r}")
    _refuse(lang, "decimal", writer["decimal"], DECIMAL_KEYS)
    _refuse(lang, "scientific", writer.get("scientific", {}), SCIENTIFIC_KEYS)
    _refuse(lang, "fraction", writer.get("fraction", {}), FRACTION_KEYS)
    for key in ("ruleset", "numerator"):
        if (name := writer.get("fraction", {}).get(key)) is not None and name not in writer["rulesets"]:
            raise ValueError(f"{lang}: the fraction names the unknown rule set {name!r}")


def _read(lang: str) -> dict:
    path = _HERE / f"{lang}.json"
    if not path.is_file():
        raise UnsupportedLanguageError(f"no lexicon for language {lang!r}")
    data = json.loads(path.read_text(encoding="utf-8"))
    _check(lang, data)
    if "extends" not in data:
        return data
    base = _read(data["extends"])
    entries = {(e["word"], e["role"]): e for e in base.get("entries", [])}
    entries.update({(e["word"], e["role"]): e for e in data.get("entries", [])})
    merged = {"format_version": max(data["format_version"], base["format_version"]),
              "settings": {**base["settings"], **data.get("settings", {})},
              "words": {**base["words"], **data.get("words", {})},
              "inflection": {**base.get("inflection", {}), **data.get("inflection", {})},
              "entries": list(entries.values())}
    if "writer" in data and data["writer"] is None:
        return merged
    if writer := {**base.get("writer", {}), **data.get("writer", {})}:
        merged["writer"] = writer
    return merged


def writer_block(lang: str) -> dict | None:
    """The ``writer`` block of the lexicon ``lang`` names, or None when it has none."""
    return _read(lang).get("writer")


@cache
def revision(lang: str) -> str:
    """The sha256 of the canonical bytes of the lexicon ``lang`` names, with
    its base merged in: sorted keys, no spaces, UTF-8."""
    canonical = json.dumps(_read(lang), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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


LEXICONS = tuple(sorted(path.stem for path in _HERE.glob("*.json")))


@cache
def load(lang: str, scale: Scale | None = None) -> Lexicon:
    data = _read(lang)
    settings = {**DEFAULT_SETTINGS, **{key: item["value"] for key, item in data["settings"].items()}}
    raw_words = {**DEFAULT_WORDS, **{key: item["value"] for key, item in data["words"].items()}}
    script = _script(settings, raw_words)
    words = {key: [form for w in value for form in sorted(script.lexicon_forms(w))]
             for key, value in raw_words.items()}
    scale = Scale(scale or settings["scale"])
    readings: dict[str, list[Entry]] = {}
    suffixes: dict[str, str | None] = {}
    inflection = data.get("inflection", {})
    suffix_ends = settings["inflection_position"] == "last"

    ambiguous_words: set[str] = set()
    vague_quantifiers: dict[tuple[str, ...], bool] = {}

    def put(spec: dict, entry: Entry) -> None:
        ambiguous = {w.casefold() for w in spec.get("ambiguous_forms", [])}
        ambiguous_words.update(ambiguous)
        weak = {w.casefold() for w in spec.get("weak_forms", [])}
        for word, ordinal, final, fraction_case in _forms(spec, inflection, suffix_ends):
            reading = replace(entry, ordinal=ordinal, final=final, fraction_case=fraction_case,
                              ambiguous=entry.ambiguous or word in ambiguous)
            if weak and word not in weak:
                # "hatkor" (at six) is no verb form: the weak cues hold for "hat" only
                reading = replace(reading, weak_at_end=False, joined_count=False,
                                  weak_after=frozenset(), weak_before=frozenset())
            for form in script.lexicon_forms(word):
                readings.setdefault(fold(form), []).append(reading)

    # Ordinal scale words and denominators that name a scale word ("scale_of")
    # come last: each takes its power of ten from the cardinal scale word.
    entries = sorted(data["entries"], key=lambda e: e["role"] == "ordinal_scale" or "scale_of" in e)
    for spec in entries:
        role = spec["role"]
        facts = dict(gender=spec.get("gender"), plural=spec.get("plural", False),
                     ambiguous=spec.get("ambiguous", False), part=spec.get("part", False))
        if role == "denominator" and "scale_of" in spec:
            cardinal = [e for e in readings[fold(script.fold(spec["scale_of"]))] if e.role in SCALE_ROLES]
            put(spec, Entry(role, "1" + "0" * cardinal[0].exponent, scale_dependent=cardinal[0].scale_dependent,
                            **facts))
        elif role in VALUE_ROLES:
            put(spec, Entry(role, spec["value"], addend=spec.get("addend", False),
                            bound=spec.get("bound", False), takes_unit=spec.get("takes_unit", False),
                            takes_units=frozenset(spec.get("takes_units", ())),
                            case=frozenset(spec.get("case", ())),
                            ordinal_unit=spec.get("ordinal_unit", False), numerator=spec.get("numerator", ""),
                            weak_alone=spec.get("weak_alone", False), invariant=spec.get("invariant", False),
                            cardinal=spec.get("cardinal", ""),
                            teens=spec.get("teens", False),
                            after_article=spec.get("after_article", False),
                            weak_at_end=spec.get("weak_at_end", False), joined_count=spec.get("joined_count", False),
                            weak_after=frozenset(fold(w) for w in spec.get("weak_after", ())),
                            weak_before=frozenset(fold(w) for w in spec.get("weak_before", ())),
                            standalone=spec.get("standalone", False),
                            number_after=frozenset(fold(w) for w in spec.get("number_after", ())), **facts))
        elif role in SCALE_ROLES:
            facts.update(count=spec.get("count", ""), counted=spec.get("counted", False))
            if "value" in spec:
                put(spec, Entry(role, exponent=spec["value"], **facts))
            else:
                rank = spec["rank"]
                dependent = _illion_exponent(rank, Scale.SHORT) != _illion_exponent(rank, Scale.LONG)
                put(spec, Entry(role, exponent=_illion_exponent(rank, scale),
                                scale_dependent=dependent, **facts))
        elif role == "half":
            put(spec, Entry(role, "1", bound=spec.get("bound", False), **facts))
        elif role in MARK_ROLES:
            put(spec, Entry(role, **facts))
        elif role == "ordinal_scale":
            named = readings[fold(script.fold(spec["value"]))]
            cardinal = [e for e in named if e.role in SCALE_ROLES]
            alone = any(e.role in ("hundred", "scale_numeral") for e in named)
            put(spec, Entry(role, exponent=cardinal[0].exponent,
                            scale_dependent=cardinal[0].scale_dependent, alone=alone,
                            after_article=spec.get("after_article", False), **facts))
        elif role == "ordinal_suffix":
            suffixes[fold(spec["word"])] = spec.get("gender")
        elif role == "vague_quantifier":
            vague_quantifiers[tuple(fold(w) for w in spec["word"].split())] = spec.get("ambiguous", False)
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
        tens_order=TensOrder(settings["tens_order"]),
        joiner_unit_ten=Joiner(settings["joiner_unit_ten"]),
        unit_ten_one_word=settings["unit_ten_one_word"],
        one_before_ordinal_scale_is_fraction=settings["one_before_ordinal_scale_is_fraction"],
        ordinal_joiner_by_place=settings["ordinal_joiner_by_place"],
        ten_joins_unit_ordinal=settings["ten_joins_unit_ordinal"],
        bare_hundred_after_scale=settings["bare_hundred_after_scale"],
        small_multiplier_starts_group=settings["small_multiplier_starts_group"],
        hundred_counts_below_thousand=settings["hundred_counts_below_thousand"],
        compound_words=settings["compound_words"],
        compound_shared_letter=settings["compound_shared_letter"],
        period_ordinals=settings["period_ordinals"],
        period_ordinal_lowercase=settings["period_ordinal_lowercase"],
        period_ordinal_free_digits=settings["period_ordinal_free_digits"],
        ordinal_suffix_marks=frozenset(settings["ordinal_suffix_marks"]) | frozenset(words["ordinal_suffix_mark"]),
        readings={w: tuple(e) for w, e in readings.items()},
        joiners=frozenset(words["joiner"]),
        decimal_markers=frozenset(words["decimal_marker"]),
        minus_words=frozenset(words["minus"]),
        minus_idioms=tuple(tuple(p.split()) for p in words["minus_idioms"]),
        negative_particles=frozenset(words["negative_particle"]),
        number_nouns=frozenset(words["number_noun"]),
        number_names=tuple(tuple(fold(w) for w in p.split()) for p in words["number_name"]),
        percent_phrases=tuple(tuple(fold(w) for w in p.split()) for p in words["percent_phrase"]),
        articles=frozenset(words["article_one"]),
        of_words=frozenset(words["of"]),
        denominator_particles=frozenset(words["denominator_particle"]),
        fraction_of_words=frozenset(words["fraction_of"]),
        class_nouns=frozenset(words["class_noun"]),
        half_units=frozenset(words["half_unit"]),
        abbreviations=frozenset(words["abbreviation"]),
        lone_decimal_marks=frozenset(words["lone_decimal_mark"]),
        and_a_half=frozenset(w.casefold() for w in words["and_a_half"]),
        range_cues=frozenset(words["range_cue"]),
        percent_before=frozenset(words["percent_before"]),
        period_ordinal_before=frozenset(w.casefold() for w in words["period_ordinal_before"]),
        article_needs_noun=frozenset(words["article_needs_noun"]),
        partitives=frozenset(words["partitive"]),
        part_nouns=frozenset(words["part_noun"]),
        nouns_after_count=frozenset(words["noun_after_count"]),
        ordinal_suffixes=suffixes,
        dotted_i=settings["dotted_i"],
        fraction_agreement=settings["fraction_agreement"],
        decimal_fraction=settings["decimal_fraction"],
        glued_denominators=settings["glued_denominators"],
        glued_denominator_alone=settings["glued_denominator_alone"],
        glued_denominator_alone_ambiguous=settings["glued_denominator_alone_ambiguous"],
        dot_ordinal=settings["dot_ordinal"],
        digit_suffix_marks=frozenset(words["digit_suffix_mark"]),
        date_months=frozenset(w.casefold() for w in words["date_month"]),
        clock_before=frozenset(w.casefold() for w in (*words["clock_before"], *words["clock_abbreviation"])),
        clock_abbreviation=frozenset(w.casefold() for w in words["clock_abbreviation"]),
        point_decimal=settings["point_decimal"],
        clock_after=frozenset(w.casefold() for w in words["clock_after"]),
        ambiguous_words=frozenset(ambiguous_words),
        ordinal_particles=frozenset(words["ordinal_particle"]),
        fraction_over=frozenset(words["fraction_over"]),
        bound_ordinal_values=frozenset(e.value for es in readings.values() for e in es
                                       if e.role == "ordinal" and e.bound),
        half_of_scale=settings["half_of_scale"],
        clock_half=settings["clock_half"],
        script=script,
        inverted_tens=Joiner(settings["inverted_tens"]) if settings["inverted_tens"] else None,
        compound_parts_by_role=settings["compound_parts_by_role"],
        bare_noun_counts_one=settings["bare_noun_counts_one"],
        decimal_fractions=settings["decimal_fractions"],
        joiner_after_decimal_marker=Joiner(settings["joiner_after_decimal_marker"]),
        word_apostrophes=frozenset(words["word_apostrophe"]),
        joiner_before_half=Joiner(settings["joiner_before_half"]),
        part_after_joiner_needs_article=settings["part_after_joiner_needs_article"],
        ordinal_form_part_takes_no_digits=settings["ordinal_form_part_takes_no_digits"],
        joiner_thousand_one_only=settings["joiner_thousand_one_only"],
        joiner_thousand_hundreds=settings["joiner_thousand_hundreds"],
        percent_phrase_is_no_number=settings["percent_phrase_is_no_number"],
        phrases=frozenset(tuple(w.split("-")) for w in readings if "-" in w),
        count_of=frozenset(words["count_of"]),
        one_after_noun=frozenset(words["one_after_noun"]),
        vague_quantifiers=vague_quantifiers,
        vague_clitics=frozenset(fold(w) for w in words["vague_clitic"]),
        ordinal_articles=frozenset(words["ordinal_article"]),
        article_after_noun=settings["article_after_noun"],
        fraction_after_scale=settings["fraction_after_scale"],
        part_glued_to_whole=settings["part_glued_to_whole"],
        fraction_of_scale=settings["fraction_of_scale"],
        compounds=frozenset(w for w in readings if COMPOUND_MARK.search(w)),
        roman_series_nouns=frozenset(words["roman_series_noun"]),
        roman_titles=frozenset(words["roman_title"]),
        roman_words=frozenset(words["roman_word"]),
        roman_lower_words=frozenset(words["roman_lower_word"]),
        roman_pronoun_letters=settings["roman_pronoun_letters"],
        roman_title_case_cue=settings["roman_title_case_cue"],
    )


def _script(settings: dict, words: dict) -> Script:
    """The script settings of a lexicon; a language that sets none reads as pt and en do."""
    native = settings["native_digits"]
    digits: list[tuple[str, str]] = []
    if native:
        for run in native["digits"]:
            digits += [(char, str(n)) for n, char in enumerate(run)]
        digits += [(native["decimal_mark"], settings["decimal_mark"]), (native["group_mark"], settings["group_mark"])]
    script = Script(fold_marks=settings["fold_marks"],
                    kept_marks=settings["kept_marks"],
                    letter_folds=tuple(settings["letter_folds"].items()),
                    word_chars=settings["word_chars"],
                    bidi_controls=settings["bidi_controls"],
                    native_digits=tuple(digits),
                    clitic_min_rest=settings["clitic_min_rest"])
    return replace(script, joiner_prefixes=tuple(script.fold(p) for p in words["joiner_prefix"]),
                   clitic_prefixes=tuple(script.fold(p) for p in words["clitic_prefix"]))
