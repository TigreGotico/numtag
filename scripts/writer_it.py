"""Write the writer block of it from CLDR RBNF it, the scale words of the lexicon and the Accademia della Crusca.

usage: python scripts/writer_it.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/it.json"
CLDR = "CLDR RBNF it (common/rbnf/it.xml as shipped in unicode-rbnf 2.5.1)"
CRUSCA_108 = ("Accademia della Crusca, consulenza 1077: \"108: centootto, meno bene centotto\", and \"101: centouno "
              "o, ormai abbastanza raro, centuno\"; Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali», ex. 29: "
              "\"centootto [raramente centotto]\"")
ONP = "ovos-number-parser 0.31.5a2 numbers_it.py"
CRUSCA_1077 = "Accademia della Crusca, consulenza 1077"
TRECCANI_FRAZIONARI = ("Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali», § 2.3 Frazionari: \"formati da un "
                       "aggettivo numerale cardinale e da un ordinale (un terzo, due quinti, quattro decimi, ecc.)\"")
TRECCANI_ORDINALE = ("Vocabolario Treccani, «ordinale»: the joined form \"è pressoché l'unico per alcuni ordinali per i "
                     "quali l'altro tipo sarebbe sentito come poco eufonico: centesimo decimo, millesimo primo, millesimo "
                     "secondo, millesimo decimo, millesimo undecimo o undicesimo, ecc. (in questi casi la grafia staccata "
                     "è preferita)\". The writer splits these cases only: a round hundred and 10, and \"mille\" and 1, 2, "
                     "10 or 11")
CRUSCA_COUNT = (CRUSCA_1077 + ": \"21.000: ventunomila o ventunmila: entrambe le forme vanno bene\", the full form "
                "first; Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali», ex. 24-25: in a compound «uno» "
                "\"può essere apocopato\", so the apocope is optional and the full form is the unmarked one: "
                "\"ventunomila\", \"ventuno milioni\"")

UNITS = ("zero uno due tre quattro cinque sei sette otto nove dieci undici dodici tredici quattordici quindici "
         "sedici diciassette diciotto diciannove").split()
TENS = [("vent", "i"), ("trent", "a"), ("quarant", "a"), ("cinquant", "a"), ("sessant", "a"), ("settant", "a"),
        ("ottant", "a"), ("novant", "a")]
ORDINALS = "zeresimo primo secondo terzo quarto quinto sesto settimo ottavo nono decimo".split()
ORD_TAIL = {1: "unesimo", 2: "duesimo", 3: "treesimo", 4: "quattresimo", 5: "cinquesimo", 6: "seiesimo",
            7: "settesimo", 8: "ottesimo", 9: "novesimo"}
# 10^exponent, singular, plural: the long scale of CLDR it and the scale_noun entries of the lexicon.
SCALES = [(6, "milione", "milioni"), (9, "miliardo", "miliardi"), (12, "bilione", "bilioni"),
          (15, "biliardo", "biliardi"), (18, "trilione", "trilioni"), (24, "quadrilione", "quadrilioni")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def tail(name, vowel, one, three, base):
    """The units after a tens stem or "cent": the stem vowel drops before "uno" and "otto" ("ventuno")."""
    rules = [R(0, vowel), R(1, vowel * (vowel == "o") + one), R(2, f"{vowel}=%{base}="), R(3, vowel + three),
             R(4, f"{vowel}=%{base}=")]
    if vowel == "o":  # after "cento": "centootto" (Crusca), "centottanta"
        rules += [R(80, f"=%{base}="), R(90, f"o=%{base}=")]
    else:
        rules += [R(8, f"=%{base}="), R(9, f"{vowel}=%{base}=")]
    return name, rules


def cardinal(name, one, three="tré"):
    """A cardinal rule set and its tails. ``one`` is "uno", "un" or "una"; "tre" loses its accent before "mila"."""
    sets = [tail(f"{name}-{v}", v, one, three, name) for v in "iao"]
    rules = [R("-x", "meno →→")] + [R(i, w) for i, w in enumerate(UNITS)]
    rules[2] = R(1, one)
    rules += [R(20 + 10 * i, f"{stem}→%{name}-{v}→") for i, (stem, v) in enumerate(TENS)]
    rules += [R(100, f"cent→%{name}-o→", CRUSCA_108), R(200, f"←%{name}←cent→%{name}-o→")]
    if three == "tré":
        rules += [R(1000, "mille[→→]"), R(2000, "←%count-mila←mila[→→]")]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"un {singular}[ →→]"),
                  R(2 * 10 ** exponent, f"←%numbering← {plural}[ →→]", CRUSCA_COUNT)]
    return [(name, rules)] + sets


def ordinal(name, e):
    """An ordinal rule set and its tails, with the ending ``e``: "o" (masculine) or "a" (feminine)."""
    def esim(word):
        return word[:-1] + e
    rules = [R("-x", "meno →→")] + [R(i, esim(w)) for i, w in enumerate(ORDINALS)]
    rules += [R(10 + i, esim(f"{w[:-1]}esimo")) for i, w in enumerate(UNITS[10:]) if i]
    rules += [R(20 + 10 * i, f"{stem}→%{name}-{v}→") for i, (stem, v) in enumerate(TENS)]
    rules += [R(100, f"cent→%{name}-o→"), R(200, f"←%cardinal-m←cent→%{name}-o→"),
              R(1000, f"mill→%{name}-mille→"), R(2000, f"←%count-mila←mil→%{name}-mila→")]
    for exponent, singular, _ in SCALES:
        stem, joined = singular[:-1], f"{name}-scale" if singular.endswith("e") else f"{name}-o"
        rules += [R(10 ** exponent, f"{stem}→%{joined}→"), R(2 * 10 ** exponent, f"←%count-mila←{stem}→%{joined}→")]
    sets = [(name, rules)]
    for v in "iao":
        tails = [R(0, esim("esimo"))] + [R(n, (v if n != 1 and (n != 8 or v == "o") else "") + esim(w)) for n, w in ORD_TAIL.items()]
        tails += [R(10, f"{esim('esimo')} {esim('decimo')}", TRECCANI_ORDINALE), R(11, f"o=%{name}=")] if v == "o" else []
        if v == "o":  # after "cent": "centottantesimo"
            tails += [R(80, f"=%{name}="), R(90, f"o=%{name}=")]
        sets.append((f"{name}-{v}", tails))
    # after "mill": "millesimo", "milleunesimo"; after "mil" of a count of thousands: "duemillesimo", "duemilaunesimo"
    split = [R(1, f"{esim('esimo')} {esim('primo')}", TRECCANI_ORDINALE), R(2, f"{esim('esimo')} {esim('secondo')}"),
             R(3, "e=%" + name + "-unit="), R(10, f"{esim('esimo')} {esim('decimo')}"),
             R(11, f"{esim('esimo')} {esim('undicesimo')}"), R(12, "e=%" + name + "-unit=")]
    sets.append((f"{name}-mille", [R(0, esim("esimo"))] + split))
    sets.append((f"{name}-scale", [R(0, esim("esimo")), R(1, "e=%" + name + "-unit=")]))
    sets.append((f"{name}-mila", [R(0, esim("lesimo")), R(1, "a=%" + name + "-unit=")]))
    sets.append((f"{name}-unit", [R(n, esim(w)) for n, w in ORD_TAIL.items()] + [R(10, f"=%{name}=")]))
    return sets


sets = (cardinal("numbering", "uno") + cardinal("cardinal-m", "un") + [("cardinal-f", [R("-x", "meno →→"), R(0, "zero"), R(1, "una"), R(2, "=%numbering=")])]
        + cardinal("count-mila", "uno", three="tre") + ordinal("ordinal-m", "o") + ordinal("ordinal-f", "a"))
SOURCES = {
    "numbering": CLDR + ", %spellout-numbering, with the scale words of this lexicon. " + CRUSCA_108,
    "cardinal-m": CLDR + ", %spellout-cardinal-masculine: \"un\" and \"ventun\" before a noun",
    "cardinal-f": CLDR + ", %spellout-cardinal-feminine, with \"una\" for a bare 1 only. " + CRUSCA_1077
                  + ": \"In passato era normale femminilizzare anche i composti di uno, mentre oggi questo è meno "
                  "comune\", so 21 is \"ventuno\"",
    "count-mila": CLDR + ", %%msc-no-final: the count before \"mila\" ends in \"tre\" with no accent (\"ventitremila\"). "
                  + CRUSCA_COUNT,
    "ordinal-m": CLDR + ", %spellout-ordinal-masculine (\"2000: ←%spellout-cardinal-masculine←mille→%%ordinal-esimo→\": "
                 "\"duemillesimo\"), with \"centoottesimo\" from the cardinal \"centootto\". " + CRUSCA_108,
    "ordinal-f": CLDR + ", %spellout-ordinal-feminine, with the changes of ordinal-m",
}
rulesets = {name: {"source": SOURCES.get(name) or "a tail of " + SOURCES[name.rsplit("-", 1)[0]].split(",")[0],
                   "rules": rules} for name, rules in sets}
maximum = "9" * 30
block = {
    "source": CLDR + ". Italian counts in the long scale: \"miliardo\" for 10^9 and \"bilione\" for 10^12.",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "numbering", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                               "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}]},
                    "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "virgola", "places": 3,
                "source": CLDR + ", %spellout-numbering x,x: \"←← virgola →→\". " + ONP + " reads each decimal digit."},
    "scientific": {"times": "per dieci elevato alla", "source": "Not checked against a grammar: the phrase of " + ONP + ", \"uno per dieci elevato alla sei\"."},
    "fraction": {"mixed": False, "limit": 10, "single": "un {denominator}", "plural": {"o": "i", "a": "e"},
                 "named": dict(zip(map(str, range(2, 11)), ["mezzo"] + ORDINALS[3:])),
                 "denominator": "{cardinal}esimi", "ruleset": "ordinal-m", "numerator": "cardinal-m",
                 "source": TRECCANI_FRAZIONARI + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
