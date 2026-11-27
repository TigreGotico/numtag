"""Write the writer block of mwr from Bahal 1964 and Swami, with the cardinals of the lexicon.

usage: python scripts/writer_mwr.py [--check]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/mwr.json"
B = ("Bahal, Kalicharan (1964), Ādhunik Rājasthānī kā Saṃracanātmak Vyākaraṇ "
     "(Papers/Languages/Indo-Aryan/Marwari/bahal1964_adhunik_rajasthani_vyakaran.pdf), read from the page scan")
SW = ("Swami, Narottamdas, Rājasthānī Vyākaraṇ (Papers/Languages/Indo-Aryan/Marwari/swami_narottamdas_rajasthani_"
      "vyakaran_djvu.txt), §100: \"अंक, दो, वीस, सो, हजार, पैलो, दूजो, दसवो, हजारबो\"")
CARDINAL = B + ", §5.2.1, book pp. 55-57: the cardinals 1 to 100, the first form of each row"
GROUPS = (B + ", §5.2.2, book p. 60: \"पूणौ दो सौ\", \"साढौ तीन सौ\": a count before सौ, with no joiner; book p. 57: "
          "\"सौ से ऊपर के गणनामूलक संख्यावाचक भारतीय आर्य भाषाओं की तद्विषयक रचनाओं के अनुरूप निर्मित होते हैं\". "
          "SILVER: \"एक सौ\" for 100, where Bahal's table prints a lone \"सौ\" and Swami a lone \"सो\"; a lone हजार, लाख and किरोड़ with no count, as Swami's \"हजार\"; the order of the groups past "
          "a thousand and the words लाख and किरोड़ (the stems of Bahal's collectives लाखां and किरोड़ां, §5.2.5)")
ORDINAL = (B + ", §5.2.3, book p. 61: \"पैलौ दूजौ~बीजौ तीजौ चौथौ पांचमौ छठौ\"; \"छ से ऊपर के क्रमसूचकों की रचना "
           "गणनामूलकों के साथ -मौ प्रत्यय के योग से होती है\": \"नव नमौ\", \"इगियारै इगियारमौ\". " + SW + ". SILVER: the "
           "forms past 13 and past 100, which only the last word makes an ordinal")


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


units = {}
for e in json.loads(LEXICON.read_text())["entries"]:
    if e["role"] == "unit" and e["value"] not in units:
        units[e["value"]] = e["word"]
ordinals = {}
for e in json.loads(LEXICON.read_text())["entries"]:
    if e["role"] == "ordinal" and e["value"] not in ordinals:
        ordinals[e["value"]] = e["word"]

SCALES = [(3, "हजार"), (5, "लाख"), (7, "किरोड़")]
cardinal = [R("-x", "ऋण →→")] + [R(n, units[str(n)]) for n in range(100)]
cardinal[2]["source"] = CARDINAL
cardinal += [R(100, "एक सौ[ →→]", GROUPS), R(200, "←← सौ[ →→]")]
for exponent, word in SCALES:
    cardinal += [R(10 ** exponent, f"एक {word}[ →→]"), R(2 * 10 ** exponent, f"←← {word}[ →→]")]

ordinal = [R("-x", "ऋण →→")] + [R(n, ordinals[str(n)]) for n in range(1, 100)]
ordinal += [R(100, "[एक ]सौ→%ordinal-tail→"), R(200, "←%cardinal← सौ→%ordinal-tail→"),
            R(1000, "हजार→%ordinal-group→"), R(2000, "←%cardinal← हजार→%ordinal-group→")]
for exponent, word in SCALES[1:]:
    ordinal += [R(10 ** exponent, f"{word}→%ordinal-tail→"), R(2 * 10 ** exponent, f"←%cardinal← {word}→%ordinal-tail→")]
ordinal[1]["source"] = ORDINAL

rulesets = {
    "cardinal": {"source": CARDINAL + ". " + GROUPS, "rules": cardinal},
    "ordinal": {"source": ORDINAL, "rules": ordinal},
    "ordinal-tail": {"source": "a part of ordinal", "rules": [R(0, "मौ"), R(1, " =%ordinal=")]},
    "ordinal-group": {"source": "a part of ordinal: " + SW + " (\"हजारबो\")", "rules": [R(0, "बो"), R(1, " =%ordinal=")]},
}
block = {
    "source": CARDINAL + ". Marwari counts in the Indian scale: सौ, हजार, लाख, किरोड़.",
    "rulesets": rulesets,
    "forms": {
        "cardinal": {"variants": [{"ruleset": "cardinal", "reason": "standard"}]},
        "ordinal": {"variants": [{"ruleset": "ordinal", "reason": "standard"}], "minimum": "1"},
    },
    "decimal": {"word": "दशमलव", "places": 3, "source": "SILVER: the Hindi word (hi.json); no Marwari source."},
}
splice(LEXICON, block, check="--check" in sys.argv)
