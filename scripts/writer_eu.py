"""Write the writer block of eu from the norms of Euskaltzaindia and the scale words of the lexicon.

usage: python scripts/writer_eu.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/eu.json"
PAPERS = "Papers/Languages/Iberian/Basque/"
N7 = f"Euskaltzaindia, 7. araua, «Zenbakien idazkeraz» ({PAPERS}euskaltzaindia_araua07_zenbakien_idazkera.pdf)"
N18 = f"Euskaltzaindia, 18. araua, «Ordinalen eta banatzaileen idazkera» ({PAPERS}euskaltzaindia_araua18_ordinalak.pdf)"
N203 = f"Euskaltzaindia, 203. araua, EBO (VI), «Zenbakizko adierazpenak» ({PAPERS}euskaltzaindia_araua203_gramatika_arauak.pdf)"
TABLE = (N7 + ": \"18 hemezortzi (hamazortzi)\", \"21 hogeita bat\", \"30 hogeita hamar\", \"60 hirurogei (hiruretan hogei)\", "
         "\"101 ehun eta bat\", \"1000 mila\"; the writer uses the first form")
ETA = (N7 + ": \"Mila zenbakitik gora eta kenduko da ondoren datozen ehunekoetan ere agertzen bada: mila eta berrehun, "
       "baina mila berrehun eta bi\"; " + N203 + ": \"1 200 000 milioi bat eta berrehun mila\", \"1 647 413 milioi bat "
       "seiehun eta berrogeita zazpi mila laurehun eta hamahiru\", \"60 200 001 hirurogei milioi berrehun mila eta bat\". "
       "\"eta\" stands before the rest when the rest has no \"eta\" of its own: one group below 100 or a round hundred")
SCALE = (N203 + ": \"1 000 000 milioi bat\", \"2 700 000 bi milioi eta zazpiehun mila\", \"1 000 000 000 mila milioi / miliar "
         "bat\", \"1012 bilioi bat\", \"1018 trilioi bat\"; \"Euskaraz, eskala luzea erabiltzen da\"; the writer uses the first form")
MINUS = N203 + ": \"Zeinu negatiboa minus irakurtzen da. Zenbaki negatiboak honela irakurtzen dira: −15: minus hamabost\""
ORDINAL = (N203 + ": \"ordinalak eratzeko, -garren atzizkia atxikitzen zaio zenbatzaile kardinalari\"; the table \"0. "
           "zerogarren 1. lehen/lehenengo\", \"5. bosgarren\", \"21. hogeita batgarren\", \"101. ehun eta batgarren\", \"1001. mila "
           "eta batgarren\", \"1 000 000. milioigarren\"; " + N18 + ": \"hogeita batgarren, hirurogeita batgarren. Hala ere, "
           "bosgarren, hogeita bosgarren\"")
SILVER_ORD = ("SILVER: a count of milioi and a rest after a scale word follow the cardinal (\"bi milioigarren\", \"milioi bat eta "
              "batgarren\"); no saved example")
FRACTION = (N203 + ": \"1/3 heren23 heren bat\", \"1/21 hogeita baten hogeita baten bat\", \"1/1 000 000 milioiren milioiren "
            "bat\"; \"2/3: bi heren\", \"7/60: zazpi hirurogeiren 2/100: bi ehunen\"; \"Izendatzailea hitz bat baino gehiagokoa "
            "denean, … zenbakitzailea esaten da lehenik, kardinal modura; ondoren, zati hitza gehitzen da\" (\"13/47 hamahiru "
            "zati berrogeita zazpi\"); \"3/2 = hiru erdi\"")
SILVER_FRACTION = "SILVER: a part of more than one word other than \"hogeita baten\" takes the ending on its last word"
DECIMAL = N203 + ": \"0,27: zero koma hogeita zazpi edo zero koma bi zazpi\"; the writer uses the first form"

UNITS = ("zero bat bi hiru lau bost sei zazpi zortzi bederatzi hamar hamaika hamabi hamahiru hamalau hamabost hamasei "
         "hamazazpi hemezortzi hemeretzi").split()
TWENTIES = {20: "hogei", 40: "berrogei", 60: "hirurogei", 80: "laurogei"}
HUNDREDS = "_ ehun berrehun hirurehun laurehun bostehun seiehun zazpiehun zortziehun bederatziehun".split()
# 10^exponent, word: the scale_noun entries of eu.json (long scale); 10^9 is "mila milioi".
SCALES = [(6, "milioi"), (12, "bilioi"), (18, "trilioi")]
MAXIMUM = "9" * 24


def R(value, text, source=None, radix=None):
    rule = {"value": str(value), "text": text + ";"}
    if radix:
        rule["radix"] = radix
    if source:
        rule["source"] = source
    return rule


# A rest with no "eta" of its own: one non-zero group of three digits that is below 100 or a round hundred.
SIMPLE = sorted({s * 1000 ** j for j in range(8) for s in [*range(1, 100), *range(100, 1000, 100)]})


def rest(name, before, after):
    """The words after a hundred or a scale word: ``before`` and the call for a rest with no "eta", ``after`` else."""
    rules = []
    for v in SIMPLE:
        rules.append(R(v, before))
        if v + 1 not in SIMPLE:
            rules.append(R(v + 1, after))
    return name, rules


def cardinal():
    rules = [R("-x", "minus →→", MINUS)] + [R(i, w) for i, w in enumerate(UNITS)]
    rules[1]["source"] = TABLE
    rules += [r for t, w in TWENTIES.items() for r in (R(t, w), R(t + 1, f"{w}ta →→", radix=20))]
    rules += [R(h * 100, f"{w}[ →%and→]", ETA if h == 1 else None) for h, w in enumerate(HUNDREDS) if h]
    rules += [R(1000, "mila[ →%and→]"), R(2000, "←← mila[ →%and→]")]
    for exponent, word in SCALES:
        rules += [R(10 ** exponent, f"{word} bat[ →%and→]", SCALE if exponent == 6 else None),
                  R(2 * 10 ** exponent, f"←← {word}[ →%and→]")]
    return "cardinal", rules


def ordinal(name, one):
    """``one`` is "lehen" alone or "batgarren" at the end of a compound ("hogeita batgarren")."""
    stem = {1: one, 5: "bosgarren", 15: "hamabosgarren"}
    rules = [R(i, stem.get(i) or w + "garren") for i, w in enumerate(UNITS)]
    rules += [r for t, w in TWENTIES.items() for r in (R(t, w + "garren"), R(t + 1, f"{w}ta →%ordinal-compound→", radix=20))]
    rules += [R(h * 100, f"{w}→%{name}-and→") for h, w in enumerate(HUNDREDS) if h]
    rules += [R(1000, f"mila→%{name}-and→"), R(2000, f"←%cardinal← mila→%{name}-and→")]
    for exponent, word in SCALES:
        rules += [R(10 ** exponent, f"{word}→%{name}-one→"), R(2 * 10 ** exponent, f"←%cardinal← {word}→%{name}-and→")]
    last = "ordinal-compound"
    sets = [(name, rules)]
    for suffix, lead in (("and", " "), ("one", " bat ")):
        tail = rest(f"{name}-{suffix}", f"{lead}eta =%{last}=", f"{lead}=%{last}=")
        sets.append((tail[0], [R(0, "garren")] + tail[1]))
    return sets


def denominator():
    """The word of a part: the cardinal with -(r)en on its last word ("bosten", "hogeiren", "hogeita baten")."""
    end = {1: "baten", 5: "bosten", 10: "hamarren", 15: "hamabosten"}
    rules = [R(i, end.get(i) or w + "ren") for i, w in enumerate(UNITS) if i]
    rules += [r for t, w in TWENTIES.items() for r in (R(t, w + "ren"), R(t + 1, f"{w}ta →%denominator→", radix=20))]
    rules += [R(h * 100, f"{w}→%denominator-and→") for h, w in enumerate(HUNDREDS) if h]
    rules += [R(1000, "mila→%denominator-and-a→"), R(2000, "←%cardinal← mila→%denominator-and-a→")]
    for exponent, word in SCALES:
        rules += [R(10 ** exponent, f"{word}→%denominator-and-a→"),
                  R(2 * 10 ** exponent, f"←%cardinal← {word}→%denominator-and-a→")]
    sets = [("denominator", rules)]
    for suffix, zero in (("and", "en"), ("and-a", "ren")):
        tail = rest(f"denominator-{suffix}", " eta =%denominator=", " =%denominator=")
        sets.append((tail[0], [R(0, zero)] + tail[1]))
    return sets


sets = [cardinal(), rest("and", "eta =%cardinal=", "=%cardinal="), *ordinal("ordinal", "lehen"),
        *ordinal("ordinal-compound", "batgarren"), *denominator()]
SOURCES = {
    "cardinal": TABLE + ". " + ETA + ". " + SCALE,
    "and": ETA,
    "ordinal": ORDINAL + ". " + SILVER_ORD,
    "ordinal-compound": ORDINAL + ": \"batgarren\" at the end of a compound",
    "denominator": FRACTION + ". " + SILVER_FRACTION,
}
rulesets = {name: {"source": SOURCES.get(name) or "a part of " + name.split("-")[0], "rules": rules}
            for name, rules in sets}
block = {
    "source": N7 + "; " + N203 + ". Basque counts in the long scale of this lexicon. " + SCALE + ".",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal", "reason": "standard"}], "maximum": MAXIMUM},
        "ordinal": {"variants": [{"ruleset": "ordinal", "reason": "standard"}], "minimum": "0", "maximum": MAXIMUM},
    },
    "decimal": {"word": "koma", "places": 3, "read": "number", "source": DECIMAL + "."},
    "scientific": {"times": "bider hamar ber", "source": N203 + ": \"1018 trilioi bat / milioi bat bilioi / hamar ber "
                                                       "hemezortzi\"; \"bider\" for times is SILVER."},
    "fraction": {"mixed": False, "limit": 10, "single": "{denominator} bat", "plural": "",
                 "named": {"2": "erdi", "3": "heren", "4": "laurden"}, "denominator": "{numerator} zati {cardinal}",
                 "ruleset": "denominator", "numerator": "cardinal", "source": FRACTION + ". " + SILVER_FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
