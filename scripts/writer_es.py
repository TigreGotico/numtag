"""Write the writer block of es from CLDR RBNF es, the -illion words of the lexicon and the RAE DPD.

usage: python scripts/writer_es.py [--check]
"""
import json
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

ROOT = Path(__file__).parents[1]
LEXICON = ROOT / "numtag/lexicon/es.json"
CLDR = "CLDR 38 RBNF es (common/rbnf/es.xml as shipped in unicode-rbnf 2.5.1)"
DPD_UNO = ("RAE, Diccionario panhispánico de dudas, 2.ª ed., «uno»: the apocope holds in compounds, "
           "\"Tengo veintiún años\"")
DPD_CIENTO = ("RAE, Diccionario panhispánico de dudas, 2.ª ed., «ciento»: \"se apocopa en la forma cien cuando "
              "antecede al sustantivo\", and in compounds it \"solo se apocopa ante mil\"")
DPD_AVO = ("RAE, Diccionario panhispánico de dudas, 2.ª ed., «fraccionarios»: \"1/11 onceavo … 1/200 "
           "doscientosavo\"; a fraction is one word, \"dos treceavos\"")
ONP = "ovos-number-parser 0.31.5a2 numbers_es.py"

UNITS = ("cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis "
         "diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco "
         "veintiséis veintisiete veintiocho veintinueve").split()
TENS = "treinta cuarenta cincuenta sesenta setenta ochenta noventa".split()
HUNDREDS = "doscientos trescientos cuatrocientos quinientos seiscientos setecientos ochocientos novecientos".split()
ORD_UNITS = "cero primero segundo tercero cuarto quinto sexto séptimo octavo noveno".split()
ORD_TENS = "trigésimo cuadragésimo quincuagésimo sexagésimo septuagésimo octogésimo nonagésimo".split()
ORD_HUNDREDS = ("ducentésimo tricentésimo cuadringentésimo quingentésimo sexcentésimo septingentésimo "
                "octingentésimo noningentésimo").split()

lex = json.loads(LEXICON.read_text(encoding="utf-8"))
SCALES = {e["rank"]: e["word"] for e in lex["entries"]
          if e.get("role") == "scale_noun" and e.get("rank") and e["word"].endswith("ón")}
TOP = next(k for k in range(1, 100) if k + 1 not in SCALES)  # the -illions run 1..TOP with no gap


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def plain(word):
    """The word with no written accent, as it reads inside a fused word: "dieciséis" in "dieciseisavo"."""
    return "".join(c for c in unicodedata.normalize("NFD", word) if unicodedata.category(c) != "Mn")


def feminine(word):
    return word[:-1] + "a" if word.endswith("o") else word


def cardinal(name, gender):
    """%numbering reads a bare number ("uno"), %cardinal-m and %cardinal-f a number before a noun."""
    units = UNITS[:]
    if gender == "m":
        units[1], units[21] = "un", "veintiún"
    elif gender == "f":
        units[1], units[21] = "una", "veintiuna"
    hundreds = HUNDREDS if gender != "f" else [w[:-2] + "as" for w in HUNDREDS]
    before_mil = "%cardinal-f" if gender == "f" else "%cardinal-m"
    rules = [R("-x", "menos →→")] + [R(i, w) for i, w in enumerate(units)]
    rules += [R(30 + 10 * i, f"{w}[ y →→]") for i, w in enumerate(TENS)]
    rules += [R(100, "cien", DPD_CIENTO), R(101, "ciento →→")]
    rules += [R(200 + 100 * i, f"{w}[ →→]") for i, w in enumerate(hundreds)]
    rules += [R(1000, "mil[ →→]"), R(2000, f"←{before_mil}← mil[ →→]")]
    for rank in range(1, TOP + 1):
        word = SCALES[rank]
        rules += [R(10 ** (6 * rank), f"un {word}[ →→]"),
                  R(2 * 10 ** (6 * rank), f"←%cardinal-m← {word[:-2]}ones[ →→]")]
    return name, rules


def fused():
    """The masculine cardinal with no accent and no space, before a fused ordinal or "-avo": "veintidos"."""
    units = [plain(w) for w in UNITS]
    units[1], units[21] = "un", "veintiun"
    rules = [R(i, w) for i, w in enumerate(units)]
    rules += [R(30 + 10 * i, f"{w}[y→→]") for i, w in enumerate(TENS)]
    rules += [R(100, "cien"), R(101, "ciento→→")]
    rules += [R(200 + 100 * i, f"{w}[→→]") for i, w in enumerate(HUNDREDS)]
    rules += [R(1000, "mil[→→]"), R(2000, "←←mil[→→]")]
    return "fused", rules


