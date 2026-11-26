"""Write the writer block of da from CLDR RBNF da, Dansk Sprognævn, Den Danske Ordbog and the scale words of the lexicon.

usage: python scripts/writer_da.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/da.json"
CLDR = "CLDR RBNF da (common/rbnf/da.xml as shipped in unicode-rbnf 2.5.1)"
PAPERS = "Papers/Languages/Germanic/Danish/"
DDO = f"Den Danske Ordbog (ordnet.dk, Wayback copies in {PAPERS})"
WORDS = (f"Dansk Sprognævn, sproget.dk «Et eller flere ord» ({PAPERS}sproget-dk-et-eller-flere-ord.html): \"Talord under "
         "100 skrives i ét ord: halvtreds femogfirs halvanden Talord over 100 skrives i to eller flere ord: to hundred(e) "
         "fire tusind(e) (og) tre hundred(e) (og) treoghalvfems (parentes om og og flertalsbøjningen angiver at disse "
         "valgfrit kan tages med eller udelades)\"; the writer takes \"hundrede\", \"tusind\" and \"og\"")
ARTICLE = (f"sproget.dk «Den 101. dalmatiner møder den 101. stryger» ({PAPERS}sproget-dk-den-101-dalmatiner.html)")
HUNDRED = (ARTICLE + ": \"en helt fjerde form, hundrede, er den korrekte form ifølge Retskrivningsordbogen\"; \"ordenstallet "
           "101. skulle bogstaveres og udtales hundred(e) (og) første\"")
TENS_ORD = (ARTICLE + ": \"Ordenstallet 40. skulle altså hedde fyrretyvende og 99. nioghalvfemsindstyvende. Reglen gælder "
            "stadig, men det vil sikkert overraske nogle, at Retskrivningsordbogen siden udgaven i 1986 også medtager de "
            "mere regelmæssigt dannede kortformer uden -tyve-, f.eks. fyrrende og nioghalvfemsende. Dansk Sprognævn regner "
            "dem dermed for lige så korrekte som de gamle, lange former. De nye korte former er indtil videre mest "
            "udbredte i talesproget.\"; the writer reads the short form first and the long form second")
NEUTER = (CLDR + ", %spellout-cardinal-common: \"2000: ←%spellout-cardinal-neuter← tusinde[ →%%and-small→];\": "
          "the count of \"tusind\" is neuter")
SILVER_TENS = ("SILVER: \"halvtredsende\", \"tressende\", \"halvfjerdsende\", \"firsende\" by the pattern of the short forms "
               "\"fyrrende\" and \"nioghalvfemsende\"; no saved example")
ORDINAL = (DDO + ", «anden»: \"som er nr. 2 i en rækkefølge\", neuter \"andet\"; «tyvende»: \"som er nr. 20 i en "
           "rækkefølge\", near \"enogtyvende toogtyvende treogtyvende\"; «million»: \"Se også millionte\"")
FRACTION = (DDO + ", «tredjedel»: \"fx to tredjedele = 2/3\"; «fjerdedel»: \"fx tre fjerdedele = 3/4\". " + ARTICLE
            + ": \"de talord, der står som førsteled i brøkangivelser med -del som andetled, er ordenstal, f.eks. i "
            "syvendedel, syttendedel og syvogtyvendedel\"")
SILVER_FRACTION = ("SILVER: \"en halv\" and \"tre halve\" (" + DDO + ", «halv»: \"fx en halv\"); a denominator past 100 with a "
                   "rest is one word with \"og\" (\"hundredeogførstedel\")")

UNITS = "nul en to tre fire fem seks syv otte ni ti elleve tolv tretten fjorten femten seksten sytten atten nitten".split()
TENS = {20: "tyve", 30: "tredive", 40: "fyrre", 50: "halvtreds", 60: "tres", 70: "halvfjerds", 80: "firs", 90: "halvfems"}
# The ordinal of a round ten: the short form, then the long form (sproget.dk).
TENS_ORDINAL = {20: ("tyvende", None), 30: ("tredivte", None), 40: ("fyrrende", "fyrretyvende"),
                50: ("halvtredsende", "halvtredsindstyvende"), 60: ("tressende", "tresindstyvende"),
                70: ("halvfjerdsende", "halvfjerdsindstyvende"), 80: ("firsende", "firsindstyvende"),
                90: ("halvfemsende", "halvfemsindstyvende")}
FIRST = "nulte første anden tredje fjerde femte sjette syvende ottende niende tiende ellevte tolvte".split()
# 10^exponent, singular, plural: the scale_noun entries of da.json (long scale).
SCALES = [(6, "million", "millioner"), (9, "milliard", "milliarder"), (12, "billion", "billioner"),
          (15, "billiard", "billiarder"), (18, "trillion", "trillioner")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def cardinal(name, one, count, joined):
    """``one`` is the bare 1: "en" or "et"; in a ten 1 is "en" ("enogtyve"), and after "hundrede" or "tusind" it
    agrees with the noun (``count``: "hundrede og et år"). The count of "tusind" is neuter ("tre hundrede og et
    tusind")."""
    rules = [R("-x", "minus →→"), R(0, "nul"), R(1, one)] + [R(i, w) for i, w in enumerate(UNITS) if i > 1]
    rules += [R(t, f"[→%count→og]{w}", WORDS if t == 50 else None) for t, w in TENS.items()]
    rules += [R(100, f"hundrede[ og →%{count}→]", HUNDRED), R(200, f"←%count-n← hundrede[ og →%{count}→]"),
              R(1000, f"tusind[ →%{joined}→]", WORDS), R(2000, f"←%count-n← tusind[ →%{joined}→]", NEUTER)]
    for exponent, singular, plural in SCALES:
        rules += [R(10 ** exponent, f"en {singular}[ →%{name}→]"), R(2 * 10 ** exponent, f"←%{name}← {plural}[ →%{name}→]")]
    return name, rules


def ordinal(name, two, long):
    """``two`` is "anden" or "andet"; ``long`` takes the long ten ("fyrretyvende")."""
    first = FIRST[:2] + [two] + FIRST[3:]
    rules = [R("-x", "minus →→")] + [R(i, w) for i, w in enumerate(first)] + [R(13, "=%count=de")]
    for t, (short, longer) in TENS_ORDINAL.items():
        word = longer if long and longer else short
        rules += [R(t, f"[→%count→og]{word}", TENS_ORD if t == 40 else SILVER_TENS if t == 50 and not long else None)]
    rules += [R(100, f"hundrede→%{name}-de→", HUNDRED), R(200, f"←%count← hundrede→%{name}-de→"),
              R(1000, f"tusind→%{name}-group→"), R(2000, f"←%count← tusind→%{name}-group→")]
    for exponent, singular, _ in SCALES:
        rules += [R(10 ** exponent, f"[en ]{singular}→%{name}-scale→", ORDINAL if exponent == 6 else None),
                  R(2 * 10 ** exponent, f"←%count← {singular}→%{name}-scales→")]
    # After a scale word the count of a lower scale word stays: "en billion en millionte", not 10^18.
    inner = [dict(r, text=r["text"].replace("[en ]", "en ")) for r in rules]
    return [(name, rules), (f"{name}-inner", inner),
            (f"{name}-de", [R(0, ""), R(1, f" og =%{name}=")]),
            (f"{name}-group", [R(0, "e"), R(1, f" og =%{name}="), R(100, f" =%{name}=")]),
            (f"{name}-scale", [R(0, "te"), R(1, f" =%{name}-inner=")]),
            (f"{name}-scales", [R(0, "te"), R(1, f"er =%{name}-inner=")])]


def denominator():
    """The word of a part: the ordinal and "del", one word ("tredjedel", "syvogtyvendedel", "hundrededel")."""
    rules = [R(i, f"{w}del") for i, w in enumerate(FIRST) if i > 2]
    rules += [R(13, "=%count=dedel")]
    rules += [R(t, f"[→%count→og]{short}del") for t, (short, _) in TENS_ORDINAL.items()]
    rules += [R(100, "hundrede[og→%ordinal-c→]del", SILVER_FRACTION), R(200, "←%count←hundrede[og→%ordinal-c→]del"),
              R(1000, "tusinde[og→%ordinal-c→]del"), R(2000, "←%count←tusinde[og→%ordinal-c→]del")]
    for exponent, singular, _ in SCALES:
        rules += [R(10 ** exponent, f"{singular}te[og→%ordinal-c→]del"),
                  R(2 * 10 ** exponent, f"←%count←{singular}te[og→%ordinal-c→]del")]
    return "denominator", rules


def count(name, one, joined):
    rules = [R(i, w) for i, w in enumerate(UNITS)] + [R(t, f"[→%count→og]{w}") for t, w in TENS.items()]
    rules[1] = R(1, one)
    rules += [R(100, "hundrede[ og →→]"), R(200, "←%count-n← hundrede[ og →→]"), R(1000, f"tusind[ →%{joined}→]"),
              R(2000, f"←%count-n← tusind[ →%{joined}→]")]
    return name, rules


sets = ([cardinal("cardinal-c", "en", "count", "and"), cardinal("cardinal-n", "et", "count-n", "and-n"),
         count("count", "en", "and"), count("count-n", "et", "and-n"),
         ("and", [R(0, "og =%count="), R(100, "=%count=")]), ("and-n", [R(0, "og =%count-n="), R(100, "=%count-n=")])]
        + ordinal("ordinal-c", "anden", False) + ordinal("ordinal-n", "andet", False)
        + ordinal("ordinal-long", "anden", True) + [denominator()])
SOURCES = {
    "cardinal-c": CLDR + ", %spellout-cardinal-common, with the scale words of this lexicon. " + WORDS + ". " + HUNDRED,
    "cardinal-n": CLDR + ", %spellout-cardinal-neuter: \"1: et;\"",
    "count": CLDR + ", %spellout-cardinal-common: a count below a million, with \"en\" for 1 (\"enogtyve\")",
    "and": CLDR + ", %%and-small: \"0: og =%spellout-cardinal-common=;\", \"100: =%spellout-cardinal-common=;\"",
    "ordinal-c": CLDR + ", %spellout-ordinal-common. " + ORDINAL + ". " + TENS_ORD + ". " + SILVER_TENS,
    "ordinal-n": CLDR + ", %spellout-ordinal-neuter: \"2: andet;\". " + ORDINAL,
    "ordinal-long": TENS_ORD,
    "denominator": FRACTION + ". " + SILVER_FRACTION,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.rsplit("-", 1)[0], "rules": rules}
            for name, rules in sets}
