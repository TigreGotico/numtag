"""Write the writer block of bn from the Wiktionary appendix of Bengali numerals, Thompson (2012) and CLDR RBNF bn.

usage: python scripts/writer_bn.py [--check]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/bn.json"
WIKT = ("en.wiktionary, \"Appendix:Bengali numerals\" (oldid 95460450; Papers/Languages/Indo-Aryan/Bengali/"
        "wikt_en_appendix_bengali_numerals.html)")
THOMPSON = ("Thompson, Bengali (LOALL 18, 2012), Appendix II \"Numbers\", pp. 372-374 (Papers/Languages/Indo-Aryan/"
            "Bengali/thompson2012_bengali_loall18_ia_djvu.txt, OCR)")
WORDS_SOURCE = WIKT + ": the Cardinal column, rows 0 to 99, one word each (\"একুশ (ekuś)\" for 21); " + THOMPSON + ": \"21 ekuS\""
SILVER_HUNDRED = ("SILVER: a count of hundreds reads the unit, a space and \"শ\" (\"দুই শ\"). " + WIKT + ", row 100: "
                  "\"একশ (ekoś), শ (śo)\" writes the one word \"একশ\"; " + THOMPSON + ": \"100 zk so\", \"200 du $6\" "
                  "writes two words in roman script and \"du\" for 2. No saved source writes 200 in Bengali script")
SCALE = (THOMPSON + ": \"1000 eek hajar, 100.000 zek lakh\". " + WIKT + ": \"১,০০,০০০\" \"লাখ (lakh)\"; "
         "\"১,০০,০০,০০০\" \"কোটি (kōṭi)\"; \"১,০০,০০,০০,০০০\" \"একশ কোটি (ekoś kōṭi)\"; "
         "\"১০,০০,০০,০০,০০০\" \"হাজার কোটি (hajar kōṭi)\": a count above 99 goes before কোটি")
CLDR = ("CLDR common/rbnf/bn.xml, commit 951424004be6 (Papers/Languages/Indo-Aryan/Bengali/"
        "cldr_rbnf_bn_951424004be6.xml)")
ORDINAL = (WIKT + ": the Ordinal column, rows 1 to 10, \"প্রথম (prothom)\" to \"দশম (dośom)\"; " + THOMPSON
           + ": \"prothom first dvitiyd second trtlyo third céturthd fourth pohcdm fifth sosthd sixth soptom seventh "
             "astom eighth noabom ninth dos6m tenth\". Past 10: " + CLDR + ", %spellout-ordinal: \"10: দশম;\", "
             "\"11: =%spellout-cardinal=তম;\"; " + WIKT + ", row 31, Ordinal: \"একত্রিশতম (ekotriśotom)\", row 58: "
             "\"আটান্নতম (aṭannotom)\", row 100,000: \"লাখতম (lakhtom)\"")
ORDINAL_COUNT = (CLDR + ", %spellout-cardinal: \"100: <<শো[ >>];\": the cardinal before তম writes the hundred as one "
                 "word (\"একশো\"), as the ordinal rule of CLDR does")
MINUS = CLDR + ", %spellout-cardinal: \"-x: ঋণ >>;\""
DECIMAL = (CLDR + ", %spellout-cardinal: \"x.x: << দশমিক >>;\". SILVER: each digit after দশমিক reads as one "
           "cardinal (\"দশমিক নয় সাত\" for .97); no saved Bengali source spells the digits after the mark.")

lexicon = json.loads(LEXICON.read_text(encoding="utf-8"))
UNITS = {e["value"]: e["word"] for e in lexicon["entries"] if e["role"] == "unit" and int(e["value"]) < 100}
WORDS = [UNITS[str(i)] for i in range(100)]
ORDINALS = {}
for e in lexicon["entries"]:
    if e["role"] == "ordinal":
        ORDINALS.setdefault(e["value"], e["word"])
FIRST = "প্রথম দ্বিতীয় তৃতীয় চতুর্থ পঞ্চম ষষ্ঠ সপ্তম অষ্টম নবম দশম".split()
assert [ORDINALS[str(i)] for i in range(2, 11)] == FIRST[1:]
# 10^exponent, word: the Indian scale.
SCALES = [(3, "হাজার"), (5, "লাখ"), (7, "কোটি")]


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


cardinal = [R("-x", "ঋণ →→", MINUS), *(R(i, w) for i, w in enumerate(WORDS))]
cardinal += [R(100, "←← শ[ →→]", SILVER_HUNDRED)]
cardinal += [R(10 ** e, f"←← {w}[ →→]") for e, w in SCALES]
ordinal_count = [R(i, w) for i, w in enumerate(WORDS)]
ordinal_count += [R(100, "←←শো[ →→]")]
ordinal_count += [R(10 ** e, f"←← {w}[ →→]") for e, w in SCALES]
ordinal = [R(i + 1, w) for i, w in enumerate(FIRST)] + [R(11, "=%ordinal-count=তম")]

maximum = "9" * 12  # the reader takes a count of কোটি below one লাখ
block = {
    "source": WIKT + "; " + THOMPSON + ". Bengali counts in the Indian scale: লাখ for 10^5, কোটি for 10^7.",
    "rulesets": {"cardinal": {"source": WORDS_SOURCE + ". " + SILVER_HUNDRED + ". " + SCALE, "rules": cardinal},
                 "ordinal": {"source": ORDINAL, "rules": ordinal},
                 "ordinal-count": {"source": ORDINAL_COUNT + ". " + SCALE, "rules": ordinal_count}},
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal", "reason": "standard"}], "maximum": maximum},
        "ordinal": {"variants": [{"ruleset": "ordinal", "reason": "standard"}], "minimum": "1", "maximum": maximum},
    },
    "decimal": {"word": "দশমিক", "places": 3, "source": DECIMAL},
    "fraction": None,  # Thompson gives the fraction words in roman script only (#366)
}
splice(LEXICON, block, check="--check" in sys.argv)
