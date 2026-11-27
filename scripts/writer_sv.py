"""Write the writer block of sv from CLDR RBNF sv and the scale words of the lexicon.

usage: python scripts/writer_sv.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/sv.json"
CLDR = "CLDR RBNF sv (common/rbnf/sv.xml as shipped in unicode-rbnf 2.5.1)"
NUMBERING = (CLDR + ", %spellout-numbering: \"1: ett;\", \"20: tjugo[­→→];\", \"100: ←%spellout-numbering←­hundra[­→→];\", "
             "\"1000: ←%%spellout-numbering-t←­tusen[ →→];\" (%%spellout-numbering-t \"1: et;\"), \"1000000: en miljon[ →→];\", "
             "\"2000000: ←%spellout-cardinal-reale← miljoner[ →→];\"")
REALE = CLDR + ", %spellout-cardinal-reale: \"1: en;\", \"100: ←%spellout-cardinal-neuter←­hundra[­→→];\", \"1000: ettusen[ →→];\""
ORDINAL = (CLDR + ", %spellout-ordinal-neuter: \"1: första;\", \"2: andra;\", \"20: tjugo→%%ord-fem-nde→;\", \"100: "
           "←%spellout-numbering←­hundra→%%ord-fem-de→;\" (%%ord-fem-de \"0: de;\", \"1: ' =%spellout-ordinal-feminine=;\"), "
           "\"1000000: en miljon→%%ord-fem-te→;\", \"2000000: ←%spellout-cardinal-reale← miljon→%%ord-fem-teer→;\"")
MASCULINE = CLDR + ", %spellout-ordinal-masculine: \"1: förste;\", \"2: andre;\""
MSR = ("Språkrådet, Myndigheternas skrivregler, 8th ed. (Papers/Languages/Germanic/Swedish/myndigheternas-skrivregler-8-uppl.pdf)")
ONE_WORD = (MSR + ", §12.1.2: \"tvåtusenfemhundratrettiofem kronor (2 535 kr)\", \"en miljon, omkring tusen deltagare\"; "
            "§12.5: \"2 mdkr = två miljarder kronor\": one word below a million, a bare \"tusen\", and a scale word as a "
            "word of its own")
ETT = ("en.wikipedia «Swedish grammar», rev. 1385083823 (Papers/Languages/Germanic/Swedish/): \"The ett preceding hundra (100) "
       "and tusen (1000) is optional, but in compounds it is usually required\", \"147 etthundrafyrtisju\". SILVER: a "
       "secondary source; the bare \"hundra\" follows the bare \"tusen\" of " + MSR)
WIKI_ORD = ("en.wikipedia «Swedish grammar», rev. 1385083823: \"hundrade ( 100:e ), tusende ( 1000:e )\", \"miljonte "
            "(\"millionth\")\". SILVER: a secondary source; an ordinal below a million is one word, as the cardinal")
SILVER_FRACTION = ("en.wikipedia «Swedish grammar», rev. 1385083823 (Papers/Languages/Germanic/Swedish/): \"Rational numbers "
                   "are read as the cardinal number of the numerator followed by the ordinal number of the denominator "
                   "compounded with del or, if the numerator is higher than one, delar\", \"For those ordinal numbers that "
                   "are three syllables or longer and end in -de , that suffix is usually dropped in favour of -del(ar)\", "
                   "\"1 ⁄ 3 en tredjedel 3 ⁄ 4 tre fjärdedelar\". SILVER: a secondary source; \"en halv\", \"tre halva\"")

UNITS = "noll ett två tre fyra fem sex sju åtta nio tio elva tolv tretton fjorton femton sexton sjutton arton nitton".split()
TENS = {20: "tjugo", 30: "trettio", 40: "fyrtio", 50: "femtio", 60: "sextio", 70: "sjuttio", 80: "åttio", 90: "nittio"}
FIRST = "nollte första andra tredje fjärde femte sjätte sjunde åttonde nionde tionde elfte tolfte".split()
PART = {3: "tredjedel", 4: "fjärdedel", 5: "femtedel", 6: "sjättedel", 7: "sjundedel", 8: "åttondel", 9: "niondel",
        10: "tiondel", 11: "elftedel", 12: "tolftedel"}
# 10^exponent, singular, plural: the scale_noun entries of sv.json (long scale).
SCALES = [(6, "miljon", "miljoner"), (9, "miljard", "miljarder"), (12, "biljon", "biljoner"),
          (15, "biljard", "biljarder"), (18, "triljon", "triljoner")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def cardinal(name, one, thousands):
    """``name`` reads a number alone ("hundra", "tusen"); ``name``-in reads it inside a compound, where 100 and 1000
    take "ett" ("etthundra", "ettusen"). ``thousands`` is the rule set of the count before "tusen"."""
    inner = f"{name}-in"
    units = [R(0, "noll"), R(1, one)] + [R(i, w) for i, w in enumerate(UNITS) if i > 1]
    units += [R(t, f"{w}[→→]") for t, w in TENS.items()]
    top = [R("-x", "minus →→")] + units + [
        R(100, "hundra", ETT), R(101, f"etthundra→%{inner}→"), R(200, f"←%{inner}←hundra[→%{inner}→]"),
        R(1000, "tusen", ONE_WORD), R(1001, f"ettusen→%{inner}→"), R(2000, f"←%{thousands}←tusen[→%{inner}→]")]
    compound = units + [R(100, "etthundra[→→]"), R(200, "←←hundra[→→]"),
                        R(1000, "ettusen[→→]"), R(2000, f"←%{thousands}←tusen[→→]")]
    for exponent, singular, plural in SCALES:
        top += [R(10 ** exponent, f"en {singular}[ →→]"), R(2 * 10 ** exponent, f"←%cardinal-c← {plural}[ →→]")]
    return [(name, top), (inner, compound)]


def ordinal(name, first):
    """``name`` and ``name``-in, as the cardinal: "hundrade", "ettusenetthundrade"."""
    sets = []
    for own, hundred, thousand in ((name, "hundrade", "tusende"), (f"{name}-in", "etthundrade", "ettusende")):
        rest = f"{name}-in"
        rules = [R(i, w) for i, w in enumerate(first)] + [R(13, "=%numbering-in=de")]
        rules += [R(t, f"{w}→%{name}-nde→") for t, w in TENS.items()]
        rules += [R(100, hundred, WIKI_ORD if own == name else None), R(101, f"etthundra→%{rest}→"),
                  R(200, f"←%numbering-in←hundra→%{name}-de→"),
                  R(1000, thousand), R(1001, f"ettusen→%{rest}→"), R(2000, f"←%t←tusen→%{name}-de→")]
        if own == name:
            rules = [R("-x", "minus →→")] + rules
            for exponent, singular, _ in SCALES:
                rules += [R(10 ** exponent, f"[en ]{singular}→%{name}-te→"),
                          R(2 * 10 ** exponent, f"←%cardinal-c← {singular}→%{name}-teer→")]
        sets.append((own, rules))
    return sets + [(f"{name}-nde", [R(0, "nde"), R(1, f"=%{name}=")]),
                   (f"{name}-de", [R(0, "de"), R(1, f"=%{name}-in=")]), (f"{name}-te", [R(0, "te"), R(1, f" =%{name}=")]),
                   (f"{name}-teer", [R(0, "te"), R(1, f"er =%{name}=")])]


def denominator():
    rules = [R(1, "=%ordinal-in=del"), R(2, "=%ordinal-in=del")] + [R(n, w) for n, w in PART.items()] + [R(13, "=%numbering-in=del")]
    rules += [R(t, f"{w}→%denominator-nde→") for t, w in TENS.items()]
    rules += [R(100, "←%numbering-in←hundra→%denominator-de→"), R(1000, "←%t←tusen→%denominator-de→")]
    for exponent, singular, _ in SCALES:
        rules += [R(10 ** exponent, f"{singular}te→%denominator-de→"), R(2 * 10 ** exponent, f"←%t←{singular}te→%denominator-de→")]
    return [("denominator", rules), ("denominator-nde", [R(0, "ndel"), R(1, "=%denominator=")]),
            ("denominator-de", [R(0, "del"), R(1, "=%denominator=")])]


t = [R(1, "et")] + [R(i, w) for i, w in enumerate(UNITS) if i > 1] + [R(t, f"{w}[→%t→]") for t, w in TENS.items()]
t += [R(100, "etthundra[→%t→]"), R(200, "←%numbering-in←hundra[→%t→]")]
sets = (cardinal("numbering", "ett", "t") + cardinal("cardinal-c", "en", "cardinal-c-in") + [("t", t)]
        + ordinal("ordinal", FIRST) + ordinal("ordinal-m", ["nollte", "förste", "andre"] + FIRST[3:]) + denominator())
SOURCES = {
    "numbering": ONE_WORD + ". " + ETT + ". " + NUMBERING + ", with the scale words of this lexicon; the writer joins "
                 "the words below a million, as " + MSR,
    "cardinal-c": REALE + ": the common gender",
    "t": CLDR + ", %%spellout-numbering-t: \"1: et;\" before \"tusen\" (\"ettusen\", \"tjugoettusen\")",
    "ordinal": ORDINAL + ". " + WIKI_ORD,
    "ordinal-m": MASCULINE,
    "denominator": SILVER_FRACTION,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 21
block = {
    "source": CLDR + ". Swedish counts in the long scale of this lexicon: \"miljard\" for 10^9, \"biljon\" for 10^12.",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "numbering", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-c", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-c", "reason": "standard"}],
                                "neuter": [{"ruleset": "numbering", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"},
                                             {"ruleset": "ordinal", "reason": "variant_spelling"}]},
                    "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "komma", "places": 3, "source": CLDR + ", %spellout-numbering x.x: \"←← komma →→\"."},
    "scientific": {"times": "gånger tio upphöjt till", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "en {denominator}", "plural": {"halv": "halva", "del": "delar"},
                 "named": {"2": "halv", "100": "hundradel", "1000": "tusendel", "1000000": "miljontedel"}, "denominator": "{cardinal}del",
                 "ruleset": "denominator", "numerator": "cardinal-c", "source": SILVER_FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
