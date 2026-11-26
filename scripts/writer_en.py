"""Write the writer block of en from CLDR RBNF en, the Oxford Advanced Learner's Dictionary, the GPO Style Manual
and the scale words of the lexicon.

usage: python scripts/writer_en.py en|en-US [--check]
In en the first variant is British, with "and" after the hundreds, and the second is American, with no "and".
In en-US the American variant is first.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

variety = sys.argv[1]
LEXICON = Path(__file__).parents[1] / f"numtag/lexicon/{variety}.json"
CLDR = "CLDR RBNF en (common/rbnf/en.xml as shipped in unicode-rbnf 2.5.1)"
OALD = "Oxford Advanced Learner's Dictionary (Papers/Languages/Germanic/English/)"
GPO = "U.S. Government Publishing Office, Style Manual (2016) (Papers/Languages/Germanic/English/GPO-STYLEMANUAL-2016.pdf)"
AND = (OALD + ", «and»: \"When numbers (but not dates) are spoken, and is used between the hundreds and the figures that "
       "follow: 2 264—two thousand, two hundred and sixty-four\". CLDR en %spellout-cardinal-verbose")
NO_AND = GPO + ", 12.20: \"one thousand eight hundred fifty\", \"one hundred fifty-two thousand three hundred five\""
HYPHEN = GPO + ", 6.36: \"Print a hyphen between the elements of compound numbers from twenty-one to ninety-nine\""
SCALE = (OALD + ", «billion»: \"1 000 000 000; one thousand million\"; \"You say a, one, two, several, etc. billion "
         "without a final ‘s’ on ‘billion’\"")
ORDINAL = CLDR + ", %spellout-ordinal and %spellout-ordinal-verbose: \"twenty-first\" (" + GPO + ", 6.36), \"hundredth\" (" \
          + OALD + ")"
SILVER_ORD = "SILVER: \"one hundred and first\", the ordinal of the British cardinal; no saved example"
FRACTION = (OALD + ", «three quarters»: \"( US English also three fourths )\"; the denominator is the ordinal with -s "
            "(\"two thirds\", \"three quarters\"). SILVER: \"one half\" for 1/2; no saved source chooses between \"a half\" "
            "and \"one half\". SILVER: a denominator 10^n drops its count (\"seven millionths\"); no saved example")

UNITS = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen "
         "eighteen nineteen").split()
TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety"}
FIRST = "zeroth first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth".split()
# 10^exponent, word: the scale_noun entries of en.json (short scale).
SCALES = [(3 * (rank + 2), word) for rank, word in enumerate(
    "million billion trillion quadrillion quintillion sextillion septillion octillion nonillion".split())]
# The long scale: "billion" is a million million, and 10^9 reads "thousand million".
LONG = [(6, "million")] + [(6 * (rank + 2), word) for rank, word in enumerate("billion trillion quadrillion quintillion".split())]
LONG_SOURCE = (OALD + ", «billion»: \"(British English, old-fashioned) 1 000 000 000 000; one million million\". ovos-number-parser "
               "writes 10^9 as \"one thousand million\" in the long scale")


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def small(name):
    return [R("-x", "minus →→"), R(0, "zero")] + [R(i, w) for i, w in enumerate(UNITS) if i] + \
           [R(t, f"{w}[-→→]", HYPHEN if t == 20 else None) for t, w in TENS.items()]


def cardinal_gb(name="cardinal-gb", scales=SCALES):
    rules = small(name) + [R(100, f"←← hundred[→%{name}-and→]", AND), R(1000, f"←← thousand[→%{name}-commas→]")]
    rules += [R(10 ** e, f"←← {w}[→%{name}-commas→]", SCALE if w == "billion" and scales is SCALES else None) for e, w in scales]
    return [(name, rules),
            (f"{name}-and", [R(1, f" and =%{name}="), R(100, f" =%{name}=")]),
            (f"{name}-commas", [R(1, f" and =%{name}="), R(100, f" =%{name}=")])]


def cardinal_us(name="cardinal-us", scales=SCALES):
    rules = small(name) + [R(100, "←← hundred[ →→]", NO_AND), R(1000, "←← thousand[ →→]")]
    rules += [R(10 ** e, f"←← {w}[ →→]") for e, w in scales]
    return [(name, rules)]


def ordinal(name, count, british, scales=SCALES):
    rules = [R("-x", "minus →→")] + [R(i, w) for i, w in enumerate(FIRST)] + [R(13, "=%cardinal-us=th")]
    rules += [R(t, f"{w[:-1]}→%{name}-tieth→") for t, w in TENS.items()]
    tail = f"{name}-and" if british else f"{name}-th"
    rules += [R(100, f"←%{count}← hundred→%{tail}→"), R(1000, f"←%{count}← thousand→%{name}-group→")]
    rules += [R(10 ** e, f"←%{count}← {w}→%{name}-group→") for e, w in scales]
    sets = [(name, rules), (f"{name}-tieth", [R(0, "ieth"), R(1, f"y-=%{name}=")])]
    if british:
        sets += [(f"{name}-and", [R(0, "th"), R(1, f" and =%{name}=", SILVER_ORD), R(100, f" =%{name}=")]),
                 (f"{name}-group", [R(0, "th"), R(1, f" and =%{name}="), R(100, f" =%{name}=")])]
    else:
        sets += [(f"{name}-th", [R(0, "th"), R(1, f" =%{name}=")]), (f"{name}-group", [R(0, "th"), R(1, f" =%{name}=")])]
    return sets


sets = (cardinal_gb() + cardinal_us() + ordinal("ordinal-gb", "cardinal-gb", True) + ordinal("ordinal-us", "cardinal-us", False)
        + cardinal_gb("cardinal-gb-long", LONG) + cardinal_us("cardinal-us-long", LONG)
        + ordinal("ordinal-gb-long", "cardinal-gb-long", True, LONG) + ordinal("ordinal-us-long", "cardinal-us-long", False, LONG))
SOURCES = {
    "cardinal-gb": CLDR + ", %spellout-cardinal-verbose, with the scale words of this lexicon. " + AND + ". " + HYPHEN,
    "cardinal-us": CLDR + ", %spellout-cardinal, with the scale words of this lexicon. " + NO_AND + ". " + HYPHEN,
    "ordinal-gb": ORDINAL + ". " + SILVER_ORD,
    "ordinal-us": ORDINAL,
    "cardinal-gb-long": LONG_SOURCE,
    "cardinal-us-long": LONG_SOURCE,
    "ordinal-gb-long": LONG_SOURCE,
    "ordinal-us-long": LONG_SOURCE,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + max((k for k in SOURCES if name.startswith(k)), key=len),
                   "rules": rules} for name, rules in sets}
maximum = "9" * 33


def pair(form, end=""):
    gb = {"ruleset": f"{form}-gb{end}", "reason": "standard"}
    us = {"ruleset": f"{form}-us{end}", "reason": "no_conjunction", "source": NO_AND}
    if variety == "en-US":
        return {"variants": [{**us, "reason": "standard"}, {**gb, "reason": "variant_spelling", "source": AND}]}
    return {"variants": [gb, us]}


block = {
    "source": CLDR + ". English counts in the short scale of this lexicon. " + SCALE + ".",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {**pair("cardinal"), "maximum": maximum,
                     "scale": {"long": {**pair("cardinal", "-long"), "maximum": "9" * 36}}},
        "ordinal": {**pair("ordinal"), "minimum": "0", "maximum": maximum,
                    "scale": {"long": {**pair("ordinal", "-long"), "minimum": "0", "maximum": "9" * 36}}},
    },
    "decimal": {"word": "point", "places": 3, "source": CLDR + ", %spellout-cardinal x.x: \"←← point →→\"."},
    "scientific": {"times": "times ten to the power of", "source": "Not checked against a style guide."},
    "fraction": {"mixed": False, "limit": 10, "single": "one {denominator}", "plural": {"half": "halves", "": "s"},
                 "named": {"2": "half", "4": "quarter", "100": "hundredth", "1000": "thousandth",
                           **{str(10 ** e): w + "th" for e, w in SCALES}}, "denominator": "{cardinal}ths", "ruleset": "ordinal-us" if variety == "en-US" else "ordinal-gb",
                 "numerator": "cardinal-us" if variety == "en-US" else "cardinal-gb", "source": FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
