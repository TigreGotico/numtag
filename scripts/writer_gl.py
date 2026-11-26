"""Write the writer block of gl from the RAG and ILG Normas ortográficas e morfolóxicas (§16) and the scale words
of the lexicon.

usage: python scripts/writer_gl.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/gl.json"
NORMAS = "RAG e ILG, Normas ortográficas e morfolóxicas do idioma galego, 23.ª ed. (2012)"
NORMAS_CARDINAL = (NORMAS + ", §16.1, p. 98: \"vinte e un / vinte e unha\", \"cen\", \"cento un, cento unha etc.\", "
                   "\"douscentos / duascentas\", \"cincocentos / cincocentas, quiñentos/ -as\"; the writer takes the "
                   "first form of each pair")
NORMAS_NOUN = NORMAS + ", p. 99: \"Cento, millón, billón, trillón, aínda que expresan número, funcionan como substantivos\""
NORMAS_ORDINAL = (NORMAS + ", §16.2, p. 100: \"undécimo / décimo primeiro\", \"duodécimo / décimo segundo\", "
                  "\"vixésimo primeiro\", \"centésimo\", \"milésimo\", \"millonésimo\"; \"Todas estas formas admiten "
                  "morfemas de xénero e número, que nas formas compostas só se unen ao último elemento (décimo "
                  "primeira)\"; the writer takes the first form of each pair")
NORMAS_PARTITIVE = (NORMAS + ", §16.4, p. 101: \"medio, -a\", \"terzo, -a\" ... \"décimo, -a\", and \"a partir de 1/11 (e "
                    "exceptuados 1/100, 1/1000, 1/1.000.000) o partitivo faise engadindo ao cardinal o sufixo -avo: "
                    "(1/16) un dezaseisavo, (2/29) dous vinte e noveavos\"")
SILVER_MIL = ("SILVER: no saved source joins \"mil\" and the rest; the writer follows \"cento un\" of the table and "
              "writes no \"e\": \"mil un\", \"mil cen\"")
SILVER_ORD = ("SILVER: the ordinals of 200 to 900 (\"ducentésimo\") and of a count of thousands or millions (\"dous "
              "milésimo\") have no saved source")
SILVER_SCALE = ("RAG, Dicionario, «millón»: \"Mil veces mil.\", «billón»: \"Un millón de millóns.\". SILVER: \"mil "
                "millóns\" for 10^9 has no saved source")

UNITS = ("cero un dous tres catro cinco seis sete oito nove dez once doce trece catorce quince dezaseis dezasete "
         "dezaoito dezanove").split()
TENS = {20: "vinte", 30: "trinta", 40: "corenta", 50: "cincuenta", 60: "sesenta", 70: "setenta", 80: "oitenta",
        90: "noventa"}
HUNDREDS = "dous tres catro cinco seis sete oito nove".split()
ORD_UNITS = "primeiro segundo terceiro cuarto quinto sexto sétimo oitavo noveno".split()
ORD_TENS = {20: "vixésimo", 30: "trixésimo", 40: "cuadraxésimo", 50: "quincuaxésimo", 60: "sesaxésimo",
            70: "septuaxésimo", 80: "octoxésimo", 90: "nonaxésimo"}
ORD_HUNDREDS = ("ducentésimo tricentésimo cuadrinxentésimo quinxentésimo sexcentésimo septinxentésimo "
                "octinxentésimo noninxentésimo").split()
# 10^exponent, singular, plural: the long scale of the lexicon.
SCALES = [(6, "millón", "millóns"), (12, "billón", "billóns"), (18, "trillón", "trillóns")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def feminine(word):
    return word[:-1] + "a" if word.endswith("o") else word


def cardinal(name, gender):
    """A cardinal rule set: masculine "un", "dous", "douscentos" or feminine "unha", "dúas", "duascentas"."""
    f = gender == "f"
    units = UNITS[:]
    if f:
        units[1], units[2] = "unha", "dúas"
    rules = [R("-x", "menos →→")] + [R(i, w) for i, w in enumerate(units)]
    rules += [R(t, f"{w}[ e →→]") for t, w in TENS.items()]
    rules += [R(100, "cen", NORMAS_CARDINAL), R(101, "cento →→", NORMAS_NOUN)]
    for i, w in enumerate(HUNDREDS):
        stem = ("duas" if f else w) if w == "dous" else w  # "duascentas", with no accent
        rules += [R(200 + 100 * i, f"{stem}cent{'as' if f else 'os'}[ →→]")]
    rules += [R(1000, "mil[ →→]", SILVER_MIL), R(2000, "←← mil[ →→]")]  # "dúas mil", "duascentas mil"
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"un {singular}[ →→]"),
                  R(2 * 10 ** exponent, f"←%cardinal-m← {plural}[ →→]", SILVER_SCALE)]
    return name, rules


def ordinal(name, gender):
    """An ordinal rule set; in a compound only the last word takes the feminine ("décimo primeira")."""
    g = feminine if gender == "f" else (lambda w: w)
    rest = f"%{name}"
    rules = [R("-x", "menos →→")] + [R(i + 1, g(w)) for i, w in enumerate(ORD_UNITS)]
    rules += [R(10, g("décimo")), R(11, g("undécimo"), NORMAS_ORDINAL), R(12, g("duodécimo")),
              R(13, f"décimo →{rest}→")]
    for t, w in ORD_TENS.items():
        rules += [R(t, g(w)), R(t + 1, f"{w} →{rest}→")]
    rules += [R(100, g("centésimo")), R(101, f"centésimo →{rest}→")]
    for i, w in enumerate(ORD_HUNDREDS):
        rules += [R(200 + 100 * i, g(w), SILVER_ORD), R(201 + 100 * i, f"{w} →{rest}→")]
    rules += [R(1000, g("milésimo")), R(1001, f"milésimo →{rest}→"),
              R(2000, f"←%cardinal-m← milésim→{rest}-tail→")]
    for exponent, singular, _ in SCALES:
        word = singular[:-2] + "onésimo"
        rules += [R(10 ** exponent, g(word)), R(10 ** exponent + 1, f"{word} →{rest}→"),
                  R(2 * 10 ** exponent, f"←%cardinal-m← {word[:-1]}→{rest}-tail→")]
    # after a count: "dous milésimo", "dous milésima", "dous milésimo primeiro"
    return [(name, rules), (f"{name}-tail", [R(0, g("o")), R(1, f"o =%{name}=")])]


def avo():
    """The partitive from 11: the cardinal and "-avo" ("onceavo", "vinte e noveavo"); 100, 1000 and 10^6 are named."""
    return "avo", [R(0, "=%cardinal-m=avo")]


sets = [cardinal("numbering", "m"), cardinal("cardinal-m", "m"), cardinal("cardinal-f", "f"),
        *ordinal("ordinal-m", "m"), *ordinal("ordinal-f", "f"), avo()]
SOURCES = {
    "numbering": NORMAS_CARDINAL + ". " + NORMAS_NOUN,
    "cardinal-m": NORMAS_CARDINAL,
    "cardinal-f": NORMAS_CARDINAL + "; \"un/unha\", \"dous/dúas\"",
    "ordinal-m": NORMAS_ORDINAL + ". " + SILVER_ORD,
    "ordinal-f": NORMAS_ORDINAL + ". " + SILVER_ORD,
    "avo": NORMAS_PARTITIVE + ". SILVER: a denominator with a hundred or a thousand (\"cento unavo\", \"dous milavo\") takes -avo by the same rule; the Normas give no example",
}
NAMED = dict(zip(map(str, range(2, 11)), "medio terzo cuarto quinto sexto sétimo oitavo noveno décimo".split()))
NAMED.update({"100": "centésimo", "1000": "milésimo", "1000000": "millonésimo"})
# The counts stop at 999999 before each scale word, so the long scale ends below 10^24.
maximum = "9" * 24
block = {
    "source": NORMAS + ", §16. Galician counts in the long scale of this lexicon: \"billón\" for 10^12. " + SILVER_SCALE,
    "rulesets": {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
                 for name, rules in sets},
    "forms": {
        "cardinal": {"variants": [{"ruleset": "numbering", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                               "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}]},
                    "minimum": "1", "maximum": maximum},
    },
    "decimal": {"word": "coma", "places": 3,
                "source": "Not checked against a grammar: \"coma\" and one word for each decimal digit."},
    "scientific": {"times": "por dez elevado a",
                   "source": "Not checked against a grammar: the phrase of ovos-number-parser 0.31.5a2 numbers_gl.py."},
    "fraction": {"mixed": False, "limit": 10, "single": "un {denominator}", "plural": "s", "named": NAMED,
                 "denominator": "{cardinal}avos", "ruleset": "avo", "numerator": "cardinal-m",
                 "source": NORMAS_PARTITIVE + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
