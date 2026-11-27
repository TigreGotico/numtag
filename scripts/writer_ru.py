"""Write the writer block of ru from CLDR RBNF ru (cardinals), Rosental (ordinals) and the CLDR plural rules.

usage: python scripts/writer_ru.py [--check]

The cardinal rule sets are copied from scripts/cldr/ru.xml, the CLDR file common/rbnf/ru.xml as unicode-rbnf 2.5.1
ships it (Unicode License v3, LICENSE-CLDR). The ordinal rule sets are built here, because CLDR ru writes "двести"
for 200th and "три тысячи" for 3000th.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice

LEXICON = Path(__file__).parents[1] / "numtag/lexicon/ru.json"
CLDR = "CLDR RBNF ru (common/rbnf/ru.xml as shipped in unicode-rbnf 2.5.1)"
PLURAL = ("CLDR plural rules ru (Babel 2.18.0, Locale('ru').plural_form): \"one: v in 0 and i mod 10 in 1 and i mod 100 "
          "not in 11, few: v in 0 and i mod 10 in 2..4 and i mod 100 not in 12..14\"")
ROSENTAL = ("Д. Э. Розенталь, Справочник по правописанию и литературной правке (1985), § 45 "
            "(Papers/Languages/Slavic/rozental1985_spravochnik_pravopisanie_literaturnaya_pravka_ocr.pdf)")
ORDINAL = (ROSENTAL + ", п. 4: \"П о р я д к о в ы е числительные пишутся так же, к� к и соответ­ ствующие сложные и "
           "составные количественные числительные\"; п. 5: \"двадцатипятитысячный, стосорокашестимиллионный, "
           "тридцатиодномиллиардный\"; § 42, п. 6: \"В форме родительного падежа без соединитеJ1ьной гласной входят в "
           "состав сложных слов имена числительные … Исключения составляют числительные один, девяносто, сто и "
           "тысяча\". The words of a compound ordinal stay cardinals in the nominative and only the last word "
           "declines (\"три тысячи пятнадцатый\")")
ENDINGS = (CLDR + ", %spellout-ordinal-masculine, -feminine, -neuter and their case sets: the endings of the ordinals "
           "0 to 199 (\"второй\", \"вторую\", \"третью\", \"сотыми\"). CLDR ru breaks from 200 (\"200: "
           "←%spellout-cardinal-feminine←сти[ →→];\"), so the ordinals here use its endings on the stems of " + ROSENTAL)
YO = ("Русская грамматика (1980), § 1374 (Papers/Languages/Slavic/russkaya_grammatika_1980_rusgram_html.zip, "
      "1366-1383.html): \"Р. дв - ух тр - ёх четыр - ёх Д. дв - ум тр - ём четыр - ём\". Правила русской орфографии и "
      "пунктуации (2006), § 5 (Papers/Languages/Slavic/Russian/lopatin2006_pravila_orfografii_s5_yo_orthographia.html): "
      "\"Для предупреждения неправильного опознания слова\", \"Для указания правильного произношения слова\", and "
      "Примечание 2: \"любая книга может быть напечатана последовательно с буквой ё\". So ё is permitted and "
      "recommended, and the writer writes it for speech (\"трёх\", \"четырёх\", \"трём\"); the е spelling is the "
      "second reading. SILVER: \"четвёртый\" and its forms, by the same rule; no saved example writes it")
GR80 = ("Русская грамматика (1980), § 1378 (Papers/Languages/Slavic/russkaya_grammatika_1980_rusgram_html.zip, "
        "1366-1383.html): \"При образовании падежных форм нормально изменение по падежам каждого слова, входящего в "
        "составное числительное. И. тысяча двести восемьдесят семь Р. тысячи двухсот восьмидесяти семи … Пр. о тысяче о "
        "двухстах о восьмидесяти семи\"")
LOCATIVE = (GR80 + ". CLDR ru writes \"двадцать[ →→]\" and \"тридцать[ →→]\" in %spellout-cardinal-masculine-locative "
            "and \"двадцати\", \"тридцати\" in the -neuter-locative set; the writer takes the declined form")
BARE = (GR80 + "; Д. Э. Розенталь, Справочник по правописанию и литературной правке (1985), § 164, п. 2 "
        "(Papers/Languages/Slavic/rozental1985_spravochnik_pravopisanie_literaturnaya_pravka_ocr.pdf): \"груз массой в "
        "тысячу пятьсот тонн\", and п. 1 г): \"не одной тысячей рублей (слово тысяча с предшествующим числительным одна "
        "рассматривается как существительное и управляет родительным падежом следующего слова)\". So a scale word "
        "with the count one is bare (\"тысяча\", \"миллион\"); CLDR ru writes \"одна тысяча\", the variant here")
ORDINAL_PLURAL = (ROSENTAL + ", п. 3: \"Д р о б н ы е числительные пишутся раздельно, например: две пятых ( 2/ 5)\". "
                  "The plural of an ordinal has one form for the three genders, with the adjective endings -ые, -ых, "
                  "-ым, -ыми (\"пятых\", \"пятыми\") and -ьи, -ьих, -ьим, -ьими for \"третий\"")
DECIMAL = (CLDR + ", %spellout-cardinal-feminine: \"x.x: [←← $(cardinal,one{целая}other{целых})$ ]→%%fractions-feminine→;\" "
           "and %%fractions-feminine: \"10: ←%spellout-cardinal-feminine← "
           "$(cardinal,one{десятая}other{десятых})$;\"; Русская грамматика (1980), Гр-80 §§ 1366–1383: \"одна целая "
           "шесть десятых, три целых и двадцать пять сотых\", \"пяти десятым участка, трем пятым суток\", and § 1378: "
           "\"нормально изменение по падежам каждого слова\"; " + ROSENTAL + ", п. 3: \"три целых и шесть седьмых\". "
           "The standard decimal reads the whole part with \"целая\" or \"целых\" and the decimals as a fraction of a "
           "power of ten, every word in the case; \"запятая\" and one word for each decimal is the variant")
SILVER = ("SILVER: the decimal word \"запятая\" (CLDR ru numbers write the decimal sign \",\") and \"умножить на десять в "
          "степени\"; no saved example")

CASES = {"nominative": "", "genitive": "-genitive", "dative": "-dative", "accusative": "-accusative",
         "instrumental": "-ablative", "prepositional": "-locative"}
ALIAS = {"ablative": "instrumental", "locative": "prepositional"}  # the CLDR names of the same cases
GENDERS = {"masculine": "m", "feminine": "f", "neuter": "n"}
# The ordinal also has a plural, which has no gender: "две пятых".
ORDINAL_GENDERS = GENDERS | {"plural": "p"}
# The adjective endings of an ordinal: a hard stem ("пятый"); "ой" stems differ in the masculine nominative and
# accusative only ("второй"); "третий" takes the soft endings of its own.
HARD = {"m": dict(nominative="ый", genitive="ого", dative="ому", accusative="ый", instrumental="ым", prepositional="ом"),
        "f": dict(nominative="ая", genitive="ой", dative="ой", accusative="ую", instrumental="ой", prepositional="ой"),
        "n": dict(nominative="ое", genitive="ого", dative="ому", accusative="ое", instrumental="ым", prepositional="ом")}
PLURAL_HARD = dict(nominative="ые", genitive="ых", dative="ым", accusative="ые", instrumental="ыми", prepositional="ых")
PLURAL_SOFT = dict(nominative="ьи", genitive="ьих", dative="ьим", accusative="ьи", instrumental="ьими", prepositional="ьих")
SOFT = {"m": dict(nominative="ий", genitive="ьего", dative="ьему", accusative="ий", instrumental="ьим", prepositional="ьем"),
        "f": dict(nominative="ья", genitive="ьей", dative="ьей", accusative="ью", instrumental="ьей", prepositional="ьей"),
        "n": dict(nominative="ье", genitive="ьего", dative="ьему", accusative="ье", instrumental="ьим", prepositional="ьем")}
# The ordinal stems and their type: "ый" hard, "ой" stressed, "ий" soft.
STEMS = {0: ("нулев", "ой"), 1: ("перв", "ый"), 2: ("втор", "ой"), 3: ("трет", "ий"), 4: ("четверт", "ый"),
         5: ("пят", "ый"), 6: ("шест", "ой"), 7: ("седьм", "ой"), 8: ("восьм", "ой"), 9: ("девят", "ый"),
         10: ("десят", "ый"), 11: ("одиннадцат", "ый"), 12: ("двенадцат", "ый"), 13: ("тринадцат", "ый"),
         14: ("четырнадцат", "ый"), 15: ("пятнадцат", "ый"), 16: ("шестнадцат", "ый"), 17: ("семнадцат", "ый"),
         18: ("восемнадцат", "ый"), 19: ("девятнадцат", "ый"), 20: ("двадцат", "ый"), 30: ("тридцат", "ый"),
         40: ("сороков", "ой"), 50: ("пятидесят", "ый"), 60: ("шестидесят", "ый"), 70: ("семидесят", "ый"),
         80: ("восьмидесят", "ый"), 90: ("девяност", "ый")}
TENS = {20: "двадцать", 30: "тридцать", 40: "сорок", 50: "пятьдесят", 60: "шестьдесят", 70: "семьдесят",
        80: "восемьдесят", 90: "девяносто"}
HUNDREDS = "сто двести триста четыреста пятьсот шестьсот семьсот восемьсот девятьсот".split()
# The first part of a joined ordinal (§ 42, п. 6): the genitive, but "одно", "девяносто" and "сто".
JOIN_UNITS = ("одно двух трех четырех пяти шести семи восьми девяти десяти одиннадцати двенадцати тринадцати "
              "четырнадцати пятнадцати шестнадцати семнадцати восемнадцати девятнадцати").split()
JOIN_TENS = {20: "двадцати", 30: "тридцати", 40: "сорока", 50: "пятидесяти", 60: "шестидесяти", 70: "семидесяти",
             80: "восьмидесяти", 90: "девяносто"}
# 10^exponent, the noun forms one/few/other in the nominative, the ordinal stem.
SCALES = [(3, ("тысяча", "тысячи", "тысяч"), "тысячн"), (6, ("миллион", "миллиона", "миллионов"), "миллионн"),
          (9, ("миллиард", "миллиарда", "миллиардов"), "миллиардн"),
          (12, ("триллион", "триллиона", "триллионов"), "триллионн")]


# The short-scale words above 10^15, copied from "квадриллион", with the sense line of each in the saved
# ru.wiktionary file.
WIKT = "Papers/Languages/Slavic/Russian/ru_wiktionary_quintillion_to_duodecillion_declension.txt"
LARGE = [("квинтиллион", "тысяча квадриллионов;  тысяча в шестой степени; число, равное 1018"),
         ("секстиллион", "тысяча квинтиллионов; тысяча в седьмой степени; число, равное 1021"),
         ("септиллион", "тысяча секстиллионов; тысяча в восьмой степени; число, равное 1024"),
         ("октиллион", "тысяча септиллионов;  тысяча в девятой степени; число, равное 1027"),
         ("нониллион", "тысяча октиллионов; число, равное 1030"),
         ("дециллион", "тысяча нониллионов; число, равное 1033"),
         ("ундециллион", "тысяча дециллионов; число, равное 1036"),
         ("дуодециллион", "тысяча ундециллионов; число, равное 1039")]
LARGE_SOURCE = {word: f"ru.wiktionary, \"{word}\" ({WIKT}): \"{sense}\"; a masculine inanimate noun of Zaliznyak type 1a, "
                      "so its rules copy those of \"квадриллион\"." for word, sense in LARGE}
LARGE_EXPONENT = {word: 3 * rank + 3 for rank, (word, _) in enumerate(LARGE, 5)}


def R(value, text, source=None):
    rule = {"value": str(value), "text": text + ";"}
    if source:
        rule["source"] = source
    return rule


def bare(name, rules):
    """The rules with a bare scale word for the count one at the start of the number: "тысяча", "тысячи двухсот".
    The CLDR rule moves to the count two, and the rest of the number reads "одна тысяча" ("миллион одна тысяча")."""
    out = []
    for rule in rules:
        value, text = rule["value"], rule["text"]
        one = re.search(r"\$\(cardinal,one\{(\w+)\}", text)
        if one and re.fullmatch(r"10*", value) and len(value) > 3:
            rest = f"[ →%{name}-one→]"
            large = next((w for w in LARGE_SOURCE if one.group(1).startswith(w)), None)
            out += [R(value, one.group(1) + rest, BARE + (". " + LARGE_SOURCE[large] if large else "")),
                    R("2" + value[1:], text.removesuffix(";").replace("[ →→]", rest))]
        else:
            out.append(rule)
    return out


def cldr_sets(path):
    """The CLDR cardinal rule sets, renamed: "spellout-cardinal-feminine-genitive" becomes "cardinal-f-genitive"."""
    def rename(name):
        gender, _, case = name.removeprefix("spellout-cardinal-").partition("-")
        return f"cardinal-{GENDERS[gender]}" + (f"-{case}" if case else "")
    sets = {}
    for ruleset in ET.parse(path).iter("ruleset"):
        name = ruleset.get("type")
        if not re.fullmatch(r"spellout-cardinal-(masculine|feminine|neuter)(-\w+)?", name):
            continue
        rules = []
        for rule in ruleset.iter("rbnfrule"):
            value, text = rule.get("value"), rule.text.removesuffix(";")
            if value == "x.x" or len(value) > 18:
                continue
            text = re.sub(r"%(spellout-cardinal-[\w-]+)", lambda m: "%" + rename(m.group(1)), text)
            if name == "spellout-cardinal-masculine-locative" and value in ("20", "30"):
                rules.append(R(value, text.replace("ать[", "ати["), LOCATIVE))
                continue
            rules.append(R(value, text))
            if value == "1000000000000000":
                rules += [R(10 ** LARGE_EXPONENT[word], text.replace("квадриллион", word)) for word, _ in LARGE]
        sets[rename(name)] = rules
    return sets


def ending(stem, kind, g, case):
    if g == "p":
        return stem + (PLURAL_SOFT if kind == "ий" else PLURAL_HARD)[case]
    if kind == "ий":
        return stem + SOFT[g][case]
    if kind == "ой" and g == "m" and case in ("nominative", "accusative"):
        return stem + "ой"
    return stem + HARD[g][case]


def ordinal(g, case):
    """The ordinal rule set of a gender and a case: "сто первый", "двухсотый", "три тысячи пятнадцатый"."""
    name = f"ordinal-{g}-{case}"
    word = lambda stem, kind="ый": ending(stem, kind, g, case)
    rules = [R("-x", "минус →→")] + [R(n, word(*STEMS[n])) for n in range(20)]
    for t, cardinal in TENS.items():
        rules += [R(t, word(*STEMS[t])), R(t + 1, f"{cardinal} →%{name}→")]
    rules += [R(100, f"[сто →%{name}→|{word('сот')}]")]
    rules += [R(100 * h, f"[{HUNDREDS[h - 1]} →%{name}→|←%join←{word('сот')}]") for h in range(2, 10)]
    for exponent, (one, _, _), stem in SCALES:
        rules += [R(10 ** exponent, f"[{one} →%{name}→|{word(stem)}]"),
                  R(2 * 10 ** exponent, f"[←%count-{one}← →%{name}→|←%join←{word(stem)}]")]
    return name, rules


def count(exponent, forms):
    """A count and its scale noun in the nominative: "две тысячи", "пять миллионов"."""
    one, few, other = forms
    cardinal = "cardinal-f" if exponent == 3 else "cardinal-m"
    return f"count-{one}", [R(1, f"=%{cardinal}= $(cardinal,one{{{one}}}few{{{few}}}other{{{other}}})$")]


def yo(text):
    """The ё spelling of a rule text: "трех" and "четырех" (also inside "трехсот"), "трем", "четырем", "четверт"."""
    text = text.replace("трех", "трёх").replace("четырех", "четырёх").replace("четверт", "четвёрт")
    return re.sub(r"\b(тр|четыр)ем\b", r"\1ём", text)


def with_yo(rulesets):
    """The rule sets in the ё spelling under their names, and in the е spelling under name + "-e"."""
    names = set(rulesets)
    rename = lambda text: re.sub(r"%([\w-]+)", lambda m: "%" + m.group(1) + ("-e" if m.group(1) in names else ""), text)
    out = {}
    for name, spec in rulesets.items():
        out[name] = {"source": spec["source"] + ". " + YO,
                     "rules": [{**rule, "text": yo(rule["text"])} for rule in spec["rules"]]}
        out[name + "-e"] = {"source": spec["source"] + ": the е spelling",
                            "rules": [{**rule, "text": rename(rule["text"])} for rule in spec["rules"]]}
    return out


# "целый" after the count one and after any other: "одна целая", "две целых", "двумя целыми".
WHOLE = {"nominative": ("целая", "целых"), "genitive": ("целой", "целых"), "dative": ("целой", "целым"),
         "accusative": ("целую", "целых"), "instrumental": ("целой", "целыми"), "prepositional": ("целой", "целых")}


def decimal_cases():
    """The rule sets and the whole word of a decimal in each case. After a count other than one, the nominative
    and the accusative take the genitive plural ("две пятых"); the other cases agree ("двумя пятыми")."""
    table = {}
    for case, (one, other) in WHOLE.items():
        plural = "genitive" if case in ("nominative", "accusative") else case
        table[case] = {"numerator": "cardinal-f" + CASES[case], "one": f"ordinal-f-{case}",
                       "other": f"ordinal-p-{plural}", "whole": {"one": one, "other": other}}
    return table | {alias: table[case] for alias, case in ALIAS.items()}


def main():
    path, check = Path(__file__).parent / "cldr/ru.xml", "--check" in sys.argv
    sets = cldr_sets(path)
    join = [R(i, w) for i, w in enumerate(JOIN_UNITS, 1)]
    join += [R(t, f"{w}[→→]") for t, w in JOIN_TENS.items()] + [R(100, "сто[→→]"), R(200, "←←сот[→→]")]
    rulesets = {name: {"source": CLDR + f", %spellout-{name.replace('cardinal-m', 'cardinal-masculine').replace('cardinal-f', 'cardinal-feminine').replace('cardinal-n', 'cardinal-neuter')}, with the CLDR plural forms of the scale nouns",
                       "rules": rules} for name, rules in sets.items()}
    rulesets["join"] = {"source": ORDINAL, "rules": join}
    for exponent, forms, _ in SCALES:
        name, rules = count(exponent, forms)
        rulesets[name] = {"source": CLDR + ", %spellout-cardinal-feminine 1000 and -masculine 1000000. " + PLURAL,
                          "rules": rules}
    for name, rules in sets.items():
        rulesets[name + "-one"] = {"source": rulesets[name]["source"] + ": the scale word with the count one, "
                                             "\"одна тысяча\"", "rules": rules}
        rulesets[name] = {"source": rulesets[name]["source"] + ". " + BARE, "rules": bare(name, rules)}
    for g in ORDINAL_GENDERS.values():
        for case in CASES:
            name, rules = ordinal(g, case)
            rulesets[name] = {"source": ORDINAL + ". " + (ORDINAL_PLURAL if g == "p" else ENDINGS), "rules": rules}

    rulesets = with_yo(rulesets)

    def pair(name):
        spellings = [{"ruleset": name, "reason": "standard"}, {"ruleset": name + "-e", "reason": "variant_spelling"}]
        one = name + "-one"
        return spellings + ([{"ruleset": one, "reason": "variant_spelling"}] if one in rulesets else [])

    def by_case(kind):
        genders = GENDERS if kind == "cardinal" else ORDINAL_GENDERS
        table = {case: {gender: pair(f"{kind}-{g}" + (CASES[case] if kind == "cardinal" else f"-{case}"))
                        for gender, g in genders.items()} for case in CASES}
        return table | {alias: table[case] for alias, case in ALIAS.items()}

    def by_gender(kind):
        genders = GENDERS if kind == "cardinal" else ORDINAL_GENDERS
        return {gender: pair(f"{kind}-{g}" + ("" if kind == "cardinal" else "-nominative")) for gender, g in genders.items()}

    block = {
        "source": CLDR + ". Russian counts in the short scale of this lexicon: \"миллиард\" for 10^9, \"триллион\" for "
                  "10^12. " + ORDINAL + ".",
        "plural": [{"category": "one", "mod10": [1], "not_mod100": [11], "source": PLURAL},
                   {"category": "few", "mod10": [2, 3, 4], "not_mod100": [12, 13, 14], "source": PLURAL}],
        "rulesets": rulesets,
        "forms": {
            "cardinal": {"variants": pair("cardinal-m"), "gender": by_gender("cardinal"),
                         "case": by_case("cardinal"), "maximum": "9" * 42},
            "ordinal": {"variants": pair("ordinal-m-nominative"),
                        "gender": by_gender("ordinal"), "case": by_case("ordinal"), "minimum": "0", "maximum": "9" * 15},
        },
        "decimal": {"word": "запятая", "places": 3, "read": "fraction", "variant_read": ["digits"],
                    "by_case": decimal_cases(), "source": DECIMAL + ". " + SILVER + "."},
        "scientific": {"times": "умножить на десять в степени", "source": SILVER + "."},
        "fraction": {"mixed": False, "limit": 10, "single": "одна {denominator}", "plural": {"ья": "ьих", "ая": "ых"},
                     "named": {}, "denominator": "{cardinal}", "ruleset": "ordinal-f-nominative",
                     "numerator": "cardinal-f",
                     "source": ROSENTAL + ", п. 3: \"Д р о б н ы е числительные пишутся раздельно, например: две "
                               "пятых ( 2/ 5)\": the numerator in the feminine, the denominator an ordinal, in the "
                               "nominative singular after one (" + PLURAL + ") and in the genitive plural after any "
                               "other count."},
    }
    splice(LEXICON, block, check=check)


main()
