"""Write the writer block of kab from the Kabyle pages in Papers/Languages/Berber/Kabyle/.

usage: python scripts/writer_kab.py [--check]

The standard reading takes the form of Dallet (1982) where the dictionary gives one: tmanyin, meyya, miṭin, alef,
alfin and the unit + u + ten compounds. Elsewhere, where languagesandnumbers.com and the fr.wiktionary table differ,
the writer takes the fr.wiktionary form. The fr.wiktionary forms of 100, 200 and 2000 (mya, mitin, juǧ alaf) stay
as a variant spelling.
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
DALLET = f"Dallet (1982), Dictionnaire kabyle-français ({PAPERS}dallet_1982_kf_p*.png)"
DALLET_SRC = (DALLET + ": p. 825 \"tmanyin ; ‖ Quatre-vingts.\"; p. 528 \"meyya ; fém.\", \"meyyat ‖ Cent. Centaine.\", "
              "\"meyyeṭ, dans les emprunts arabes : meyyeṭ esna, cent ans.\", \"miṭin / miṭayen / mitayen (duel ar.). "
              "‖ Deux cents.\"; p. 446 \"alef (wa)\", \"luluf / alaf ‖ Mille.\", \"alfin (wa) ‖ Deux mille.\"; "
              "p. 703 \"ṛebɛa w ɛecrin, vingt-quatre.\"; p. 756 \"sebɛa u ɛecrin, vingt-sept.\"")
NATIVE = f"Mokraoui (2026), native answers on the Kabyle clock ({PAPERS}athmanemokraoui_2026_kabyle_clock_answers.md)"
UNITS_SRC = (WP + ": \"Only the first two numbers are Berber; for higher numbers, Arabic is used. They are yiwen (f. yiwet ) "
             "\\\"one\\\", sin (f. snat ) \\\"two\\\".\"; " + WT + ": \"0 ilem\", \"3 tlata\", \"13 telṭac\", \"17 sbeɛṭac\", "
             "\"18 tmenṭac\", \"80 tmanyin\", \"90 tesɛin\"; " + LN + ": \"ziṛu or ilem [0]\", \"tleṭṭac [13]\", "
             "\"tmanyina [80], and tsɛin [90]\": the writer takes the fr.wiktionary form")
COMPOUND = (DALLET_SRC + "; " + LN + ": \"Compound numbers are formed starting with the unit, followed by the conjunction u , then the ten\", "
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
NUMBERS = f"Mokraoui (2026), native answers on Kabyle numbers ({PAPERS}athmanemokraoui_2026_kabyle_number_answers.md)"
NATIVE_N = (NUMBERS + ": \"8. 80: tmanyin | 13: telṭac | 90: tesɛin | 400: ṛebɛ-mya | 3,000: telt-alaf\", "
            "\"For 400 and 900 I write \\\"ṛebɛ-mya\\\" and \\\"tesɛ-mya\\\", without the final \\\"a\\\" that the PR has.\", "
            "\"2. 102: mya u tnayn = mya d sin (the same)\", \"5. 21,000: waḥed u ɛecrin n alef\", "
            "\"6. 10,000: ɛecṛ-alaf\", \"100,000: myat-alef\", \"200,000: mitin n alef\", \"300,000: telt-myat-alef\", "
            "\"Before \\\"alef\\\" or \\\"melyun\\\", the word for 100 can be \\\"myat\\\" (100,000, 300,000, 900,000,000), "
            "but 200,000 is \\\"mitin n alef\\\".\", \"1. Two million: sin n imelyunen = sin imelyan (the same)\", "
            "\"7. 900,000,000: tesɛ-myat melyun (main form). Also the same: tesɛ-mya imelyan, tesɛ-mya imelyunen\", "
            "\"4. After a count above 10, \\\"n\\\" comes before the noun: ɛecrin n wussan\"")
NATIVE_IMELYAN = ("The equal forms as a variant: \"d\" and the cardinal after a hundred, and a count of millions with "
                  "\"imelyan\" and no \"n\". " + NUMBERS + ": \"2. 102: mya u tnayn = mya d sin (the same)\", \"1. Two "
                  "million: sin n imelyunen = sin imelyan (the same)\", \"Also the same: tesɛ-mya imelyan\". SILVER: "
                  "\"imelyaren\" for the milliards and \"d\" after a hundred above 102; no saved example")
NATIVE_IMELYUNEN = ("The equal form as a variant: a count of millions with \"imelyunen\" and no \"n\". " + NUMBERS
                    + ": \"Also the same: tesɛ-mya imelyan, tesɛ-mya imelyunen\". SILVER: the same for a count other "
                    "than 900 and for the milliards; no saved example")
NATIVE_FRACTION = NUMBERS + ": \"3. 1/3: afkraḍ ; 1/4: afkuẓ ; 2/3: sin ifekṛad\""
SILVER_THOUSANDS = ("SILVER: a count of thousands from 11 to 99 other than 21 takes \"n alef\" (\"ḥḍac n alef\"), as "
                    "\"waḥed u ɛecrin n alef\"; a round ten keeps the form of " + LN + " (\"ɛecrin-alaf\"); no saved "
                    "example")
SILVER_HUNDRED_COUNTS = ("SILVER: a hundred count other than 100, 200, 300 and 900 takes the form of \"telt-myat-alef\" "
                         "and \"tesɛ-myat melyun\"; 200 before melyun takes \"mitin n\" as \"mitin n alef\"; a rest "
                         "after a hundred count of millions takes \"u\"; a count of thousands above 100 that is not a "
                         "round hundred keeps the hyphen (\"mya u waḥed u ɛecrin-alaf\"); no saved example")
SCALE = WT + ": \"1 000 000 = 1 000 1+1 amelyun\", \"amelyaṛ\""
SILVER_SCALE = ("SILVER: a count of milliards takes \"n\" and the plural (\"sin n imelyaren\", \"tesɛ-mya n "
                "imelyaren\"), as \"sin n imelyunen\"; no saved example")
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
ROOTS = {3: "telt", 4: "ṛebɛ", 5: "xems", 6: "sett", 7: "sebɛ", 8: "temn", 9: "tesɛ"}
HUNDREDS = {100: "mya", 200: "mitin", **{100 * k: f"{r}-mya" for k, r in ROOTS.items()}}
THOUSANDS = {1000: "alef", 2000: "alfin", **{1000 * k: f"{r}-alaf" for k, r in ROOTS.items()}, 10000: "ɛecṛ-alaf"}
HUNDREDS_WT = {**HUNDREDS, 100: "meyya", 200: "miṭin", 400: "ṛebɛa-mya", 900: "tesɛa-mya"}
THOUSANDS_WT = {**THOUSANDS, 2000: "juǧ alaf"}
# a hundred as a count before alef and melyun: "myat-alef", "mitin n alef", "telt-myat-alef", "tesɛ-myat melyun"
HUNDRED_COUNTS = {100: ("myat", "-"), 200: ("mitin", " n "), **{100 * k: (f"{r}-myat", "-") for k, r in ROOTS.items()}}
SCALES = [(6, "amelyun", "imelyunen", "melyun"), (9, "amelyaṛ", "imelyaren", None)]
# How a count above one names a scale word: "n" and the plural (default), or a plural with no "n".
STANDARD, IMELYAN, IMELYUNEN = "", "-imelyan", "-imelyunen"
NATIVE_PLURALS = {IMELYAN: {6: "imelyan", 9: "imelyaren"}, IMELYUNEN: {6: "imelyunen", 9: "imelyaren"}}


def R(value, text, source=None, radix=None, round=None):
    rule = {"value": str(value), "text": text + ";"}
    if round:
        rule["round"] = round + ";"
    if source:
        rule["source"] = source
    if radix:
        rule["radix"] = radix
    return rule


def cardinal(one, two, rest, count, thousands_count, scale_counts, hundreds=HUNDREDS, thousands=THOUSANDS, join=None):
    """``one`` and ``two`` are the words of 1 and 2: yiwen and sin alone, waḥed and tnayn in a compound. ``join``
    is the joiner and the rule set of the rest of a hundred: " u " and ``rest`` by default."""
    joiner, after = join or (" u ", rest)
    rules = [R(i, {1: one, 2: two}.get(i, w)) for i, w in UNITS.items()]
    rules += [R(t, f"[→%{rest}→ u ]{w}") for t, w in TENS.items()]
    rules += [R(h, f"{w}[{joiner}→%{after}→]") for h, w in hundreds.items()]
    rules += [R(t, f"{w}[ u →%{rest}→]") for t, w in thousands.items()]
    rules += [R(11000, f"←%{thousands_count}←[ u →%{rest}→]", radix=1000)]
    for (exponent, singular, _, _), name in zip(SCALES, scale_counts):
        rules += [R(10 ** exponent, f"{singular}[ u →%{rest}→]"),
                  R(2 * 10 ** exponent, f"←%{name}←[ u →%{rest}→]")]
    return rules


def thousands_count(rest):
    """A count of thousands: the thousand words to 10, then the count and "n alef", then a round hundred count."""
    rules = [R(k // 1000, w) for k, w in THOUSANDS.items()]
    rules += [R(11, f"=%{rest}= n alef", SILVER_THOUSANDS)]
    rules += [R(t, f"=%{rest}= n alef", round=f"{w}-alaf") for t, w in TENS.items()]
    rules += [R(h, f"=%{rest}=-alaf", SILVER_HUNDRED_COUNTS, round=f"{w}{sep}alef") for h, (w, sep) in HUNDRED_COUNTS.items()]
    return f"thousands-{rest}", rules


def scale_count(exponent, plural, bound, count, rest, style):
    """A count of millions or milliards from 2."""
    if style != STANDARD:
        return [R(2, f"=%{count}= {NATIVE_PLURALS[style][exponent]}")]
    rules = [R(2, f"=%{count}= n {plural}")]
    if bound is None:
        return rules
    rules += [R(h, f"{w}[ u →%{rest}→]{sep if sep == ' n ' else ' '}{bound}", SILVER_HUNDRED_COUNTS)
              for h, (w, sep) in HUNDRED_COUNTS.items()]
    return rules


sets = {}


def numbers(suffix, style=STANDARD, hundreds=HUNDREDS, thousands=THOUSANDS, join_d=False):
    """The cardinal, rest, thousand count and scale count rule sets of one spelling, named with ``suffix``."""
    card, rest = f"cardinal{suffix}", f"rest{suffix}"
    tc, tc_rules = thousands_count(rest)
    sets[tc] = tc_rules
    names = []
    for exponent, _, plural, bound in SCALES:
        name = f"scale{exponent}{suffix}"
        sets[name] = scale_count(exponent, plural, bound, card, rest, style)
        names.append(name)
    sets[card] = cardinal("yiwen", "sin", rest, card, tc, names, hundreds, thousands, (" d ", card) if join_d else None)
    sets[rest] = cardinal("waḥed", "tnayn", rest, card, tc, names, hundreds, thousands)


numbers("")
numbers("-wt", hundreds=HUNDREDS_WT, thousands=THOUSANDS_WT)
numbers(IMELYAN, IMELYAN, join_d=True)
numbers(IMELYUNEN, IMELYUNEN)
sets["cardinal-f"] = cardinal("yiwet", "snat", "rest", "cardinal", "thousands-rest", ["scale6", "scale9"])
sets["ordinal"] = [R(1, "amezwaru"), R(2, "wis =%cardinal=")]
sets["ordinal-f"] = [R(1, "tamezwarut"), R(2, "tis =%cardinal-f=")]
WT_VARIANT = ("The forms of Dallet and fr.wiktionary as a variant spelling. " + DALLET_SRC + ". " + HUNDRED + ". "
              + THOUSAND + ". " + COMPOUND + ". " + SILVER_REST)
SOURCES = {
    "cardinal": ". ".join((NATIVE_N, UNITS_SRC, COMPOUND, HUNDRED, THOUSAND, SCALE, SILVER_REST)),
    "cardinal-f": UNITS_SRC,
    "rest": COMPOUND + ". " + SILVER_REST,
    "cardinal-wt": WT_VARIANT,
    "rest-wt": WT_VARIANT,
    "cardinal" + IMELYAN: NATIVE_IMELYAN,
    "rest" + IMELYAN: NATIVE_IMELYAN,
    "cardinal" + IMELYUNEN: NATIVE_IMELYUNEN,
    "rest" + IMELYUNEN: NATIVE_IMELYUNEN,
    "ordinal": ORDINAL,
    "ordinal-f": ORDINAL,
}
for name in sets:
    if name.startswith("thousands-"):
        SOURCES[name] = NATIVE_N
    elif name.startswith("scale"):
        SOURCES[name] = NATIVE_N + ". " + SCALE + ". " + SILVER_SCALE
rulesets = {name: {"source": SOURCES[name], "rules": rules} for name, rules in sets.items()}
maximum = "9" * 12


def form(masculine, feminine, *variants):
    spellings = [{"ruleset": masculine, "reason": "standard"}]
    spellings += [{"ruleset": variant, "reason": "variant_spelling"} for variant in variants]
    return {"variants": spellings,
            "gender": {"masculine": spellings,
                       "feminine": [{"ruleset": feminine, "reason": "standard"}]},
            "maximum": maximum}


block = {
    "source": "The Kabyle pages in " + PAPERS + ": " + DALLET + ", " + WT + ", " + LN + ", " + WP + ", " + NATIVE + " and " + NUMBERS + ".",
    "rulesets": rulesets,
    "forms": {"cardinal": form("cardinal", "cardinal-f", "cardinal-wt", "cardinal" + IMELYAN, "cardinal" + IMELYUNEN), "ordinal": {**form("ordinal", "ordinal-f"), "minimum": "1"}},
    "decimal": {"word": None, "places": 3,
                "source": LN + ": the page names no word for the decimal mark, so a number with decimals has no reading."},
    "fraction": {"limit": 4, "named": {"2": "azgen", "3": "afkraḍ", "4": "afkuẓ"}, "plural": {"afkraḍ": "ifekṛad"},
                 "mixed_named": {"2": "d wezgen"}, "denominator": "{cardinal}", "single": "{denominator}",
                 "source": HALF + ". " + NATIVE_FRACTION + ". " + SILVER_FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
