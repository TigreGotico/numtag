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
ACADEMIE_NOUNS = ("Académie française, «Questions de langue: nombres»: \"Milliard, million et millier, étant des noms, "
                  "ne sont pas concernés par cette rectification\"")
ORDINAL_2000 = ("Not checked against a quoted example: \"deux millième\" applies the traditional rule to the "
                "ordinal, as OQLF BDL 23494 says the hyphen rule \"vaut tant pour les déterminants numéraux ... que "
                "pour les adjectifs ordinaux\"")
SILVER_CH = "SILVER: no official source on \"huitante\" was reached; the form is that of CLDR RBNF fr_CH"

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


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
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
    """20 to 99. ``name`` is the rule set of a unit after the ten; ``ordinal`` changes the last word."""
    last = (lambda w: ordinal_word(w)) if ordinal else (lambda w: w)
    rules = []
    for value, word in TENS.items():
        rules += [R(value, last(word)), R(value + 1, f"{word} et {last('un')}"), R(value + 2, f"{word}-=%{name}=")]
    if 70 not in TENS:  # fr-FR: soixante-dix, soixante et onze, soixante-douze
        rules += [R(70, f"soixante-{last('dix')}"), R(71, f"soixante et {last('onze')}"), R(72, f"soixante-=%{name}-ten=")]
    if 80 not in TENS:  # quatre-vingts, quatre-vingt-un with no "et"
        rules += [R(80, last("quatre-vingts") if ordinal else "quatre-vingts"), R(81, f"quatre-vingt-=%{name}=")]
    if 90 not in TENS:
        rules += [R(90, f"quatre-vingt-{last('dix')}"), R(91, f"quatre-vingt-=%{name}-ten=")]
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
    if not plural:
        body = [R(80, "quatre-vingt") if r["value"] == "80" else r for r in body]
    rules += body
    rules += [R(100, f"cent[ →{'%' + name}→]"), R(200, f"←%count← cent→%{name}-cents→")]
    rules += [R(1000, f"mille[ →%{name}→]"), R(2000, f"←%count← mille[ →%{name}→]")]
    for exponent, noun in SCALES:
        rules += [R(10 ** exponent, f"un {noun}[ →%{name}→]", ACADEMIE_NOUNS),
                  R(2 * 10 ** exponent, f"←%cardinal-m← {noun}s[ →%{name}→]")]
    cents = [R(0, "s" if plural else ""), R(1, f" =%{name}=")]
    ten = [R(10, "dix"), R(11, f"=%{name}=")]  # the 10 to 19 after "soixante-" and "quatre-vingt-"
    return [(name, rules), (f"{name}-cents", cents), (f"{name}-ten", ten)]


def ordinal(name, first):
    """An ordinal rule set: the cardinal with its last word in -ième, and "premier" or "première" for 1."""
    rules = [R("-x", "moins →→"), R(0, "zéroième"), R(1, first)] + [R(n, w) for n, w in ORDINALS.items() if n > 1]
    rules += [R(17, f"dix-=%{name}-unit=")]
    rules += tens(f"{name}-unit", True)
    rules += [R(100, f"cent→%{name}-rest→"), R(200, f"←%count← cent→%{name}-rest→"),
              R(1000, f"mill→%{name}-mille→"), R(2000, f"←%count← mill→%{name}-mille→", ORDINAL_2000)]
    for exponent, noun in SCALES:
        rules += [R(10 ** exponent, f"{noun}→%{name}-rest→"), R(2 * 10 ** exponent, f"←%count← {noun}→%{name}-rest→")]
    unit = [R(n, w) for n, w in ORDINALS.items()]
    rest = [R(0, "ième"), R(1, f" =%{name}-unit=")]
    mille = [R(0, "ième"), R(1, f"e =%{name}-unit=")]
    sets = [(name, rules), (f"{name}-unit", unit + [R(17, f"dix-=%{name}-unit=")] + tens(f"{name}-unit", True)
                            + rules[-2 * len(SCALES) - 4:]),
            (f"{name}-rest", rest), (f"{name}-mille", mille)]
    ten = [R(10, "dixième"), R(11, f"=%{name}-unit=")]
    sets.append((f"{name}-unit-ten", ten))
    return sets


sets = (cardinal("numbering", "un") + cardinal("cardinal-m", "un") + cardinal("cardinal-f", "une")
        + cardinal("count", "un", plural=False) + ordinal("ordinal-m", "premier") + ordinal("ordinal-f", "première"))
rulesets = {}
for name, rules in sets:
    source = CLDR + f", %spellout-{name}" if "-" not in name.removeprefix("cardinal-").removeprefix("ordinal-") else \
        "a part of " + name.rsplit("-", 1)[0]
    rulesets[name] = {"source": f"{source}. {ACADEMIE}" + (f". {SILVER_CH}" if variety == "fr-CH" else ""),
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
                    "minimum": "1", "maximum": maximum},
    },
    "decimal": {"word": "virgule", "places": 3, "source": CLDR + ", %spellout-numbering x,x: \"←← virgule →→\"."},
    "scientific": {"times": "fois dix puissance",
                   "source": "Not checked against a grammar: the phrase of ovos-number-parser 0.31.5a2 numbers_fr.py, "
                             "\"un fois dix puissance quinze\"."},
    "fraction": {"mixed": False, "limit": 10, "single": "un {denominator}", "plural": {"s": "s", "": "s"},
                 "named": {"2": "demi", "3": "tiers", "4": "quart"}, "denominator": "{cardinal}ièmes",
                 "ruleset": "ordinal-m", "numerator": "cardinal-m",
                 "source": "Académie française, «Questions de langue: nombres» is not quoted for fractions. "
                           "Not checked: the numerator is a cardinal and the denominator a plural ordinal, with "
                           "\"demi\", \"tiers\" and \"quart\" for 2, 3 and 4; \"tiers\" is the same in the plural."},
}
splice(LEXICON, block, check="--check" in sys.argv)
