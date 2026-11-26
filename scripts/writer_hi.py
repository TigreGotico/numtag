"""Write the writer block of hi from CLDR RBNF hi and the scale words of the lexicon.

usage: python scripts/writer_hi.py [--check]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/hi.json"
CLDR = "CLDR RBNF hi (common/rbnf/hi.xml as shipped in unicode-rbnf 2.5.1)"
SCALE = (CLDR + ", %spellout-cardinal: \"100: ←← सौ[ →→];\", \"1000: ←← हज़ार[ →→];\", \"100000: ←← लाख[ →→];\", "
         "\"10000000: ←← करोड़[ →→];\", \"1000000000: ←← अरब[ →→];\", \"100000000000: ←← खरब[ →→];\"")
ORDINAL = (CLDR + ", %spellout-ordinal-masculine: \"1: पहला;\", \"2: दूसरा;\", \"3: तीसरा;\", \"4: चौथा;\", \"5: पाँचवाँ;\", "
           "\"6: छठा;\", \"7: =%spellout-cardinal=वाँ;\"")
ORDINAL_F = (CLDR + ", %spellout-ordinal-feminine: \"1: पहली;\", \"2: दूसरी;\", \"3: तीसरी;\", \"4: चौथी;\", \"5: पाँचवी;\", "
             "\"6: छठी;\", \"7: =%spellout-cardinal=वी;\"")
KHN = ("Kendriya Hindi Nideshalaya, Devanagari Lipi tatha Hindi Vartani ka Manakikaran (2016) (Papers/Languages/Indo-Aryan/"
       "Hindi/khn-devanagari-vartani-manakikaran-2016.pdf)")
KHN_WORDS = (KHN + ", §5.1 p. 52: \"एक से सौ तक सभी संख्यावाचक शब्दों पर विचार करने के बाद इनका जो मानक रूप स्वीकृत हुआ\": "
             "the list writes पंद्रह, चवालीस, तिरपन, तिरसठ, सतासी, अठासी, इक्यानवे … निन्यानवे; CLDR hi writes पन्द्रह, "
             "चौवालीस, तिरेपन, तिरेसठ, सत्तासी, अट्ठासी, इक्यानबे … निन्यानबे")
KHN_ORDINAL = (KHN + ", §5.2 p. 53: \"पहला दूसरा तीसरा चौथा पाँचवाँ छठा (छठवाँ नहीं) सातवाँ आठवाँ नवाँ दसवाँ\"")
SILVER_FEMININE = ("SILVER: the feminine ordinal ends in -वीं, with the nasal of the masculine -वाँ (" + KHN + ", §3.6.2.3 p. 26); "
                   "CLDR hi writes -वी")
KHN_SCALE = KHN + ", p. 53: \"हज़ार, लाख, करोड़, अरब (सौ करोड़ नहीं), साठ अरब (छह हज़ार करोड़ नहीं) पाँच खरब\""
SILVER_FRACTION = ("SILVER: a fraction reads the numerator, \"बटा\" and the denominator, each a cardinal (\"एक बटा तीन\"); "
                   "no saved source. The named words of " + KHN + ", §5.3 p. 53 (\"एक चौथाई\", \"आधा\", \"पौन\", \"सवा\", "
                   "\"डेढ़\", \"ढाई\", \"साढ़े तीन\") need a fraction form that the writer has no rule for (#364)")

# 0 to 99: the standard list of KHN, which wins over CLDR where the two differ.
WORDS = ("शून्य एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस बीस "
         "इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस "
         "छत्तीस सैंतीस अड़तीस उनतालीस चालीस इकतालीस बयालीस तैंतालीस चवालीस पैंतालीस छियालीस सैंतालीस "
         "अड़तालीस उनचास पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ साठ इकसठ बासठ तिरसठ "
         "चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर "
         "अठहत्तर उनासी अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सतासी अठासी नवासी नब्बे इक्यानवे बानवे "
         "तिरानवे चौरानवे पचानवे छियानवे सतानवे अठानवे निन्यानवे").split()
# 10^exponent, word: the Indian scale of CLDR hi.
SCALES = [(2, "सौ"), (3, "हज़ार"), (5, "लाख"), (7, "करोड़"), (9, "अरब"), (11, "खरब")]
FIRST = {"masculine": "पहला दूसरा तीसरा चौथा पाँचवाँ छठा".split(), "feminine": "पहली दूसरी तीसरी चौथी पाँचवीं छठी".split()}
END = {"masculine": "वाँ", "feminine": "वीं"}


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


cardinal = [R("-x", "ऋण →→"), *(R(i, w) for i, w in enumerate(WORDS))]
cardinal += [R(10 ** e, f"←← {w}[ →→]", SCALE if e == 2 else None) for e, w in SCALES]


def ordinal(gender):
    rules = [R("-x", "ऋण →→"), R(0, "शून्य" + END[gender])]
    rules += [R(i + 1, w) for i, w in enumerate(FIRST[gender])]
    return rules + [R(7, f"=%cardinal={END[gender]}"), R(9, "न" + END[gender], KHN_ORDINAL if gender == "masculine" else None),
                    R(10, f"=%cardinal={END[gender]}")]


sets = [("cardinal", cardinal), ("ordinal-m", ordinal("masculine")), ("ordinal-f", ordinal("feminine")),
        ("over", [R(0, "बटा =%cardinal=")])]
SOURCES = {"cardinal": CLDR + ", %spellout-cardinal. " + SCALE + ". " + KHN_WORDS + ". " + KHN_SCALE,
           "ordinal-m": ORDINAL + ". " + KHN_ORDINAL, "ordinal-f": ORDINAL_F + ". " + SILVER_FEMININE,
           "over": SILVER_FRACTION}
rulesets = {name: {"source": SOURCES[name], "rules": rules} for name, rules in sets}
maximum = "9" * 16  # the reader takes a count of खरब below one लाख (#361)
block = {
    "source": CLDR + ". Hindi counts in the Indian scale: लाख for 10^5, करोड़ for 10^7. " + SCALE + ".",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal", "reason": "standard"}], "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal-m", "reason": "standard"}],
                    "gender": {"masculine": [{"ruleset": "ordinal-m", "reason": "standard"}],
                               "feminine": [{"ruleset": "ordinal-f", "reason": "standard"}]},
                    "minimum": "0", "maximum": maximum},
    },
    "decimal": {"word": "दशमलव", "places": 3, "source": CLDR + ", %spellout-cardinal x.x: \"←← दशमलव →→\"."},
    "fraction": {"mixed": False, "limit": 10, "single": "एक {denominator}", "plural": "", "named": {},
                 "denominator": "बटा {cardinal}", "ruleset": "over", "numerator": "cardinal",
                 "source": SILVER_FRACTION + "."},
}
splice(LEXICON, block, check="--check" in sys.argv)
