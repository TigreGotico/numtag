"""Write the writer block of cs from the Internetová jazyková příručka (ÚJČ AV ČR), CLDR RBNF cs and the scale
words of the lexicon.

usage: python scripts/writer_cs.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/cs.json"
CLDR = "CLDR RBNF cs (common/rbnf/cs.xml as shipped in unicode-rbnf 2.5.1)"
IJP = ("Internetová jazyková příručka (ÚJČ AV ČR), «Členění čísel, víceslovné číslovkové výrazy» "
       "(Papers/Languages/Slavic/ijc_prirucka_791_viceslovne_cislovkove_vyrazy.html)")
WORDS = (IJP + ": \"píšeme každé slovo zvlášť, např. dvacet jedna, padesát čtyři, devět set, dva tisíce (jedno) sto "
         "šedesát osm, dva tisíce dvě stě třicet jedna, jeden milion tři sta tisíc sedm set osmdesát tři\"")
ORDINAL = IJP + ": \"dvacátý pátý, stý padesátý, čtyřstý sedmdesátý osmý, tisící devítistý padesátý šestý\""
SCALE = (CLDR + ", %spellout-cardinal-masculine: \"2000: ←%spellout-cardinal-masculine← "
         "$(cardinal,one{tisíc}few{tisíce}other{tisíc})$\", \"2000000: … milióny\", \"5000000: … miliónů\"; the "
         "spelling \"milion\" of " + IJP + " (\"jeden milion tři sta tisíc\")")
COUNT = (IJP + ": \"0,1 – nula/žádná celá jedna (desetina)\", \"5,1 – pět celých jedna (desetina)\": a number "
         "with no counted noun reads 1 as \"jedna\"")
SILVER_ORD = ("SILVER: the joined count of a round scale word (\"dvoutisící\", \"třítisící\", \"dvoumiliontý\") by the "
              "pattern of \"čtyřstý\", \"devítistý\" in " + IJP + "; no saved example")
SILVER_BIG = ("SILVER: a count of 10 or more before a scale word stays a cardinal and only the last word is ordinal "
              "(\"dvacet pět tisící\", \"dvacet pět tisíc první\"); no saved example of a joined form")
SILVER_PART = ("SILVER: a part from 11 to 99 is one word, with the units first and \"a\" as in \"pětadvacátý\" of "
               "the Internetová jazyková příručka (\"jedenáctina\", \"pětadvacetina\"); another part above 99 is the ordinal "
               "(\"jedna stá první\"); no saved example")
FRACTION = ("Internetová jazyková příručka (ÚJČ AV ČR), «Členění čísel»: \"1000,05 – tisíc celých pět setin\", "
            "\"0,1 – nula celá jedna (desetina)\", \"0,2 – nula celá dvě (desetiny)\", \"0,5 – nula celá pět (desetin)\": "
            "the part is \"-ina\" after 1, \"-iny\" after 2 to 4 and \"-in\" after 5 or more")

UNITS = ("nula jedna dva tři čtyři pět šest sedm osm devět deset jedenáct dvanáct třináct čtrnáct patnáct šestnáct "
         "sedmnáct osmnáct devatenáct").split()
TENS = {20: "dvacet", 30: "třicet", 40: "čtyřicet", 50: "padesát", 60: "šedesát", 70: "sedmdesát", 80: "osmdesát",
        90: "devadesát"}
HUNDREDS = {100: "sto", 200: "dvě stě", 300: "tři sta", 400: "čtyři sta", 500: "pět set", 600: "šest set",
            700: "sedm set", 800: "osm set", 900: "devět set"}
FIRST = ("nultý první druhý třetí čtvrtý pátý šestý sedmý osmý devátý desátý jedenáctý dvanáctý třináctý čtrnáctý "
         "patnáctý šestnáctý sedmnáctý osmnáctý devatenáctý").split()
TENTHS = {20: "dvacátý", 30: "třicátý", 40: "čtyřicátý", 50: "padesátý", 60: "šedesátý", 70: "sedmdesátý",
          80: "osmdesátý", 90: "devadesátý"}
PREFIX = {2: "dvou", 3: "tří", 4: "čtyř", 5: "pěti", 6: "šesti", 7: "sedmi", 8: "osmi", 9: "devíti"}
HUNDREDTHS = {100: "stý", **{k * 100: p + "stý" for k, p in PREFIX.items()}}
# 10^exponent, singular, few (after 2-4), other, ordinal: the scale words of cs.json (long scale).
SCALES = [(3, "tisíc", "tisíce", "tisíc", "tisící"), (6, "milion", "miliony", "milionů", "miliontý"),
          (9, "miliarda", "miliardy", "miliard", "miliardtý"), (12, "bilion", "biliony", "bilionů", "biliontý"),
          (15, "biliarda", "biliardy", "biliard", "biliardtý")]
GENDER = {"m": ("jeden", "dva"), "f": ("jedna", "dvě"), "n": ("jedno", "dvě")}
PART = {2: "polovin", 3: "třetin", 4: "čtvrtin", 5: "pětin", 6: "šestin", 7: "sedmin", 8: "osmin", 9: "devítin",
        10: "desetin", 100: "setin", 1000: "tisícin", 10 ** 6: "miliontin"}


def R(value, text, source=None, round_text=None):
    rule = {"value": str(value), "text": text + ";"}
    if round_text:
        rule["round"] = round_text + ";"
    if source:
        rule["source"] = source
    return rule


def tail(g):
    """1 to the maximum inside a number: "jedna" for 1 ("dvacet jedna"), the gender form of 2."""
    rules = [R(1, "jedna", WORDS), R(2, GENDER[g][1])] + [R(i, w) for i, w in enumerate(UNITS) if i > 2]
    rules += [R(t, f"{w}[ →→]") for t, w in TENS.items()] + [R(h, f"{w}[ →→]") for h, w in HUNDREDS.items()]
    for exponent, singular, *_ in SCALES:
        one = singular if exponent == 3 else ("jeden " if singular.endswith("n") else "jedna ") + singular
        rules += [R(10 ** exponent, f"{one}[ →→]"), R(2 * 10 ** exponent, f"←%sc-{singular}←[ →→]")]
    return f"tail-{g}", rules


def cardinal(g):
    one = "jedna" if g == "c" else GENDER[g][0]
    return f"cardinal-{g}", [R("-x", "minus →→"), R(0, "nula"), R(1, one, COUNT if g == "c" else None),
                             R(2, f"=%tail-{'m' if g == 'c' else g}=")]


def scale_count(singular, few, other):
    """The count of a scale word and the word: "dva tisíce", "pět tisíc", "dvacet dva tisíce"."""
    female = singular.endswith("a")
    rules = [R(0, other), R(1, f"jedna {other}"), R(2, f"={'%tail-f' if female else '%tail-m'}= {few}"),
             R(5, f"=%tail-m= {other}")]
    rules += [R(t, f"{w} →→") for t, w in TENS.items()] + [R(h, f"{w} →→") for h, w in HUNDREDS.items()]
    return f"sc-{singular}", rules


def form(word, g):
    """The ordinal of the gender: a hard "-ý" takes "-á" (f) and "-é" (n); a soft "-í" stays."""
    if g == "m" or word.endswith("í"):
        return word
    return word[:-1] + ("á" if g == "f" else "é")


def ordinal(g):
    name = f"ordinal-{g}"
    rules = [R("-x", "minus →→")] + [R(i, form(w, g), ORDINAL if i == 1 else None) for i, w in enumerate(FIRST)]
    rules += [R(t, f"{form(w, g)}[ →→]") for t, w in TENTHS.items()]
    rules += [R(h, f"{form(w, g)}[ →→]") for h, w in HUNDREDTHS.items()]
    for exponent, singular, _, _, ordinal_word in SCALES:
        if exponent > 3:  # SILVER_BIG: with a rest, the scale word stays a cardinal
            one = ("jeden " if singular.endswith("n") else "jedna ") + singular
            rules += [R(10 ** exponent, f"{one} →→", None, form(ordinal_word, g)),
                      R(2 * 10 ** exponent, f"←%sc-{singular}← →→", None, f"←%prefix←{form(ordinal_word, g)}"),
                      dict(R(10 * 10 ** exponent, f"←%sc-{singular}← →→", None, f"←%tail-m← {form(ordinal_word, g)}"),
                           radix=1000)]
            continue
        rules += [R(10 ** exponent, f"{form(ordinal_word, g)}[ →→]"),
                  R(2 * 10 ** exponent, f"←%prefix←{form(ordinal_word, g)}[ →→]", SILVER_ORD if exponent == 3 else None),
                  dict(R(10 * 10 ** exponent, f"←%sc-{singular}← →→", SILVER_BIG if exponent == 3 else None,
                         f"←%tail-m← {form(ordinal_word, g)}"), radix=1000)]
    return name, rules


def prefix():
    return "prefix", [R(1, "jedno")] + [R(k, w) for k, w in PREFIX.items()]


JOINED = {1: "jedn", 2: "dva", 3: "tři", 4: "čtyři", 5: "pět", 6: "šest", 7: "sedm", 8: "osm", 9: "devět"}


def part_words(ending):
    """value -> the word of a part: "třetina", "jedenáctina", "pětadvacetina"."""
    words = {v: stem + ending for v, stem in PART.items() if v <= 10}
    words.update({i: f"{w}in{ending}" for i, w in enumerate(UNITS) if 11 <= i})
    for t, w in TENS.items():
        words[t] = f"{w}in{ending}"
        words.update({t + u: f"{unit}a{w}in{ending}" for u, unit in JOINED.items()})
    return words


def part(name, ending, g):
    """The word of a part; above 99 the round 100, 1000 and 10^6, else the ordinal of the gender."""
    rules = [R(v, w, FRACTION if v == 3 else None) for v, w in part_words(ending).items()]
    rules += [R(v, f"=%ordinal-{g}=", SILVER_PART if v == 100 else None, PART[v] + ending) for v in (100, 1000, 10 ** 6)]
    rules += [R(200, f"=%ordinal-{g}="), R(2000, f"=%ordinal-{g}="), R(2 * 10 ** 6, f"=%ordinal-{g}=")]
    return name, sorted(rules, key=lambda rule: int(rule["value"]))


sets = ([tail(g) for g in GENDER] + [cardinal(g) for g in (*GENDER, "c")]
        + [scale_count(singular, few, other) for _, singular, few, other, _ in SCALES]
        + [ordinal(g) for g in GENDER] + [prefix(), part("part-1", "a", "f"), part("part-2", "y", "n"), part("part-5", "", "n")])
SOURCES = {
    "cardinal-m": CLDR + ", %spellout-cardinal-masculine, with the scale words of this lexicon. " + WORDS + ". " + SCALE,
    "cardinal-c": COUNT + ". " + WORDS,
    "cardinal-f": CLDR + ", %spellout-cardinal-feminine: \"1: jedna;\", \"2: dvě;\"",
    "cardinal-n": CLDR + ", %spellout-cardinal-neuter: \"1: jedno;\", \"2: dvě;\"",
    "ordinal-m": ORDINAL + ". " + SILVER_ORD,
    "ordinal-f": ORDINAL + ": the feminine \"-á\"",
    "ordinal-n": ORDINAL + ": the neuter \"-é\"",
    "prefix": SILVER_ORD,
}
SOURCES.update({f"tail-{g}": WORDS for g in GENDER})
SOURCES.update({f"sc-{s}": SCALE for _, s, *_ in SCALES})
SOURCES.update({f"part-{n}": FRACTION + ". " + SILVER_PART for n in (1, 2, 5)})
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 18
block = {
    "source": CLDR + ". Czech counts in the long scale of this lexicon: \"miliarda\" for 10^9, \"bilion\" for 10^12.",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal-c", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}],
                                "neuter": [{"ruleset": "cardinal-n", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                               "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}],
                               "neuter": [{"ruleset": "ordinal-n", "reason": "standard"}]},
                    "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "čárka", "places": 3,
                "source": CLDR + ", %spellout-cardinal-masculine x.x: \"←← čárka →→\"."},
    "scientific": {"times": "krát deset na", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "jedna {denominator}", "named": {},
                 "denominator": "{cardinal}", "numerator": "cardinal-f",
                 "by_count": [{"count": "1", "ruleset": "part-1"},
                              {"count": r"(\d*[02-9])?[234]", "ruleset": "part-2"},
                              {"count": r"\d+", "ruleset": "part-5"}],
                 "source": FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
