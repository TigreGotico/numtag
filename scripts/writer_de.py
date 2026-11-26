"""Write the writer block of de from the Amtliches Regelwerk (Rat für deutsche Rechtschreibung, 2024), CLDR RBNF de and
the scale words of the lexicon.

usage: python scripts/writer_de.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/de.json"
CLDR = "CLDR RBNF de (common/rbnf/de.xml as shipped in unicode-rbnf 2.5.1)"
RR = "Rat für deutsche Rechtschreibung, Amtliches Regelwerk (2024)"
ONE_WORD = (RR + ", § 36(1.6), p. 61: one word when \"es sich um mehrteilige Kardinalzahlen unter einer Million sowie "
            "allgemein um Ordinalzahlen handelt: dreizehn, siebenhundert, neunzehnhundertneunundachtzig; der siebzehnte "
            "Oktober, der einhundertste Geburtstag, der fünfhunderttausendste Fall, der zweimillionste Besucher\"")
SCALE = (RR + ", § 36(1.6), p. 61: \"Vgl. aber Substantive wie Dutzend, Million, Milliarde, Billion: zwei Dutzend "
         "Hühner, eine Million Teilnehmer, zwei Milliarden fünfhunderttausend Menschen\"")
FRACTION = (RR + ", § 56(6) E5, p. 87: \"In allen übrigen Fällen schreibt man Bruchzahlen auf -tel und -stel entsprechend "
            "§ 55 groß: ein Drittel, das erste Fünftel, neun Zehntel des Umsatzes, um drei Viertel größer\"")
SILVER_ORD = ("SILVER: an ordinal past a million with a rest keeps one word with the plural scale word "
              "(\"zweimillionenerste\"), by the one-word rule of § 36(1.6); no saved example")
SILVER_HALF = "SILVER: 1/2 reads \"ein Halb\" and n/2 \"Halbe\"; no saved rule"
DUDEN_EIN = ("Duden online, «hundertundein» (Papers/Languages/Germanic/German/duden_hundertundein.html): \"hundertundeinen "
             "Krimi lesen\"; «tausendundein»: \"tausendundeine Idee\", \"Märchen aus Tausendundeiner Nacht\": a final ein "
             "declines before a singular noun")
SILVER_CASE = ("IDS grammis, «Flexion der Adjektive» (Papers/Languages/Germanic/German/grammis_flexion_der_adjektive_3609.html): "
               "\"Ordinalzahl-Adjektive (z. B. der dritte Mann, das fünfte Gebot ) werden regelmäßig stark oder schwach "
               "flektiert.\" SILVER: the endings of each case and gender (weak: -e, -en; strong: -er, -e, -es, -en, -em); "
               "no saved table. " + CLDR + ", %spellout-ordinal-m, -n, -r, -s: "
               "\"0: =%spellout-ordinal=m;\"")
# The endings of the ordinal by case and gender: after an article, then with no article (strong).
WEAK = {"nominative": dict(masculine="e", feminine="e", neuter="e"),
        "accusative": dict(masculine="en", feminine="e", neuter="e"),
        "dative": dict(masculine="en", feminine="en", neuter="en"),
        "genitive": dict(masculine="en", feminine="en", neuter="en")}
STRONG = {"nominative": dict(masculine="er", feminine="e", neuter="es"),
          "accusative": dict(masculine="en", feminine="e", neuter="es"),
          "dative": dict(masculine="em", feminine="er", neuter="em"),
          "genitive": dict(masculine="en", feminine="er", neuter="en")}
# The cardinal 1 by case and gender, with no article (CLDR %spellout-cardinal-m, -n, -r, -s).
ONE = {"nominative": dict(masculine="ein", feminine="eine", neuter="ein"),
       "accusative": dict(masculine="einen", feminine="eine", neuter="ein"),
       "dative": dict(masculine="einem", feminine="einer", neuter="einem"),
       "genitive": dict(masculine="eines", feminine="einer", neuter="eines")}

UNITS = "null eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf dreizehn vierzehn fünfzehn sechzehn " \
        "siebzehn achtzehn neunzehn".split()
TENS = {20: "zwanzig", 30: "dreißig", 40: "vierzig", 50: "fünfzig", 60: "sechzig", 70: "siebzig", 80: "achtzig",
        90: "neunzig"}
FIRST = {1: "ers", 2: "zwei", 3: "drit", 4: "vier", 5: "fünf", 6: "sechs", 7: "sieb", 8: "ach"}
# 10^exponent, ordinal stem, singular, plural: the scale_noun entries of de.json (long scale).
SCALES = [(6, "million", "Million", "Millionen"), (9, "milliard", "Milliarde", "Milliarden"),
          (12, "billion", "Billion", "Billionen"), (15, "billiard", "Billiarde", "Billiarden"),
          (18, "trillion", "Trillion", "Trillionen"), (21, "trilliard", "Trilliarde", "Trilliarden")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def cardinal(name, one):
    """``one`` is "eins" (a bare number), "ein" or "eine" (before a noun); "einundzwanzig" in every case."""
    rules = [R("-x", "minus →→"), R(0, "null"), R(1, one)] + [R(i, w) for i, w in enumerate(UNITS) if i > 1]
    for t, w in TENS.items():
        rules += [R(t, w), R(t + 1, f"→%unit→und{w}")]
    rules += [R(100, "←%unit←hundert[→→]", ONE_WORD), R(1000, "←%cardinal-m←tausend[→→]")]
    for exponent, _, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"eine {singular}[ →→]", SCALE),
                  R(2 * 10 ** exponent, f"←%cardinal-f← {plural}[ →→]")]
    return name, rules


def ordinal(name, end):
    """``end`` is "te" (an ordinal) or "tel" (a fraction word): "dritte", "Drittel"; from 20 "ste" or "stel"."""
    rules = [R("-x", "minus →→"), R(0, "null" + end)] + [R(n, w + end) for n, w in FIRST.items()]
    rules += [R(9, f"=%numbering={end}"), R(20, f"=%numbering=s{end}")]
    rules += [R(100, f"←%unit←hundert→%{name}-tail→", ONE_WORD), R(1000, f"←%cardinal-m←tausend→%{name}-tail→")]
    sets = [(f"{name}-tail", [R(0, "s" + end), R(1, f"=%{name}=")])]
    for exponent, stem, singular, _ in SCALES:
        one = singular.lower()[len(stem):]  # "milliarde": "einmilliardeerste"
        rules += [R(10 ** exponent, f"←%cardinal-m←{stem}→%{name}-{stem}→", SILVER_ORD),
                  R(2 * 10 ** exponent, f"←%cardinal-m←{stem}→%{name}-{stem}s→")]
        sets += [(f"{name}-{stem}", [R(0, "s" + end), R(1, f"{one}=%{name}=")]),
                 (f"{name}-{stem}s", [R(0, "s" + end), R(1, f"en=%{name}=")])]
    return [(name, rules)] + sets


sets = ([cardinal("numbering", "eins"), cardinal("cardinal-m", "ein"), cardinal("cardinal-f", "eine"),
         ("unit", [R(1, "ein")] + [R(i, w) for i, w in enumerate(UNITS[:10]) if i > 1])]
        + [cardinal(f"cardinal-{one}", one) for one in ("einen", "einem", "einer", "eines")]
        + ordinal("ordinal", "te") + ordinal("fraction", "tel")
        + [s for end in ("ten", "ter", "tes", "tem") for s in ordinal(f"ordinal-{end[1:]}", end)])
CARDINAL_SET = {"ein": "cardinal-m", "eine": "cardinal-f"}
ORDINAL_SET = {"e": "ordinal", "en": "ordinal-en", "er": "ordinal-er", "es": "ordinal-es", "em": "ordinal-em"}
SOURCES = {
    "numbering": CLDR + ", %spellout-numbering, with the scale words of this lexicon. " + ONE_WORD + ". " + SCALE,
    "cardinal-m": CLDR + ", %spellout-cardinal-masculine: \"ein\" before a masculine or neuter noun",
    "cardinal-f": CLDR + ", %spellout-cardinal-feminine: \"eine\" before a feminine noun",
    "unit": CLDR + ", %spellout-cardinal-masculine: the units before \"und\" and \"hundert\" (\"einundzwanzig\", "
            "\"einhundert\")",
    "ordinal": CLDR + ", %spellout-ordinal, with one word past a million. " + ONE_WORD + ". " + SILVER_ORD,
    "fraction": FRACTION + ": the ordinal stem with -tel and -stel. " + SILVER_ORD,
}
SOURCES.update({f"cardinal-{one}": CLDR + f", %spellout-cardinal-{one[-1]}: \"1: {one};\". " + DUDEN_EIN
                for one in ("einen", "einem", "einer", "eines")})
SOURCES.update({f"ordinal-{end}": SOURCES["ordinal"] + ". " + SILVER_CASE for end in ("en", "er", "es", "em")})
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 24
block = {
    "source": CLDR + ". German counts in the long scale of this lexicon: \"Milliarde\" for 10^9, \"Billion\" for 10^12.",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "numbering", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "neuter": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}]},
                     "case": {case: {g: [{"ruleset": CARDINAL_SET.get(one, f"cardinal-{one}"), "reason": "standard"}]
                                     for g, one in by.items()} for case, by in ONE.items()},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal", "reason": "standard"}],
                    "case": {case: {g: [{"ruleset": ORDINAL_SET[WEAK[case][g]], "reason": "standard"},
                                        {"ruleset": ORDINAL_SET[STRONG[case][g]], "reason": "strong"}]
                                    for g in by} for case, by in WEAK.items()},
                    "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "Komma", "places": 3, "source": CLDR + ", %spellout-numbering x.x: \"←← Komma →→\"."},
    "scientific": {"times": "mal zehn hoch", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "ein {denominator}", "plural": {"halb": "halbe"},
                 "capitalise": True,
                 "named": {"2": "halb", "100": "hundertstel", "1000": "tausendstel", "1000000": "millionstel"},
                 "denominator": "{cardinal}stel", "ruleset": "fraction", "numerator": "cardinal-m",
                 "source": FRACTION + "; \"in fünf hundertstel Sekunden\" (6.1). " + SILVER_HALF + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
