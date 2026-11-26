"""Write the writer block of nn from CLDR RBNF nn, Nynorskordboka, Språkrådet and the scale words of the lexicon.

usage: python scripts/writer_nn.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/nn.json"
CLDR = "CLDR RBNF nn (common/rbnf/nn.xml as shipped in unicode-rbnf 2.5.1)"
NO = "Nynorskordboka (ord.uib.no; Papers/Languages/Germanic/Norwegian Nynorsk/)"
SR_FRACTION = ("Språkrådet, «Tredjedel, tredel, fjerdedel, firedel og så vidare» (Papers/Languages/Germanic/Norwegian "
               "Nynorsk/sprakradet_tredjedel-tredel-fjerdedel-firedel.html)")
ACCENT = ("Språkrådet, «Aksentteikn» (Papers/Languages/Germanic/Norwegian Nynorsk/sprakradet_aksentteikn.html): \"Vi kan "
          "bruke aksentteikn for å skilje den ubundne artikkelen ein/en frå talordet éin/én.\"")
CARDINAL = (CLDR + ", %spellout-cardinal-reale: \"1: éin;\", \"20: tjue[­→→];\", \"100: ←%spellout-cardinal-neuter← "
            "hundre[ og →→];\", \"1000: ←%spellout-cardinal-neuter← tusen[ og →→];\", \"1000000: éin million[ →→];\", "
            "\"2000000: ←← millionar[ →→];\". " + NO + ", «tjueein»: \"grunntalet 21\"; «hundre»: \"bli hundre år\"; "
            "«tusen»: \"fleire tusen fans møtte opp\": no count before a lone hundre or tusen")
GENDER = (NO + ", «ein»: \"ein meter, ei mil, eit hekto\"; " + CLDR + ", %spellout-cardinal-neuter: \"1: eitt;\". "
          + ACCENT + " \"Det var berre eitt spørsmål han ikkje greidde å svare på.\"; the gender changes only the lone 1, "
          "as the CLDR sets do")
SCALE = (NO + ", «million»: \"grunntalet 1 000 000\", plural \"millionar\"; «milliard»: \"tusen millionar\", plural "
         "\"milliardar\"; «billion»: \"grunntalet 1 000 000 000 000\", \"ein million millionar\"")
ORDINAL = (NO + ", «første»: \"første · fyrste\", \"rekkjetal til éin\"; «tjuande»: \"rekkjetal til 20\"; «tjueførste»: "
           "\"rekkjetal til 21\"; «hundrede»: \"rekkjetal til 100\"; «million»: \"millionte\"; «milliard»: \"milliardte\"; "
           "«billion»: \"billionte\"; the first form listed")
SILVER_ORD = ("SILVER: \"nullte\", \"tusande\" (the -ande of \"tiande\" and \"tjuande\"), \"hundre og første\" and \"to millionar første\" follow the cardinal and the "
              "Bokmål pattern of CLDR no; CLDR nn has no ordinal rules; no saved example")
FRACTION = (SR_FRACTION + ": \"Åttedel og åttandedel er heilt jamstilte former, som tredel og tredjedel, firedel og "
            "fjerdedel\", \"No er trettendel og trettandedel osb. valfrie former.\"; " + NO + ", «tredel»: \"ein tredel av "
            "løna\", plural \"tredelar\"; the writer takes the cardinal form, the first form of each pair")
SILVER_FRACTION = ("SILVER: \"ein halv\" and \"tre halve\"; a denominator from 100 is one word with \"og\" "
                   "(\"hundreogeindel\"), as in Bokmål; no saved example")

UNITS = "null ein to tre fire fem seks sju åtte ni ti elleve tolv tretten fjorten femten seksten sytten atten nitten".split()
TENS = {20: "tjue", 30: "tretti", 40: "førti", 50: "femti", 60: "seksti", 70: "sytti", 80: "åtti", 90: "nitti"}
FIRST = ("nullte første andre tredje fjerde femte sjette sjuande åttande niande tiande ellevte tolvte trettande fjortande "
         "femtande sekstande syttande attande nittande").split()
# 10^exponent, singular, plural: the scale_noun entries of nn.json (long scale).
SCALES = [(6, "million", "millionar"), (9, "milliard", "milliardar"), (12, "billion", "billionar"),
          (15, "billiard", "billiardar"), (18, "trillion", "trillionar")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def cardinal(name, one):
    """``one`` is the lone 1: "éin", "éi" or "eitt"; in a compound 1 is "ein" ("tjueein", "hundre og ein")."""
    rules = [R("-x", "minus →→"), R(0, "null"), R(1, one, GENDER if one != "éin" else ACCENT)]
    rules += [R(i, w) for i, w in enumerate(UNITS) if i > 1]
    rules += [R(t, f"{w}[→%count→]") for t, w in TENS.items()]
    rules += [R(100, "hundre[ og →%count→]", CARDINAL), R(200, "←%count← hundre[ og →%count→]"),
              R(1000, "tusen[ og →%count→]"), R(2000, "←%count← tusen[ og →%count→]")]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"éin {singular}[ →%count→]", SCALE if exponent == 6 else None),
                  R(2 * 10 ** exponent, f"←%count← {plural}[ →%count→]")]
    return name, rules


def count():
    """A cardinal with "ein" for 1, the count inside a number."""
    rules = [R(i, w) for i, w in enumerate(UNITS)] + [R(t, f"{w}[→→]") for t, w in TENS.items()]
    rules += [R(100, "hundre[ og →→]"), R(200, "←← hundre[ og →→]"), R(1000, "tusen[ og →→]"), R(2000, "←← tusen[ og →→]")]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"éin {singular}[ →→]"), R(2 * 10 ** exponent, f"←← {plural}[ →→]")]
    return "count", rules


def ordinal():
    rules = [R("-x", "minus →→")] + [R(i, w) for i, w in enumerate(FIRST)]
    rules += [R(20, "tjuande", ORDINAL), R(21, "tjue→%ordinal→")]
    rules += [R(t, f"{w}→%ordinal-ande→") for t, w in TENS.items() if t > 20]
    rules += [R(100, "hundre→%ordinal-de→", SILVER_ORD), R(200, "←%count← hundre→%ordinal-de→"),
              R(1000, "tus→%ordinal-thousand→"), R(2000, "←%count← tus→%ordinal-thousand→")]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"[éin ]{singular}→%ordinal-scale→"),
                  R(2 * 10 ** exponent, f"←%count← {singular}→%ordinal-scales→")]
    return [("ordinal", rules),
            ("ordinal-ande", [R(0, "ande"), R(1, "=%ordinal=")]),
            ("ordinal-de", [R(0, "de"), R(1, " og =%ordinal=")]),
            ("ordinal-thousand", [R(0, "ande"), R(1, "en og =%ordinal=")]),
            ("ordinal-scale", [R(0, "te"), R(1, " =%ordinal=")]),
            ("ordinal-scales", [R(0, "te"), R(1, "ar =%ordinal=")])]


def denominator():
    """The word of a part: the cardinal and "del", one word ("tredel", "trettifiredel", "hundreogeindel")."""
    rules = [R(i, f"{w}del") for i, w in enumerate(UNITS) if i > 1]
    rules += [R(t, f"{w}[→%count→]del") for t, w in TENS.items()]
    rules += [R(100, "hundre[og→%count→]del", SILVER_FRACTION), R(200, "←%count←hundre[og→%count→]del"),
              R(1000, "tusen[og→%count→]del"), R(2000, "←%count←tusen[og→%count→]del")]
    for exponent, singular, _ in SCALES:
        rules += [R(10 ** exponent, f"{singular}[og→%count→]del"), R(2 * 10 ** exponent, f"←%count←{singular}[og→%count→]del")]
    return "denominator", rules


sets = [cardinal("cardinal-m", "éin"), cardinal("cardinal-f", "éi"), cardinal("cardinal-n", "eitt"), count()]
sets += ordinal() + [denominator()]
SOURCES = {
    "cardinal-m": CARDINAL + ". " + ACCENT,
    "cardinal-f": GENDER,
    "cardinal-n": GENDER,
    "count": CARDINAL,
    "ordinal": ORDINAL + ". " + SILVER_ORD,
    "denominator": FRACTION + ". " + SILVER_FRACTION,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 21
block = {
    "source": CLDR + ". Nynorsk counts in the long scale of this lexicon: \"milliard\" for 10^9, \"billion\" for 10^12. "
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
    "scientific": {"times": "gonger ti opphøgd i", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "ein {denominator}", "plural": {"halv": "halve", "del": "delar"},
                 "named": {"2": "halv"}, "denominator": "{cardinal}del", "ruleset": "denominator",
                 "numerator": "count", "source": FRACTION + ". " + SILVER_FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