maximum = "9" * 21
block = {
    "source": CLDR + ". Danish counts in the long scale of this lexicon: " + DDO + ", «milliard»: \"(an)tallet "
              "1.000.000.000 (10 9 ); tusinde millioner\".",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal-c", "reason": "standard"}],
                     "gender": {"masculine": [{"ruleset": "cardinal-c", "reason": "standard"}],
                                "feminine": [{"ruleset": "cardinal-c", "reason": "standard"}],
                                "neuter": [{"ruleset": "cardinal-n", "reason": "standard"}]},
                     "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-c", "reason": "standard"},
                                 {"ruleset": "ordinal-long", "reason": "variant_spelling"}],
                    "gender": {"neuter": [{"ruleset": "ordinal-n", "reason": "standard"}]},
                    "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "komma", "places": 3, "source": CLDR + ", %spellout-cardinal-common x.x: \"←← komma →→\"."},
    "scientific": {"times": "gange ti i", "source": "Not checked against a grammar."},
    "fraction": {"mixed": False, "limit": 10, "single": "en {denominator}", "plural": {"halv": "halve", "del": "dele"},
                 "named": {"2": "halv"}, "denominator": "{cardinal}del", "ruleset": "denominator",
                 "numerator": "cardinal-c", "source": FRACTION + ". " + SILVER_FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
