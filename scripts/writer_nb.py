"""Write the writer block of nb from CLDR RBNF no, Språkrådet, Bokmålsordboka and the scale words of the lexicon.

usage: python scripts/writer_nb.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/nb.json"
CLDR = "CLDR RBNF no (common/rbnf/no.xml as shipped in unicode-rbnf 2.5.1)"
BM = "Bokmålsordboka (ord.uib.no; Papers/Languages/Germanic/Norwegian Bokmål/)"
SR = "Språkrådet, «Tall, tid og dato» (Papers/Languages/Germanic/Norwegian Bokmål/sprakradet_tall-tid-dato.html)"
AND = CLDR + ", %spellout-cardinal-reale: \"100: hundre[ og →→];\" and %%and-small: \"0: og =%%spellout-cardinal-reale=;\""
TJUENDE = BM + ", «tjuende»: \"ordenstall til 20\""
TJUEEN = BM + ", «tjueen»: \"grunntallet 21\": the tens and the units are one word"
ETT = ("Språkrådet, «Et eller ett?» (Papers/Languages/Germanic/Norwegian Bokmål/sprakradet_et-eller-ett.html): \"Når du "
       "sikter til tallet 1 (i motsetning til 2 eller flere), har ordet trykk og skrives ett\"")
SCALE = (BM + ", «million»: \"én million\"; «milliard»: \"grunntallet 1 000 000 000\"; «billion»: \"grunntallet "
         "1 000 000 000 000\"")
ORDINAL = (CLDR + ", %spellout-ordinal-masculine: \"13: =%spellout-cardinal-neuter=de;\", \"20: tjue→%%ord-masc-nde→;\". "
           + BM + ", «tjueførste»: \"ordenstall til 21\"; «hundrede»: \"ordenstall til 100\". " + SR
           + ": \"for tusende gang\"")
SILVER_ORD = ("SILVER: \"hundre og første\" and \"to hundrede\" follow the cardinal (\"hundre og en\"); no saved "
              "example. " + CLDR + ", %spellout-ordinal-masculine: \"1000000: én million→%%ord-masc-te→;\", "
              "\"2000000: ←%%spellout-cardinal-reale← million→%%ord-masc-teer→;\"")
FRACTION = (SR + ": \"Hovedregelen er at vi bruker grunntall i nevneren i brøker. åtte trettendeler ni "
            "trettifiredeler\"; \"I tall til og med 12 kan vi velge om vi vil bruke grunntall eller ordenstall i nevneren. "
            "en tredel eller en tredjedel\"; the writer uses the first form")
SILVER_FRACTION = ("SILVER: \"en halv\", \"tre halve\" (" + SR + ": \"to og en halv side\"); a denominator from 100 is one "
                   "word with \"og\", as the years of " + SR + " (\"nittenhundreogåttifire\"): \"hundreogendeler\"")

UNITS = "null en to tre fire fem seks sju åtte ni ti elleve tolv tretten fjorten femten seksten sytten atten nitten".split()
TENS = {20: "tjue", 30: "tretti", 40: "førti", 50: "femti", 60: "seksti", 70: "sytti", 80: "åtti", 90: "nitti"}
FIRST = "nullte første andre tredje fjerde femte sjette sjuende åttende niende tiende ellevte tolvte".split()
# 10^exponent, singular, plural: the scale_noun entries of nb.json (long scale).
SCALES = [(6, "million", "millioner"), (9, "milliard", "milliarder"), (12, "billion", "billioner"),
          (15, "billiard", "billiarder"), (18, "trillion", "trillioner")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def cardinal(name, one):
    """``one`` is the 1 of the gender: "en", "ei" or "ett". It ends a compound after "hundre og" and "tusen" in each
    gender ("hundre og ei"), and after a ten only in the neuter ("tjueett", but "tjueen" for the feminine)."""
    tail = name if one == "ett" else "count"
    rules = [R("-x", "minus →→"), R(0, "null"), R(1, one, ETT if one == "ett" else None)]
    rules += [R(i, w) for i, w in enumerate(UNITS) if i > 1]
    rules += [R(t, f"{w}[→%{tail}→]", TJUEEN if t == 20 else None) for t, w in TENS.items()]
    rules += [R(100, f"hundre[ og →%{name}→]", AND), R(200, f"←%count← hundre[ og →%{name}→]"),
              R(1000, f"tusen[ →%and-{name}→]"), R(2000, f"←%count← tusen[ →%and-{name}→]")]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"én {singular}[ →%{name}→]", SCALE if exponent == 6 else None),
                  R(2 * 10 ** exponent, f"←%cardinal-m← {plural}[ →%{name}→]")]
    return name, rules


def ordinal():
    rules = [R("-x", "minus →→")] + [R(i, w) for i, w in enumerate(FIRST)] + [R(13, "=%count=de")]
    rules += [R(20, "tjuende", TJUENDE), R(21, "tjue→%ordinal→")]
    rules += [R(t, f"{w}→%ordinal-nde→") for t, w in TENS.items() if t > 20]
    rules += [R(100, "hundre→%ordinal-de→", SILVER_ORD), R(200, "←%count← hundre→%ordinal-de→"),
              R(1000, "tusen→%ordinal-group→"), R(2000, "←%count← tusen→%ordinal-group→")]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"én {singular}→%ordinal-scale→"), R(2 * 10 ** exponent, f"←%count← {singular}→%ordinal-scales→")]
    return [("ordinal", rules),
            ("ordinal-nde", [R(0, "ende"), R(1, "=%ordinal=")]),
            ("ordinal-de", [R(0, "de"), R(1, " og =%ordinal=")]),
            ("ordinal-group", [R(0, "de"), R(1, " og =%ordinal="), R(100, " =%ordinal=")]),
            ("ordinal-scale", [R(0, "te"), R(1, " =%ordinal=")]),
            ("ordinal-scales", [R(0, "te"), R(1, "er =%ordinal=")])]


def denominator():
    """The word of a part: the cardinal and "del", one word ("tredel", "trettifiredel", "hundreogendel")."""
    rules = [R(i, f"{w}del") for i, w in enumerate(UNITS) if i > 1]
    rules += [R(t, f"{w}[→%count→]del") for t, w in TENS.items()]
    rules += [R(100, "hundre[og→%count→]del", SILVER_FRACTION), R(200, "←%count←hundre[og→%count→]del"),
              R(1000, "tusen[og→%count→]del"), R(2000, "←%count←tusen[og→%count→]del")]
    for exponent, singular, _ in SCALES:
        rules += [R(10 ** exponent, f"{singular}[og→%count→]del"), R(2 * 10 ** exponent, f"←%count←{singular}[og→%count→]del")]
    return "denominator", rules


sets = [cardinal("cardinal-m", "en"), cardinal("cardinal-f", "ei"), cardinal("cardinal-n", "ett"),
        ("count", [R(i, w) for i, w in enumerate(UNITS)] + [R(t, f"{w}[→→]") for t, w in TENS.items()]
         + [R(100, "hundre[ og →→]"), R(200, "←← hundre[ og →→]"), R(1000, "tusen[ →%and→]"), R(2000, "←← tusen[ →%and→]")]),
        ("and", [R(0, "og =%count="), R(100, "=%count=")])]
sets += [(f"and-{name}", [R(0, f"og =%{name}="), R(100, f"=%{name}=")]) for name in ("cardinal-m", "cardinal-f", "cardinal-n")]
sets += ordinal() + [denominator()]
SOURCES = {
    "cardinal-m": CLDR + ", %spellout-cardinal-masculine, with the scale words of this lexicon. " + AND + ". " + TJUEEN,
    "cardinal-f": CLDR + ", %spellout-cardinal-feminine: \"1: ei;\", \"100: hundre[ og →→];\", \"1000: tusen[ "
                  "→%%and-small-f→];\", and no rule for the tens, which read the cardinal (\"tjueen\")",
    "cardinal-n": CLDR + ", %spellout-cardinal-neuter: \"1: ett;\", \"20: tjue[­→→];\", \"100: hundre[ og →→];\". "
                  + ETT,
    "count": CLDR + ", %spellout-cardinal-reale: a count below a thousand, with \"en\" for 1 (" + TJUEEN + ")",
    "and": CLDR + ", %%and-small: \"0: og =%%spellout-cardinal-reale=;\", \"100: =%%spellout-cardinal-reale=;\"",
    "ordinal": ORDINAL + ". " + SILVER_ORD,
    "denominator": FRACTION + ". " + SILVER_FRACTION,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 21
block = {
    "source": CLDR + ". Norwegian counts in the long scale of this lexicon: \"milliard\" for 10^9, \"billion\" for 10^12. "
              + SCALE + ".",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal-m", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}],
                                "neuter": [{"ruleset": "cardinal-n", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal", "reason": "standard"}], "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "komma", "places": 3, "source": CLDR + ", %spellout-cardinal-reale x.x: \"←← komma →→\"."},
    "scientific": {"times": "ganger ti opphøyd i", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "en {denominator}", "plural": {"halv": "halve", "del": "deler"},
                 "named": {"2": "halv"}, "denominator": "{cardinal}del", "ruleset": "denominator",
                 "numerator": "cardinal-m", "source": FRACTION + ". " + SILVER_FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
