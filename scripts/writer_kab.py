"""Write the writer block of kab from the Kabyle pages in Papers/Languages/Berber/Kabyle/.

usage: python scripts/writer_kab.py [--check]

Where languagesandnumbers.com and the fr.wiktionary table differ, the writer takes the fr.wiktionary form, which
cites Dallet and Kossmann.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/kab.json"
PAPERS = "Papers/Languages/Berber/Kabyle/"
LN = f"languagesandnumbers.com (a hobby site), «Counting in Kabyle» ({PAPERS}languagesandnumbers_kabyle.html)"
WT = f"fr.wiktionary, «Modèle:cardinaux/kab» ({PAPERS}cardinaux_kab_frwiktionary_template.html)"
WP = f"en.wikipedia, «Kabyle grammar», Numerotation ({PAPERS}kabyle_grammar_enwiki_oldid1383353682.html)"
NATIVE = f"Mokraoui (2026), native answers on the Kabyle clock ({PAPERS}athmanemokraoui_2026_kabyle_clock_answers.md)"
UNITS_SRC = (WP + ": \"Only the first two numbers are Berber; for higher numbers, Arabic is used. They are yiwen (f. yiwet ) "
             "\\\"one\\\", sin (f. snat ) \\\"two\\\".\"; " + WT + ": \"0 ilem\", \"3 tlata\", \"13 telṭac\", \"17 sbeɛṭac\", "
             "\"18 tmenṭac\", \"80 tmanyin\", \"90 tesɛin\"; " + LN + ": \"ziṛu or ilem [0]\", \"tleṭṭac [13]\", "
             "\"tmanyina [80], and tsɛin [90]\": the writer takes the fr.wiktionary form")
COMPOUND = (LN + ": \"Compound numbers are formed starting with the unit, followed by the conjunction u , then the ten\", "
            "\"When compound, the units one and two are replaced by Arabic loanwords : waḥed [1] (from wahid ), tnayn [2] "
            "(from ithnan ). Thus, we get waḥed u ɛecrin [21], tnayn u tlatin [32]\"; " + WT + ": \"21 waḥed u ɛecrin\", "
            "\"22 tnayn u ɛecrin\"")
HUNDRED = (WT + ": \"100 mya 200 mitin 300 telt-mya 400 ṛebɛa-mya 500 xems-mya 600 sett-mya 700 sebɛ-mya 800 temn-mya "
           "900 tesɛa-mya\"; " + LN + ": \"Hundreds are formed starting with the root of the multiplier unit, linked with a "
           "hyphen to the word for hundred\"")
THOUSAND = (WT + ": \"1 000 alef 2 000 juǧ alaf 3 000 telt-alaf 4 000 ṛebɛ-alaf 5 000 xems-alaf 6 000 sett-alaf 7 000 "
            "sebɛ-alaf 8 000 temn-alaf 9 000 tesɛ-alaf\"; " + LN + ": \"ɛecṛ-alaf [10,000], ɛecrin-alaf [20,000], "
            "tlatin-alaf [30,000]… mya-alaf [100,000]\"")
SILVER_REST = ("SILVER: \"u\" before the rest of a hundred or a thousand, with waḥed and tnayn for 1 and 2 (\"mya u "
               "tnayn\"), follows \"When compound, the units one and two are replaced by Arabic loanwords\" of " + LN
               + "; no saved example")
SILVER_THOUSANDS = "SILVER: a count of thousands that is not round (\"waḥed u ɛecrin-alaf\"); no saved example"
SCALE = WT + ": \"1 000 000 = 1 000 1+1 amelyun\", \"amelyaṛ\""
SILVER_SCALE = ("SILVER: a count of millions takes the plural with no \"n\" (\"sin imelyunen\"), as " + THOUSAND
                + " (\"juǧ alaf\"); " + WP + " puts a counted noun in the genitive (\"sin n yirgazen\"); no saved example "
                "with a scale word")
ORDINAL = (WP + ": \"\\\"First\\\" and \\\"last\\\" are respectively amezwaru and aneggaru (regular adjectives). Other "
           "ordinals are formed with the prefix wis (f. tis ): wis sin \\\"second (m.)\\\", tis tlata \\\"third (f.)\\\"\"; "
           f"en.wiktionary, «wis» ({PAPERS}wis_enwiktionary.html): \"The particle is not used before yiwen ( “ one ” ) . "
           "The adjective amezwaru ( “ first ” ) is used instead of such an ordinal.\"; en.wiktionary, «amezwaru» "
           f"({PAPERS}amezwaru_enwiktionary.html): \"amezwaru ( feminine tamezwarut , masculine plural imezwura )\"")
HALF = (f"fr.wiktionary, «azgen» ({PAPERS}azgen_frwiktionary.html): \"Moitié\"; " + NATIVE + ": \"\\\"D lweḥda d wezgen\\\" "
        "(grammatically correct annexed state wezgen after the conjunction d)\"")
SILVER_FRACTION = ("SILVER: a denominator other than 2 reads as the count and the ordinal of the denominator (\"yiwen wis "
                   "tlata\"); no saved rule")

UNITS = {0: "ilem", 1: "yiwen", 2: "sin", 3: "tlata", 4: "ṛebɛa", 5: "xemsa", 6: "setta", 7: "sebɛa", 8: "tmanya",
         9: "tesɛa", 10: "ɛecṛa", 11: "ḥḍac", 12: "tnac", 13: "telṭac", 14: "ṛbeɛṭac", 15: "xemseṭṭac", 16: "seṭṭac",
         17: "sbeɛṭac", 18: "tmenṭac", 19: "tseɛṭac"}
TENS = {20: "ɛecrin", 30: "tlatin", 40: "ṛebɛin", 50: "xemsin", 60: "settin", 70: "sebɛin", 80: "tmanyin", 90: "tesɛin"}
HUNDREDS = {100: "mya", 200: "mitin", 300: "telt-mya", 400: "ṛebɛa-mya", 500: "xems-mya", 600: "sett-mya",
            700: "sebɛ-mya", 800: "temn-mya", 900: "tesɛa-mya"}
THOUSANDS = {1000: "alef", 2000: "juǧ alaf", 3000: "telt-alaf", 4000: "ṛebɛ-alaf", 5000: "xems-alaf", 6000: "sett-alaf",
             7000: "sebɛ-alaf", 8000: "temn-alaf", 9000: "tesɛ-alaf", 10000: "ɛecṛ-alaf"}
SCALES = [(6, "amelyun", "imelyunen"), (9, "amelyaṛ", "imelyaren")]


def R(value, text, source=None, radix=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    if radix:
        rule["radix"] = radix
    return rule


def cardinal(one, two):
    """``one`` and ``two`` are the words of 1 and 2: yiwen and sin alone, waḥed and tnayn in a compound."""
    rules = [R(i, {1: one, 2: two}.get(i, w)) for i, w in UNITS.items()]
    rules += [R(t, f"[→%rest→ u ]{w}") for t, w in TENS.items()]
    rules += [R(h, f"{w}[ u →%rest→]") for h, w in HUNDREDS.items()]
    rules += [R(t, f"{w}[ u →%rest→]") for t, w in THOUSANDS.items()]
    rules += [R(11000, "←%rest←-alaf[ u →%rest→]", SILVER_THOUSANDS, radix=1000)]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"{singular}[ u →%rest→]"),
                  R(2 * 10 ** exponent, f"←%cardinal← {plural}[ u →%rest→]", SILVER_SCALE if exponent == 6 else None)]
    return rules


def ordinal(prefix, first, count):
    return [R(1, first), R(2, f"{prefix} =%{count}=")]


sets = {"cardinal": cardinal("yiwen", "sin"), "cardinal-f": cardinal("yiwet", "snat"), "rest": cardinal("waḥed", "tnayn"),
        "ordinal": ordinal("wis", "amezwaru", "cardinal"), "ordinal-f": ordinal("tis", "tamezwarut", "cardinal-f")}
SOURCES = {
    "cardinal": ". ".join((UNITS_SRC, COMPOUND, HUNDRED, THOUSAND, SCALE, SILVER_REST, SILVER_THOUSANDS, SILVER_SCALE)),
    "cardinal-f": UNITS_SRC,
    "rest": COMPOUND + ". " + SILVER_REST,
    "ordinal": ORDINAL,
    "ordinal-f": ORDINAL,
}
rulesets = {name: {"source": SOURCES[name], "rules": rules} for name, rules in sets.items()}
maximum = "9" * 12


def form(masculine, feminine):
    return {"variants": [{"ruleset": masculine, "reason": "standard"}],
            "gender": {"masculine": [{"ruleset": masculine, "reason": "standard"}],
                       "feminine": [{"ruleset": feminine, "reason": "standard"}]},
            "maximum": maximum}


block = {
    "source": "The Kabyle pages in " + PAPERS + ": " + WT + ", " + LN + ", " + WP + " and " + NATIVE + ".",
    "rulesets": rulesets,
    "forms": {"cardinal": form("cardinal", "cardinal-f"), "ordinal": {**form("ordinal", "ordinal-f"), "minimum": "1"}},
    "decimal": {"word": None, "places": 3,
                "source": LN + ": the page names no word for the decimal mark, so a number with decimals has no reading."},
    "fraction": {"limit": 2, "named": {"2": "azgen"}, "mixed_named": {"2": "d wezgen"}, "denominator": "{cardinal}",
                 "single": "{denominator}", "source": HALF + ". " + SILVER_FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
