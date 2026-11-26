"""Write the writer block of fr-FR, fr-BE or fr-CH in the traditional spelling of the Académie française.

usage: python scripts/writer_fr.py fr-FR|fr-BE|fr-CH [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

variety = sys.argv[1]
LEXICON = Path(__file__).parents[1] / f"numtag/lexicon/{variety}.json"
CLDR = f"CLDR RBNF {variety.replace('-FR', '').replace('-', '_')} (common/rbnf as shipped in unicode-rbnf 2.5.1)"
ACADEMIE = ("Académie française, «Questions de langue: nombres»: the traditional spelling joins with a hyphen the "
            "numerals below one hundred and links the others with a space; \"il est également possible, en accord "
            "avec les Rectifications de l'orthographe ... de lier par un trait d'union tous les éléments qui "
            "composent le nombre\". The writer prints the traditional spelling; the reader reads both")
ACADEMIE_NOUNS = "Académie française, «Questions de langue: nombres»: \"vingt et cent varient devant millier, million, milliard\""
ACADEMIE_ORDINAL = ("Académie française, «vingt et cent»: \"Ils restent également invariables lorsqu’ils sont employés "
                    "comme adjectifs numéraux ordinaux\", so the count before an ordinal in -ième has no s: "
                    "\"quatre-vingt millionième\", \"deux cent millionième\"")
ORDINAL_2000 = ("Not checked against a quoted example: \"deux millième\" applies the traditional rule to the "
                "ordinal, as OQLF BDL 23494 says the hyphen rule \"vaut tant pour les déterminants numéraux ... que "
                "pour les adjectifs ordinaux\"")
SOURCE_CH = ("Académie française, «Questions de langue: nombres»: \"octante, qui a été supplanté par quatre-vingts et "
             "huitante – en Suisse – tant dans l'usage courant que dans l'enseignement ou les textes administratifs\"; "
             "Avanzi 2017, Français de nos régions, «Comment dit-on 80 en Belgique et en Suisse?»: in Vaud, Fribourg "
             "and Valais 77,4 to 82,4% use \"huitante\", and \"huitante est également en usage à l’école et dans "
             "l’administration\". OFS, Relevé structurel 2024, T 01.08.01.02 «Langues principales selon la grande région et le "
             "canton»: French as a main language, permanent residents aged 15 or over, up to three main languages per "
             "person: Vaud, Fribourg and Valais 969 116 against Geneva, Neuchâtel, Jura and Bern 596 172. CLDR RBNF fr_CH \"huitante\"")

UNITS = ("zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize dix-sept "
         "dix-huit dix-neuf").split()
ORDINALS = {1: "unième", 2: "deuxième", 3: "troisième", 4: "quatrième", 5: "cinquième", 6: "sixième", 7: "septième",
            8: "huitième", 9: "neuvième", 10: "dixième", 11: "onzième", 12: "douzième", 13: "treizième",
            14: "quatorzième", 15: "quinzième", 16: "seizième"}
TENS = {20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante", 60: "soixante"}
if variety != "fr-FR":
    TENS.update({70: "septante", 90: "nonante"})
if variety == "fr-CH":
    TENS[80] = "huitante"
# 10^exponent and the singular noun: the scale_noun entries of fr-FR.json, long scale.
SCALES = [(6, "million"), (9, "milliard"), (12, "billion"), (15, "billiard"), (18, "trillion")]


def R(value, text, source=None, radix=None):
    rule = {"value": str(value), "text": text + ";"}
    if radix:
        rule["radix"] = radix
    if source:
        rule["source"] = source
    return rule


def ordinal_word(word):
    """The ordinal of a final cardinal word: "trente" "trentième", "cinq" "cinquième", "neuf" "neuvième"."""
    word = word.removesuffix("s")
    if word.endswith("e"):
        word = word[:-1]
    return {"cinq": "cinqu", "neuf": "neuv"}.get(word, word) + "ième"


def tens(name, ordinal):
    """20 to 99. ``name`` is the rule set of a unit after the ten; ``ordinal`` changes the last word. The
    engine divides by powers of ten, so 70 to 79 and 90 to 99 of fr-FR each have a rule of their own."""
    last = (lambda w: "-".join(w.split("-")[:-1] + [ordinal_word(w.split("-")[-1])])) if ordinal else (lambda w: w)
    rules = []
    for value, word in TENS.items():
        rules += [R(value, last(word)), R(value + 1, f"{word} et {last('un')}"), R(value + 2, f"{word}-→%{name}→")]
    teens = UNITS[10:]
    if 70 not in TENS:  # fr-FR: soixante-dix, soixante et onze, soixante-douze, one rule each
        rules += [R(70 + i, ("soixante et " if i == 1 else "soixante-") + last(w)) for i, w in enumerate(teens)]
    if 80 not in TENS:  # quatre-vingts, quatre-vingt-un with no "et"
        rules += [R(80, last("quatre-vingts") if ordinal else "quatre-vingts"), R(81, f"quatre-vingt-→%{name}→")]
    if 90 not in TENS:
        rules += [R(90 + i, "quatre-vingt-" + last(w)) for i, w in enumerate(teens)]
    return sorted(rules, key=lambda r: int(r["value"]))


def cardinal(name, one, plural=True):
    """A cardinal rule set. ``one`` is "un" or "une"; with ``plural`` false, "vingt" and "cent" keep no plural s,
    as before "mille" ("quatre-vingt mille", "deux cent mille")."""
    units = UNITS[:]
    units[1] = one
    rules = [R("-x", "moins →→")] + [R(i, w) for i, w in enumerate(units)]
    body = tens(name, False)
    for r in body:
        r["text"] = r["text"].replace(" et un;", f" et {one};")
    if not plural and 80 not in TENS:
        body = [R(80, "quatre-vingt") if r["value"] == "80" else r for r in body]
    rules += body
    rules += [R(100, f"cent[ →{'%' + name}→]"), R(200, f"←%count← cent→%{name}-cents→")]
    rules += [R(1000, f"mille[ →%{name}→]"), R(2000, f"←%count← mille[ →%{name}→]")]
    for exponent, noun in SCALES:
        rules += [R(10 ** exponent, f"un {noun}[ →%{name}→]", ACADEMIE_NOUNS),
                  R(2 * 10 ** exponent, f"←%cardinal-m← {noun}s[ →%{name}→]")]
    cents = [R(0, "s" if plural else ""), R(1, f" =%{name}=")]
    return [(name, rules), (f"{name}-cents", cents)]


def ordinal(name, first):
    """An ordinal rule set: the cardinal with its last word in -ième, and "premier" or "première" for 1."""
    rules = [R("-x", "moins →→"), R(0, "zéroième"), R(1, first)] + [R(n, w) for n, w in ORDINALS.items() if n > 1]
    rules += [R(17, f"dix-→%{name}-unit→")]
    rules += tens(f"{name}-unit", True)
    big = [R(100, f"cent→%{name}-rest→"), R(200, f"←%count← cent→%{name}-rest→"),
           R(1000, f"mill→%{name}-mille→"), R(2000, f"←%count← mill→%{name}-mille→", ORDINAL_2000)]
    # A count whose cardinal ends in a plural s ("quatre-vingts", "deux cents") has an exact rule of its own: no s
    # before the ordinal ("quatre-vingt millionième"), the s before the noun ("quatre-vingts millions unième").
    # The radix keeps the divisor at the scale, so the count is the whole quotient.
    plural_counts = [c for c in range(2, 1000) if (c % 100 == 0 and c >= 200) or (c % 100 == 80 and 80 not in TENS)]
    for exponent, noun in SCALES:
        radix = 10 ** exponent
        big += [R(radix, f"{noun}ième"), R(radix + 1, f"un {noun} →%{name}-unit→"),
                R(2 * radix, f"←%cardinal-m← {noun}→%{name}-scale→", ACADEMIE_NOUNS, radix)]
        for c in plural_counts:
            big += [R(c * radix, f"←%count← {noun}ième", ACADEMIE_ORDINAL, radix),
                    R(c * radix + 1, f"←%cardinal-m← {noun}→%{name}-scale→", None, radix)]
    rules += big
    unit = [R(n, w) for n, w in ORDINALS.items()]
    rest = [R(0, "ième"), R(1, f" =%{name}-unit=")]
    scale = [R(0, "ième"), R(1, f"s =%{name}-unit=")]
    mille = [R(0, "ième"), R(1, f"e =%{name}-unit=")]
    inner = [r if not r["text"].endswith("ième;") or r["value"] not in {str(10 ** e) for e, _ in SCALES}
             else R(r["value"], "un " + r["text"][:-1]) for r in big]
    sets = [(name, rules), (f"{name}-unit", unit + [R(17, f"dix-→%{name}-unit→")] + tens(f"{name}-unit", True)
                            + inner),
            (f"{name}-rest", rest), (f"{name}-scale", scale), (f"{name}-mille", mille)]
    return sets


sets = (cardinal("numbering", "un") + cardinal("cardinal-m", "un") + cardinal("cardinal-f", "une")
        + cardinal("count", "un", plural=False) + ordinal("ordinal-m", "premier") + ordinal("ordinal-f", "première"))
rulesets = {}
for name, rules in sets:
    source = CLDR + f", %spellout-{name}" if "-" not in name.removeprefix("cardinal-").removeprefix("ordinal-") else \
        "a part of " + name.rsplit("-", 1)[0]
    rulesets[name] = {"source": f"{source}. {ACADEMIE}" + (f". {SOURCE_CH}" if variety == "fr-CH" else ""),
                      "rules": rules}
maximum = "9" * 24
gender = {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
          "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}]}
block = {
    "source": CLDR + ". French counts in the long scale: \"milliard\" for 10^9 and \"billion\" for 10^12. " + ACADEMIE,
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "numbering", "reason": "standard"}], "gender": gender, "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                               "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}]},
                    "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "virgule", "places": 3, "source": CLDR + ", %spellout-numbering x,x: \"←← virgule →→\"."},
    "scientific": {"times": "fois dix puissance",
                   "source": "Not checked against a grammar: the phrase of ovos-number-parser 0.31.5a2 numbers_fr.py, "
                             "\"un fois dix puissance quinze\"."},
    "fraction": {"mixed": False, "limit": 10, "single": "un {denominator}", "plural": {"s": "s", "": "s"},
                 "named": {"2": "demi", "3": "tiers", "4": "quart"}, "denominator": "{cardinal}ièmes",
                 "ruleset": "ordinal-m", "numerator": "cardinal-m",
                 "source": "OQLF, Banque de dépannage linguistique 23494, «Pluriel des fractions»: the fractions "
                           "\"sont formées d’un déterminant numéral, qui est le numérateur ( trois ), et d’un nom, qui est "
                           "le dénominateur ( cinquièmes ). Ce dernier prend la marque du pluriel comme tout autre nom\". "
                           "SILVER, not in a saved source: \"demi\", \"tiers\" and \"quart\" for 2, 3 and 4, and the "
                           "plural after \"zéro\"."},
}
splice(LEXICON, block, check="--check" in sys.argv)