def avo():
    """The denominator past ten: the fused cardinal and "avo", "treintavo", "cientounavo" (DPD «fraccionarios»)."""
    def end(word):
        return (word[:-1] if word.endswith("a") else word) + "avo"
    units = [plain(w) for w in UNITS]
    units[1], units[21] = "un", "veintiun"
    rules = [R(i, end(w)) for i, w in enumerate(units)]
    for i, w in enumerate(TENS):
        rules += [R(30 + 10 * i, end(w)), R(31 + 10 * i, f"{w}y→→")]
    rules += [R(100, "cienavo"), R(101, "ciento→→")]
    for i, w in enumerate(HUNDREDS):
        rules += [R(200 + 100 * i, end(w)), R(201 + 100 * i, f"{w}→→")]
    rules += [R(1000, "milavo"), R(1001, "mil→→"), R(2000, "←%fused←milavo"), R(2001, "←%fused←mil→→")]
    return "avo", rules


def ordinal(name, gender):
    g = feminine if gender == "f" else (lambda w: w)
    rules = [R("-x", "menos →→")] + [R(i, g(w)) for i, w in enumerate(ORD_UNITS)]
    rules += [R(10, g("décimo")), R(11, g("undécimo"), ONP), R(12, g("duodécimo"), ONP),
              R(13, "decimo→→"), R(20, g("vigésimo")), R(21, "vigesimo→→", ONP)]
    rules += [R(30 + 10 * i, f"{g(w)}[ →→]") for i, w in enumerate(ORD_TENS)]
    rules += [R(100, f"{g('centésimo')}[ →→]")]
    rules += [R(200 + 100 * i, f"{g(w)}[ →→]") for i, w in enumerate(ORD_HUNDREDS)]
    rules += [R(1000, f"{g('milésimo')}[ →→]"), R(2000, f"←%fused←{g('milésimo')}[ →→]", ONP)]
    for rank in range(1, TOP + 1):
        word = g(SCALES[rank][:-2] + "onésimo")
        rules += [R(10 ** (6 * rank), f"{word}[ →→]"), R(2 * 10 ** (6 * rank), f"←%fused←{word}[ →→]")]
    return name, rules


sets = [cardinal("numbering", None), cardinal("cardinal-m", "m"), cardinal("cardinal-f", "f"),
        ordinal("ordinal-m", "m"), ordinal("ordinal-f", "f"), fused(), avo()]
SOURCES = {
    "numbering": CLDR + ", %spellout-numbering, with the -illion words of this lexicon",
    "cardinal-m": CLDR + ", %spellout-cardinal-masculine: \"un\" and \"veintiún\" before a noun. " + DPD_UNO,
    "cardinal-f": CLDR + ", %spellout-cardinal-feminine",
    "ordinal-m": CLDR + ", %spellout-ordinal-masculine. Changed from it, as " + ONP + " writes it: 11.º and "
                 "12.º are \"undécimo\" and \"duodécimo\", 21.º to 29.º are one word (\"vigesimoprimero\"), and "
                 "the count before a scale ordinal joins it (\"dosmilésimo\", \"veintidosmilésimo\")",
    "ordinal-f": CLDR + ", %spellout-ordinal-feminine, with the changes of ordinal-m",
    "fused": ONP + ": the count of a fused ordinal and of an -avo word has no written accent and no space",
    "avo": DPD_AVO + ". " + ONP + " writes \"treintavo\", \"veintiunavos\", \"cientounavo\" and \"milunavos\"",
}
maximum = "9" * (6 * TOP + 6)
forms = {
    "cardinal": {"variants": [{"ruleset": "numbering", "reason": "standard"}],
                 "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                            "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}]},
                 "maximum": maximum},
    "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                           "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}]},
                "minimum": "0", "maximum": maximum},
}
NAMED = dict(zip(map(str, range(2, 11)), "medio tercio cuarto quinto sexto séptimo octavo noveno décimo".split()))
NAMED.update({"100": "centésimo", "1000": "milésimo", "1000000": "millonésimo"})
block = {
    "source": CLDR + ". Spanish counts in the long scale: the -illion words of this lexicon, 10^(6 × rank), and a "
              "count up to 999999 before each (\"mil millones\" for 10^9).",
    "rulesets": {name: {"source": SOURCES[name], "rules": rules} for name, rules in sets},
    "forms": forms,
    "decimal": {"word": "coma", "places": 3, "source": CLDR + ", %spellout-numbering x,x: \"←← coma →→\". "
                + ONP + " reads each decimal digit (\"dos coma dos cinco\")."},
    "scientific": {"times": "por diez elevado a", "source": ONP + ": 10^300 reads \"uno por diez elevado a trescientos\"."},
    "fraction": {"mixed": False, "limit": 10, "single": "un {denominator}", "plural": "s", "named": NAMED,
                 "denominator": "{cardinal}avos", "ruleset": "avo",
                 "source": DPD_AVO + ". " + ONP + " writes \"un medio\", \"dos tercios\" and \"tres milésimos\"."},
}
splice(LEXICON, block, check="--check" in sys.argv)
