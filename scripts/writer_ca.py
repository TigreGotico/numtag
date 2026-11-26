"""Write the writer block of ca from the IEC grammar (GIEC §17.2) and orthography (OIEC §4.4.2.2), CLDR RBNF ca and
the scale words of the lexicon.

usage: python scripts/writer_ca.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/ca.json"
CLDR = "CLDR RBNF ca (common/rbnf/ca.xml as shipped in unicode-rbnf 2.5.1)"
GIEC = "IEC, Gramàtica de la llengua catalana (2016)"
HYPHEN = (GIEC + ", §17.2.1.1: \"el guionet uneix els numerals que representen les desenes i les unitats, tant quan "
          "estan coordinats (vint-i-dos, vint-i-tres) com quan estan juxtaposats (trenta-dos, trenta-tres), i els que "
          "representen les unitats i les centenes (dos-cents, tres-centes), però no en la resta de casos (cent dos, dos "
          "mil, dos milions cent mil).\" CLDR ca writes \"cent-dos\"; the writer follows the IEC")
GENDER = (GIEC + ", quadre 17.1: \"1 un una 2 dos dues 21 vint-i-un vint-i-una\", \"200 dos-cents dues-centes\", and "
          "\"2.000 dos mil/dues mil\"")
NUMBER_NAME = (GIEC + ": the names of the numbers \"prenen en la majoria de contextos la forma masculina dels cardinals, i "
               "en el cas de un adopta de vegades la forma u\"; the writer reads the masculine \"un\"")
ORDINAL = (GIEC + ", §17.2.5: \"Els quatre primers ordinals tenen formes bàsiques específiques: primer, segon, tercer i "
           "quart\"; the others \"es formen d’una manera general a partir dels nombres cardinals i el sufix ‑è / ‑en(a), com "
           "els fraccionaris (vint-i-dosè, cent vint-i-cinquè, centè, dos-centè, milè), llevat del cas de deu, en què per "
           "raons històriques tenim desè, desena\"; \"no en la resta de casos (cent dosè, cent tresè, dos milè)\"; and "
           "\"En general, són preferibles els ordinals en ‑er / ‑er(a) i en ‑è / ‑en(a) a les formes en ‑èsim\"")
FRACTION = (GIEC + ", §17.2.2: \"La forma de la majoria dels quantificadors fraccionaris coincideix amb la dels numerals "
            "ordinals\" and \"tenen formes particulars els numerals fraccionaris mig, meitat i terç\"; \"un quart o una "
            "quarta part (1/4), dos quarts\"; \"el quantificador cardinal designa el numerador de la fracció, i el "
            "fraccionari, el denominador\"")
SILVER_ORD = ("SILVER: in a compound ordinal the words before the last one keep the masculine (\"dos-cents unena\"), and "
              "\"milionè\" follows the -è rule; no saved example")
SILVER_FEMININE = "the feminine ordinals primera, segona, tercera, quarta: CPNL, «Numerals catalans»"

UNITS = ("zero un dos tres quatre cinc sis set vuit nou deu onze dotze tretze catorze quinze setze disset divuit "
         "dinou").split()
TENS = {20: "vint", 30: "trenta", 40: "quaranta", 50: "cinquanta", 60: "seixanta", 70: "setanta", 80: "vuitanta",
        90: "noranta"}
# The ordinals from 5 (CLDR ca %spellout-ordinal-masculine); in a compound 1 to 4 are "unè", "dosè", "tresè", "quatrè".
ORD = {1: "unè", 2: "dosè", 3: "tresè", 4: "quatrè", 5: "cinquè", 6: "sisè", 7: "setè", 8: "vuitè", 9: "novè",
       10: "desè", 11: "onzè", 12: "dotzè", 13: "tretzè", 14: "catorzè", 15: "quinzè", 16: "setzè", 17: "dissetè",
       18: "divuitè", 19: "dinovè"}
FIRST = {"m": ["primer", "segon", "tercer", "quart"], "f": ["primera", "segona", "tercera", "quarta"]}
# 10^exponent, singular, plural: the scale_noun entries of ca.json (miliard 10^9, bilió rank 2).
SCALES = [(6, "milió", "milions"), (9, "miliard", "miliards"), (12, "bilió", "bilions"), (18, "trilió", "trilions"),
          (24, "quadrilió", "quadrilions"), (30, "quintilió", "quintilions")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def cardinal(name, f):
    units = UNITS[:]
    if f:
        units[1], units[2] = "una", "dues"
    rules = [R("-x", "menys →→")] + [R(i, w) for i, w in enumerate(units)]
    rules += [R(20, "vint[-i-→→]", HYPHEN)] + [R(t, f"{w}[-→→]") for t, w in TENS.items() if t > 20]
    rules += [R(100, "cent[ →→]")]
    for h in range(2, 10):
        rules += [R(100 * h, f"{units[h] if h == 2 else UNITS[h]}-cent{'es' if f else 's'}[ →→]", GENDER if h == 2 else None)]
    rules += [R(1000, "mil[ →→]"), R(2000, "←← mil[ →→]")]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"un {singular}[ →→]"), R(2 * 10 ** exponent, f"←%cardinal-m← {plural}[ →→]")]
    return name, rules


def ordinal(name, f):
    """An ordinal: the cardinal with -è or -ena on its last word; 1 to 4 alone are "primer" to "quart"."""
    end = (lambda w: w[:-1] + "ena") if f else (lambda w: w)
    part = f"{name}-part"
    rules = [R("-x", "menys →→")] + [R(i + 1, w, ORDINAL if i == 0 else None) for i, w in enumerate(FIRST["f" if f else "m"])]
    rules += [R(5, f"=%{part}=")]
    tail = [R(n, end(w)) for n, w in ORD.items()]
    tail += [R(20, end("vintè")), R(21, f"vint-i-→%{part}→")]
    for t, w in TENS.items():
        if t > 20:
            tail += [R(t, end(w[:-1] + "è")), R(t + 1, f"{w}-→%{part}→")]
    tail += [R(100, end("centè")), R(101, f"cent →%{part}→")]
    for h in range(2, 10):
        tail += [R(100 * h, f"{UNITS[h]}-cent→%{part}-cents→")]
    tail += [R(1000, f"mil→%{part}-mil→"), R(2000, f"←%cardinal-m← mil→%{part}-mil→")]
    for exponent, singular, plural in SCALES:
        stem = plural[:-1]
        tail += [R(10 ** exponent, end(stem + "è"), SILVER_ORD), R(10 ** exponent + 1, f"un {singular} →%{part}→"),
                 R(2 * 10 ** exponent, f"←%cardinal-m← {stem}→%{part}-scale→")]
    return [(name, rules), (part, tail),
            (f"{part}-cents", [R(0, end("è")), R(1, f"s =%{part}=")]),
            (f"{part}-mil", [R(0, end("è")), R(1, f" =%{part}=")]),
            (f"{part}-scale", [R(0, end("è")), R(1, f"s =%{part}=")])]


sets = ([cardinal("cardinal-m", False), cardinal("cardinal-f", True)]
        + ordinal("ordinal-m", False) + ordinal("ordinal-f", True))
SOURCES = {
    "cardinal-m": CLDR + ", %spellout-cardinal-masculine, with the scale words of this lexicon. " + HYPHEN + ". "
                  + NUMBER_NAME,
    "cardinal-f": CLDR + ", %spellout-cardinal-feminine. " + GENDER,
    "ordinal-m": ORDINAL + ". " + SILVER_ORD,
    "ordinal-f": ORDINAL + "; " + SILVER_FEMININE + ". " + SILVER_ORD,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 36
block = {
    "source": CLDR + ". Catalan counts in the long scale of this lexicon: \"miliard\" for 10^9, \"bilió\" for 10^12 "
              "(DIEC2, «bilió»: \"Milió de milions.\").",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal-m", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                               "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}]},
                    "minimum": "1", "maximum": maximum},
    },
    "decimal": {"word": "coma", "places": 3, "source": CLDR + ", %spellout-numbering x.x: \"←← coma →→\"."},
    "scientific": {"times": "per deu elevat a", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "un {denominator}",
                 "plural": {"è": "ens", "ig": "igs", "ç": "ços", "t": "ts"},
                 "named": {"2": "mig", "3": "terç", "4": "quart"}, "denominator": "{cardinal}ens",
                 "ruleset": "ordinal-m-part", "numerator": "cardinal-m", "source": FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
