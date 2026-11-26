"""Write the writer block of nl from Taaladvies.net (Taalunie), CLDR RBNF nl and the scale words of the lexicon.

usage: python scripts/writer_nl.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/nl.json"
CLDR = "CLDR RBNF nl (common/rbnf/nl.xml as shipped in unicode-rbnf 2.5.1)"
TA = "Taaladvies.net, «Aaneenschrijven van telwoorden (algemeen)» (Papers/Languages/Germanic/Dutch/)"
SPACING = (TA + ": \"Hoofdtelwoorden worden aaneengeschreven tot en met het woord duizend.\", \"Na het woord duizend (en "
           "samenstellingen hiermee, zoals vierduizend) staat een spatie.\" (\"zesduizend achtentwintig\") and \"Miljoen en "
           "miljard zijn altijd aparte woorden.\" (\"vijf miljard tweehonderd miljoen\"); 101 \"honderdeen of honderdeneen\", "
           "the first form. CLDR nl writes \"duizendachtentwintig\"; the writer follows the Taalunie")
ORDINAL = (TA + ": \"Rangtelwoorden worden gevormd door toevoeging van het achtervoegsel -ste, de of -e aan het "
           "overeenkomstige hoofdtelwoord. Met de hoofdtelwoorden een en drie corresponderen evenwel de rangtelwoorden eerste "
           "en derde. Voor het overige worden de rangtelwoorden op dezelfde wijze gespeld als de hoofdtelwoorden waarvan ze "
           "zijn afgeleid.\" Examples: \"honderdentweede\", \"drieduizend tweehonderdtwintigste\", \"vier miljoenste\", \"vier "
           "miljoen vierhonderdduizendste\". The writer joins no \"en\" after honderd (\"honderdtweede\"), as the first form of "
           "the cardinal \"honderdeen of honderdeneen\"")
SILVER_ONE = (TA + ": \"vier miljoenste\", \"vier miljoen vierhonderdduizendste\"; SILVER: a lone scale ordinal has "
              "no count (\"miljoenste\"), as \"honderdste\" and \"duizendste\", and keeps it before a rest (\"één "
              "miljoen eerste\")")
FRACTION = (TA + ": \"Bij breuken is de teller een hoofdtelwoord en de noemer een rangtelwoord.\", \"Teller en noemer worden "
            "los van elkaar geschreven.\" (\"twee derde\", \"zevenenveertig tienduizendste\"), and \"Het rangtelwoord in de "
            "noemer krijgt meestal geen meervouds-n.\"")
SILVER_HALF = "SILVER: 1/2 reads \"een half\" and n/2 \"halve\"; no saved rule"
ONE = ("Taaladvies.net, «Eén / een van de» (Papers/Languages/Germanic/Dutch/taaladvies-een-of-een-van-de.html): \"komen er "
       "bijvoorbeeld uitspraaktekens op een als men een precies aantal bedoelt: Hij heeft nog één rekening (en geen twee "
       "rekeningen) te betalen\"; a lone 1 and the count of a scale word are a precise number (\"één\", \"één miljoen\"); "
       "inside a word 1 stays \"een\" (\"eenentwintig\", \"honderdeen\")")

UNITS = "nul een twee drie vier vijf zes zeven acht negen tien elf twaalf dertien veertien vijftien zestien zeventien " \
        "achttien negentien".split()
TENS = {20: "twintig", 30: "dertig", 40: "veertig", 50: "vijftig", 60: "zestig", 70: "zeventig", 80: "tachtig",
        90: "negentig"}
# A unit before "en" and a ten (CLDR nl %%number-en): "eenentwintig", "tweeëntwintig", "drieëntwintig".
UNIT_EN = {u: {1: "eenen", 2: "tweeën", 3: "drieën"}.get(u) or w + "en" for u, w in enumerate(UNITS[:10])}
# The ordinal ending of 1 to 19 (CLDR nl %spellout-ordinal): -de, and -ste for 8.
FIRST = {0: "nulste", 1: "eerste", 2: "tweede", 3: "derde", 8: "achtste"}
# 10^exponent, word: the scale_noun entries of nl.json (long scale).
SCALES = [(6, "miljoen"), (9, "miljard"), (12, "biljoen"), (15, "biljard"), (18, "triljoen"), (21, "triljard")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def tens(name, last):
    """20 to 99: "eenentwintig", "tweeëntwintig"; ``last`` is the ending of a round ten ("" or "ste")."""
    rules = []
    for t, w in TENS.items():
        rules += [R(t, w + last)] + [R(t + u, f"{UNIT_EN[u]}{w}{last}") for u in range(1, 10)]
    return rules


cardinal = [R("-x", "min →→")] + [R(i, w) for i, w in enumerate(UNITS)]
cardinal += tens("cardinal", "")
cardinal += [R(100, "honderd[→→]", SPACING), R(200, "←←honderd[→→]"), R(1000, "duizend[ →→]"), R(2000, "←←duizend[ →→]")]
for exponent, word in SCALES:
    cardinal += [R(10 ** exponent, f"←← {word}[ →→]")]
# The stressed reading: "één" for a lone 1 and for the count of a scale word; the rest is the cardinal.
stressed = [R(1, "één", ONE), R(100, "=%cardinal="), R(1000, "duizend[ →%stressed→]"),
            R(2000, "←%cardinal←duizend[ →%stressed→]")]
stressed += [R(10 ** e, f"←%stressed← {w}[ →%stressed→]") for e, w in SCALES]
stressed = [R("-x", "min →→"), R(0, "=%cardinal=")] + stressed[:1] + [R(2, "=%cardinal=")] + stressed[1:]

ordinal = [R("-x", "min →→")] + [R(i, FIRST.get(i) or w + "de") for i, w in enumerate(UNITS)]
ordinal[1]["source"] = ORDINAL
ordinal += tens("ordinal", "ste")
ordinal += [R(100, "honderd→%ordinal-hundred→"), R(200, "←%cardinal←honderd→%ordinal-hundred→"),
            R(1000, "duizend→%ordinal-thousand→"), R(2000, "←%cardinal←duizend→%ordinal-thousand→")]
for exponent, word in SCALES:
    ordinal += [R(10 ** exponent, f"[één ]{word}→%ordinal-thousand→", SILVER_ONE if exponent == 6 else None),
                R(2 * 10 ** exponent, f"←%cardinal← {word}→%ordinal-thousand→")]

sets = [
    ("cardinal", cardinal),
    ("stressed", stressed),
    ("ordinal", ordinal),
    ("ordinal-hundred", [R(0, "ste"), R(1, "=%ordinal=")]),
    ("ordinal-thousand", [R(0, "ste"), R(1, " =%ordinal=")]),
]
SOURCES = {
    "cardinal": CLDR + ", %spellout-cardinal, with the scale words of this lexicon. " + SPACING,
    "stressed": ONE,
    "ordinal": CLDR + ", %spellout-ordinal. " + ORDINAL + ". " + SILVER_ONE,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of ordinal", "rules": rules} for name, rules in sets}
maximum = "9" * 24
block = {
    "source": CLDR + ". Dutch counts in the long scale of this lexicon: Onze Taal 70 (2001), «Een miljard of een "
              "biljoen?»: \"Een miljoen miljoen is een biljoen … duizend miljoen is een miljard\".",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "stressed", "reason": "standard"},
                                  {"ruleset": "cardinal", "reason": "variant_spelling"}], "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal", "reason": "standard"}], "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "komma", "places": 3, "source": CLDR + ", %spellout-cardinal x.x: \"←← komma →→\"."},
    "scientific": {"times": "maal tien tot de macht", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "een {denominator}", "plural": {"half": "halve"},
                 "named": {"2": "half", **{str(10 ** e): w + "ste" for e, w in SCALES}}, "denominator": "{cardinal}ste", "ruleset": "ordinal", "numerator": "cardinal",
                 "source": FRACTION + ". " + SILVER_HALF + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
