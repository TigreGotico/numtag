"""Write the writer block of ro from CLDR RBNF ro, DOOM 3 (as quoted by dexonline) and the scale words of the lexicon.

usage: python scripts/writer_ro.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/ro.json"
CLDR = "CLDR RBNF ro (common/rbnf/ro.xml as shipped in unicode-rbnf 2.5.1)"
DOOM = "DOOM 3 (2021), as quoted by dexonline"
DOOM_SPELLING = (DOOM + ": \"paisprezece (desp. pais-pre-/pai-spre-) num. invar.; 14/XIV\", \"șaisprezece (desp. "
                 "șais-pre-/șai-spre-) ... 16/XVI\", \"șaizeci (desp. șai-) ... 60/LX\". The writer spells ș and ț with "
                 "a comma, as DOOM 3 does; CLDR ro has the cedilla and \"patrusprezece\", \"șasezeci\"")
DOOM_GENDER = (DOOM + ": \"doi2 num. m., f. două\", \"!unu2 num. m., g.-d. unuia; f. una, g.-d. uneia\"; the headwords "
               "\"sută1 (o ~)\" and \"mie1 (o ~)\"")
DOOM_ORDINAL = (DOOM + ": \"unsprezecelea (al ~) num. m., f. a unsprezecea\", \"sutălea (al o ~) (referitor la o sută) "
                "num. m., f. a suta/a o suta\", \"mielea (al ~/al o ~) (referitor la o mie) num. m., f. a mia/a o mia\", "
                "\"miilea (al + num. + ~) ... (al două/trei etc. miilea), f. a ... mia\"")
DOOM_DOI = DOOM + ": \"locul doi, parcela doi = al doilea/a doua\""
SILVER_DE = ("SILVER: \"de\" between a count of 20 or more and the scale word (\"douăzeci de mii\") has no saved rule; "
             "DOOM 3 has the examples \"o ~ de dolari\" (sută) and \"o mie de dolari\". The count is \"de\" when its last "
             "two digits are 00 or 20 to 99")
DOOM_MILION = ("DOOM 3 (2021), via dexonline (Papers/Languages/Romance/Romanian/dexonline_milioanelea.html): "
               "\"milioanelea (al + num. + ~) (referitor la milioane) (desp. -li-oa-) num. m. (al două/trei etc. "
               "milioanelea), f. a ... milioana\"; dexonline_milionulea.html: \"milionulea (al ~/al un ~) (referitor la un "
               "milion)\"")
SILVER_ORD = ("SILVER: the ordinal of a compound and of a plural count of hundreds (\"al douăzeci și unulea\", \"al două "
              "sutelea\") follows the -lea rule of the headwords; DOOM 2 (2005) has \"douăzeci și unulea (al ~) num. m., "
              "f. a douăzeci și una\", DOOM 3 has no such entry. " + DOOM_MILION)
SILVER_PRIMUL = "SILVER: \"primul\" and \"prima\" for 1 have no saved DOOM 3 entry"

DOOM_FRACTION = (DOOM + " lists the nouns doime/doimi, jumătate, treime, pătrime/pătrimi, sfert/sferturi and "
                 "cincime/cincimi, all valid, and ranks none as the norm. The writer takes the feminine nouns "
                 "(\"jumătate\", \"treime\", \"pătrime\") so that the count agrees: \"o pătrime\", \"trei pătrimi\". "
                 "SILVER: the -ime words past 5 and the reading \"trei pe douăzeci și cinci\" for every other "
                 "denominator have no saved source")
UNITS = "zero unu doi trei patru cinci șase șapte opt nouă zece unsprezece".split()
TEENS = {12: "doisprezece", 13: "treisprezece", 14: "paisprezece", 15: "cincisprezece", 16: "șaisprezece",
         17: "șaptesprezece", 18: "optsprezece", 19: "nouăsprezece"}
TENS = {20: "douăzeci", 30: "treizeci", 40: "patruzeci", 50: "cincizeci", 60: "șaizeci", 70: "șaptezeci",
        80: "optzeci", 90: "nouăzeci"}
# 10^exponent, singular, plural: the long scale of the lexicon (milion rank 1, bilion rank 2).
SCALES = [(6, "milion", "milioane"), (9, "miliard", "miliarde"), (12, "bilion", "bilioane"),
          (15, "biliard", "biliarde"), (18, "trilion", "trilioane")]
# The masculine ordinal ("-lea") and the feminine ordinal ("-a") of each final word.
ORD_M = {"unu": "unulea", "doi": "doilea", "trei": "treilea", "patru": "patrulea", "cinci": "cincilea",
         "șase": "șaselea", "șapte": "șaptelea", "opt": "optulea", "nouă": "nouălea", "zece": "zecelea"}
ORD_F = {"una": "una", "două": "doua", "trei": "treia", "patru": "patra", "cinci": "cincea", "șase": "șasea",
         "șapte": "șaptea", "opt": "opta", "nouă": "noua", "zece": "zecea"}


# The denominator nouns: "o cincime", "trei sutimi"; the stem of 6, 7 and 9 changes ("șesime", "șeptime", "noime").
FRACTIONS = {"2": "jumătate", "3": "treime", "4": "pătrime", "5": "cincime", "6": "șesime", "7": "șeptime",
             "8": "optime", "9": "noime", "10": "zecime", "11": "unsprezecime", "12": "douăsprezecime",
             **{str(n): w + "ime" for n, w in TEENS.items() if n > 12},
             **{str(t): w[:-1] + "ime" for t, w in TENS.items()},
             "100": "sutime", "1000": "miime", "1000000": "milionime", "1000000000": "miliardime"}


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def cardinal(name, one, two):
    """A cardinal rule set. ``one`` and ``two`` are the forms of 1 and 2 in this gender, also in a compound."""
    units = UNITS[:]
    units[1], units[2] = one, two
    rules = [R("-x", "minus →→")] + [R(i, w) for i, w in enumerate(units)]
    rules += [R(12, "douăsprezece" if two == "două" else "doisprezece")]
    rules += [R(n, w) for n, w in TEENS.items() if n > 12]
    rules += [R(t, f"{w}[ și →→]") for t, w in TENS.items()]
    rules += [R(100, "o sută[ →→]", DOOM_GENDER), R(200, "←%cardinal-f← sute[ →→]"),
              R(1000, "o mie[ →→]"), R(2000, "←%count-f← mii[ →→]", SILVER_DE)]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"un {singular}[ →→]"), R(2 * 10 ** exponent, f"←%count-n← {plural}[ →→]")]
    return name, rules


def count(name, base):
    """The count before a plural scale word, with "de" after 20 to 99 and after a round hundred."""
    return [(name, [R(2, f"=%{base}="), R(20, f"=%{base}= de"), R(100, f"o sută→%{name}-rest→"),
                    R(200, f"←%cardinal-f← sute→%{name}-rest→")]),
            (f"{name}-rest", [R(0, " de"), R(1, f" =%{base}="), R(20, f" =%{base}= de")])]


def ordinal(name, article, ends, first):
    """An ordinal rule set: the article, then the cardinal with its last word in -lea ("al") or -a ("a")."""
    body = f"{name}-body"
    rules = [R(1, first, SILVER_PRIMUL), R(2, f"{article} =%{body}=", DOOM_DOI)]
    tail = [R(1, ends["unu" if "unu" in ends else "una"])] + [R(2, ends["doi" if "doi" in ends else "două"])]
    tail += [R(i, ends[w]) for i, w in enumerate(UNITS) if 3 <= i <= 10]
    m = article == "al"
    teen = (lambda w: w + ("lea" if m else "a"))  # "al unsprezecelea", "a unsprezecea"
    tail += [R(11, teen("unsprezece"), DOOM_ORDINAL), R(12, teen("doisprezece" if m else "douăsprezece"))]
    tail += [R(n, teen(w)) for n, w in TEENS.items() if n > 12]
    for t, w in TENS.items():
        tail += [R(t, w + "lea" if m else w[:-1] + "ea"), R(t + 1, f"{w} și →%{body}→", SILVER_ORD)]
    sute, mii = ("elea", "ilea") if m else ("a", "a")
    # DOOM 3 lists "al o sutălea" only, and "a suta", "al mielea", "a mia" before the forms with "o".
    tail += [R(100, "o sutălea" if m else "suta", DOOM_ORDINAL), R(101, "o sută →%" + body + "→"),
             R(200, f"←%cardinal-f← sut→%{body}-sute→"),
             R(1000, "mielea" if m else "mia"), R(1001, "o mie →%" + body + "→"),
             R(2000, f"←%count-f← mi→%{body}-mii→")]
    for exponent, singular, plural in SCALES:
        stem = plural[:-1]
        tail += [R(10 ** exponent, f"{singular}ulea" if m else f"{singular}a"),
                 R(10 ** exponent + 1, f"un {singular} →%{body}→"),
                 R(2 * 10 ** exponent, f"←%count-n← {stem}→%{body}-scale→")]
    return [(name, rules), (body, tail),
            (f"{body}-sute", [R(0, sute), R(1, f"e =%{body}=")]),
            (f"{body}-mii", [R(0, mii), R(1, f"i =%{body}=")]),
            (f"{body}-scale", [R(0, "elea" if m else "a"), R(1, f"e =%{body}=")])]


sets = ([cardinal("numbering", "unu", "doi"), cardinal("cardinal-m", "unu", "doi"),
         cardinal("cardinal-f", "una", "două"), cardinal("cardinal-n", "unu", "două")]
        + count("count-f", "cardinal-f") + count("count-n", "cardinal-n")
        + [("count-frac", [R(0, "zero"), R(1, "o"), R(2, "=%count-f=")])]
        + ordinal("ordinal-m", "al", ORD_M, "primul")
        + ordinal("ordinal-f", "a", ORD_F, "prima"))
SOURCES = {
    "numbering": CLDR + ", %spellout-numbering, with the scale words of this lexicon. " + DOOM_SPELLING,
    "cardinal-m": CLDR + ", %spellout-cardinal-masculine. " + DOOM_GENDER,
    "cardinal-f": CLDR + ", %spellout-cardinal-feminine: \"una\", \"două\", \"douăsprezece\". " + DOOM_GENDER,
    "cardinal-n": CLDR + ", %spellout-cardinal-neuter: \"unu\" and \"două\", the count of \"milioane\"",
    "count-f": SILVER_DE,
    "count-n": SILVER_DE,
    "count-frac": "the count before a feminine denominator noun: \"o treime\", \"două treimi\", \"douăzeci de treimi\". " + SILVER_DE,
    "ordinal-m": DOOM_ORDINAL + ". " + SILVER_ORD,
    "ordinal-f": DOOM_ORDINAL + ". " + SILVER_ORD,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 21  # the count before "trilioane" stops at 999
block = {
    "source": CLDR + ". Romanian counts in the long scale of this lexicon: \"miliard\" for 10^9, \"bilion\" for 10^12. "
              + DOOM + " gives \"bilion (un miliard, o mie de miliarde) (rar)\", so 10^12 is SILVER.",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "numbering", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}],
                                "neuter": [{"ruleset": "cardinal-n", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                               "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}],
                               "neuter": [{"ruleset": "ordinal-m", "reason": "standard"}]},
                    "minimum": "1", "maximum": maximum},
    },
    "decimal": {"word": "virgulă", "places": 3, "source": CLDR + ", %spellout-numbering x.x: \"←← virgulă →→\"."},
    "fraction": {"mixed": False, "limit": 10, "single": "o {denominator}",
                 "plural": {"ime": "imi", "jumătate": "jumătăți"}, "named": FRACTIONS,
                 "denominator": "{numerator} pe {cardinal}", "numerator": "count-frac", "source": DOOM_FRACTION},
    "scientific": {"times": "ori zece la puterea",
                   "source": "Not checked against a grammar: the phrase of ovos-number-parser 0.31.5a2 numbers_ro.py."},
}
splice(LEXICON, block, check="--check" in sys.argv)
