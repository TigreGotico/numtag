"""Write the writer block of pl from Jagodziński «Tworzenie i składnia liczebników», zpe.gov.pl «Odmiana liczebnika»,
CLDR RBNF pl and the scale words of the lexicon.

usage: python scripts/writer_pl.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/pl.json"
CLDR = "CLDR RBNF pl (common/rbnf/pl.xml as shipped in unicode-rbnf 2.5.1)"
JG = "G. Jagodziński, «Tworzenie i składnia liczebników» (Papers/Languages/Slavic/Polish/jagodzinski-liczebniki.html)"
ZPE = "zpe.gov.pl, «Odmiana liczebnika i zaimka» (Papers/Languages/Slavic/Polish/zpe-odmiana-liczebnika.html)"
JOIN = JG + ": \"Liczebniki wielowyrazowe to proste zestawienia liczebników połączonych\" (\"tysiąc pięćset dwadzieścia trzy\")"
JEDEN = (JG + ": \"dwadzieścia jeden jabłek, dwudziestu jeden kolegów, tysiąc jeden żołnierzy\": \"jeden\" inside a number "
         "does not change; \"widzę tysiąc dwie gwiazdy\": the last word agrees with the noun")
SCALE = (JG + ": \"występuje przy mnożnych zakończonych na 2, 3, 4 z wyjątkiem zakończonych na 12, 13, 14\"; \"pięć tysięcy\", "
         "\"dwanaście milionów\", \"trzydzieści jeden miliardów\"; \"dwa tysiące dwie dziewczyny\": the count of a scale word "
         "has the masculine form; \"sto jeden tysięcy\", and a lone scale word has no count (\"tysiąc\")")
ORDINAL = (JG + ": \"21. – dwudziesty pierwszy, 63. – sześćdziesiąty trzeci\"; \"101. – sto pierwszy, 1016. – tysiąc "
           "szesnasty, 2150. – dwa tysiące sto pięćdziesiąty\"; \"2000. – dwutysięczny, 2100. – dwa tysiące setny\". " + ZPE
           + ": \"tysiąc osiemset pierwszy\", \"tysiąc osiemsetny\"")
SILVER_ROUND = (JG + ": \"2000. – dwutysięczny\", \"1 500 000. – milion pięćsettysięczny\": a round multiple of a scale "
                "word joins its count to the ordinal. SILVER: the joined forms of the other counts (\"trzytysięczny\", "
                "\"dwudziestopięciotysięczny\"), and the genitive of 100 to 400 (\"stutysięczny\", \"trzystutysięczny\") "
                "beside the nominative of 500 to 900 (\"pięćsettysięczny\"); no saved example")
FRACTION = (JG + ": \"z dwoma trzecimi bochenka, w jednej czwartej miast\", \"trzy czwarte pizzy\": the numerator is a "
            "feminine cardinal and the part a feminine ordinal; after 2, 3 or 4 the part is a nominative plural "
            "(\"trzy czwarte\"). SILVER: after 5 or more, and after a count that ends in 1 above 1, the part is a genitive "
            "plural (\"pięć ósmych\"), by the agreement rule of 5 and more; no saved example")

UNITS = ("zero jeden dwa trzy cztery pięć sześć siedem osiem dziewięć dziesięć jedenaście dwanaście trzynaście czternaście "
         "piętnaście szesnaście siedemnaście osiemnaście dziewiętnaście").split()
TENS = {20: "dwadzieścia", 30: "trzydzieści", 40: "czterdzieści", 50: "pięćdziesiąt", 60: "sześćdziesiąt",
        70: "siedemdziesiąt", 80: "osiemdziesiąt", 90: "dziewięćdziesiąt"}
HUNDREDS = {100: "sto", 200: "dwieście", 300: "trzysta", 400: "czterysta", 500: "pięćset", 600: "sześćset",
            700: "siedemset", 800: "osiemset", 900: "dziewięćset"}
FIRST = ("zerowy pierwszy drugi trzeci czwarty piąty szósty siódmy ósmy dziewiąty dziesiąty jedenasty dwunasty trzynasty "
         "czternasty piętnasty szesnasty siedemnasty osiemnasty dziewiętnasty").split()
TENTHS = {20: "dwudziesty", 30: "trzydziesty", 40: "czterdziesty", 50: "pięćdziesiąty", 60: "sześćdziesiąty",
          70: "siedemdziesiąty", 80: "osiemdziesiąty", 90: "dziewięćdziesiąty"}
HUNDREDTHS = {100: "setny", 200: "dwusetny", 300: "trzechsetny", 400: "czterechsetny", 500: "pięćsetny",
              600: "sześćsetny", 700: "siedemsetny", 800: "osiemsetny", 900: "dziewięćsetny"}
TEEN_PREFIX = ("dziesięcio jedenasto dwunasto trzynasto czternasto piętnasto szesnasto siedemnasto osiemnasto "
               "dziewiętnasto").split()
TEN_PREFIX = {20: "dwudziesto", 30: "trzydziesto", 40: "czterdziesto", 50: "pięćdziesięcio", 60: "sześćdziesięcio",
              70: "siedemdziesięcio", 80: "osiemdziesięcio", 90: "dziewięćdziesięcio"}
PREFIX = {2: "dwu", 3: "trzy", 4: "cztero", 5: "pięcio", 6: "sześcio", 7: "siedmio", 8: "ośmio", 9: "dziewięcio"}
# 10^exponent, singular, few (after 2-4), other, ordinal: the scale words of pl.json (long scale).
SCALES = [(3, "tysiąc", "tysiące", "tysięcy", "tysięczny"), (6, "milion", "miliony", "milionów", "milionowy"),
          (9, "miliard", "miliardy", "miliardów", "miliardowy"), (12, "bilion", "biliony", "bilionów", "bilionowy"),
          (15, "biliard", "biliardy", "biliardów", "biliardowy"), (18, "trylion", "tryliony", "trylionów", "trylionowy")]
GENDER = {"m": ("jeden", "dwa"), "f": ("jedna", "dwie"), "n": ("jedno", "dwa")}


def R(value, text, source=None, radix=None):
    rule = {"value": str(value), "text": text + ";"}
    if radix:
        rule["radix"] = radix
    if source:
        rule["source"] = source
    return rule


def tail(g):
    """1 to the maximum inside a number: "jeden" for 1, the gender form of 2."""
    rules = [R(1, "jeden", JEDEN), R(2, GENDER[g][1])] + [R(i, w) for i, w in enumerate(UNITS) if i > 2]
    rules += [R(t, f"{w}[ →→]") for t, w in TENS.items()] + [R(h, f"{w}[ →→]", JOIN if h == 100 else None)
                                                            for h, w in HUNDREDS.items()]
    for exponent, singular, *_ in SCALES:
        rules += [R(10 ** exponent, f"{singular}[ →→]"), R(2 * 10 ** exponent, f"←%sc-{singular}←[ →→]")]
    return f"tail-{g}", rules


def cardinal(g):
    return f"cardinal-{g}", [R("-x", "minus →→"), R(0, "zero"), R(1, GENDER[g][0]), R(2, f"=%tail-{g}=")]


def scale_count(singular, few, other):
    """The count of a scale word and the word: "dwa tysiące", "pięć tysięcy", "dwadzieścia dwa tysiące"."""
    rules = [R(0, other), R(1, f"jeden {other}"), R(2, f"=%tail-m= {few}", SCALE if singular == "tysiąc" else None),
             R(5, f"=%tail-m= {other}")]
    rules += [R(t, f"{w} →→") for t, w in TENS.items()] + [R(h, f"{w} →→") for h, w in HUNDREDS.items()]
    return f"sc-{singular}", rules


def form(word, g):
    """The ordinal ending of the gender: m "-y"/"-i", f "-a", n and the plural "-e", gen. plural "-ych"/"-ich"."""
    if g == "m":
        return word
    soft = word.endswith("i")
    stem = word[:-1]
    if g == "f":
        return stem + ("ia" if word.endswith("ci") else "a")
    if g == "n":
        return stem + ("ie" if soft else "e")
    return stem + ("ich" if soft else "ych")


def ordinal(g):
    name = f"ordinal-{g}"
    rules = [R("-x", "minus →→")] + [R(i, form(w, g), ORDINAL if i == 1 else None) for i, w in enumerate(FIRST)]
    rules += [R(t, f"{form(w, g)}[ →→]") for t, w in TENTHS.items()]
    rules += [dict(R(h, f"{w} →→"), round=form(HUNDREDTHS[h], g) + ";") for h, w in HUNDREDS.items()]
    for exponent, singular, _, _, ordinal_word in SCALES:
        rules += [dict(R(10 ** exponent, f"{singular} →→"), round=form(ordinal_word, g) + ";"),
                  dict(R(2 * 10 ** exponent, f"←%sc-{singular}← →→", SILVER_ROUND if exponent == 3 else None),
                       round=f"←%prefix←{form(ordinal_word, g)};")]
    return [(name, rules)]


def prefix():
    """The count joined before the ordinal of a round scale word: "dwu" in "dwutysięczny", "pięćset" in
    "pięćsettysięczny"."""
    rules = [R(1, "jedno")] + [R(k, w) for k, w in PREFIX.items()]
    rules += [R(10 + i, w) for i, w in enumerate(TEEN_PREFIX)]
    rules += [R(t, f"{w}[→→]") for t, w in TEN_PREFIX.items()]
    rules += [R(h, f"{ {100: 'stu', 200: 'dwustu', 300: 'trzystu', 400: 'czterystu'}.get(h, w)}[→→]")
              for h, w in HUNDREDS.items()]
    return "prefix", rules


sets = ([tail(g) for g in GENDER] + [cardinal(g) for g in GENDER]
        + [scale_count(singular, few, other) for _, singular, few, other, _ in SCALES]
        + [s for g in ("m", "f", "n", "g") for s in ordinal(g)] + [prefix()])
SOURCES = {
    "cardinal-m": CLDR + ", %spellout-cardinal-masculine, with the scale words of this lexicon. " + JOIN + ". " + SCALE,
    "cardinal-f": CLDR + ", %spellout-cardinal-feminine: \"1: jedna;\", \"2: dwie;\". " + JEDEN,
    "cardinal-n": CLDR + ", %spellout-cardinal-neuter: \"1: jedno;\". " + JEDEN,
    "ordinal-m": ORDINAL + ". " + SILVER_ROUND,
    "ordinal-f": ORDINAL + ": the feminine \"-a\". " + FRACTION,
    "ordinal-n": ORDINAL + ": the neuter and the nominative plural \"-e\". " + FRACTION,
    "ordinal-g": FRACTION,
}
SOURCES.update({f"tail-{g}": JEDEN for g in GENDER})
SOURCES.update({f"sc-{s}": SCALE for _, s, *_ in SCALES})
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 21
block = {
    "source": CLDR + ". Polish counts in the long scale of this lexicon: \"miliard\" for 10^9, \"bilion\" for 10^12.",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal-m", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-m", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-f", "reason": "standard"}],
                                "neuter": [{"ruleset": "cardinal-n", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                               "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}],
                               "neuter": [{"ruleset": "ordinal-n", "reason": "standard"}]},
                    "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "przecinek", "places": 3,
                "source": CLDR + ", %spellout-cardinal-masculine x.x: \"←%spellout-cardinal-masculine← przecinek "
                                 "→%%spellout-fraction→\"."},
    "scientific": {"times": "razy dziesięć do potęgi", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "jedna {denominator}", "named": {},
                 "denominator": "{cardinal}", "numerator": "cardinal-f",
                 "by_count": [{"count": "1", "ruleset": "ordinal-f"},
                              {"count": r"(\d*[02-9])?[234]", "ruleset": "ordinal-n"},
                              {"count": r"\d+", "ruleset": "ordinal-g"}],
                 "source": FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
