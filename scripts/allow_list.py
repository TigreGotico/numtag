"""Rebuild the allow-list entries of one language from the writer golden file: each row where the
writer differs from ovos-number-parser gets the output of numtag and the source of its category.

usage: python scripts/allow_list.py LANG [--check]
A row with no category stops the script, so every entry has a source.
"""
import sys, json, collections, os, re
from pathlib import Path
os.chdir(Path(__file__).parents[1])
sys.path.insert(0, "tests"); import golden_writers as gw
from numtag import spell, SpokenForm
lang = sys.argv[1]
CIB = "https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/"
SRC = {
 "quadringentesimo": "Priberam, \"quadringentésimo\": \"Que ou o que ocupa o último lugar numa série de quatrocentos\"; \"quadrigentésimo\" has no definition in Priberam.",
 "whole_float": "numtag docs/values.md: a value is a canonical digit string, and the float 2.0 of the row is the digit string \"2\", with no decimals to read.",
 "scientific": "ovos-number-parser 0.30.1a1 numbers_pt.py, pronounce_number_pt: the function has no scientific parameter, so the row reads the plain number." if lang.startswith("pt") else f"ovos-number-parser 0.31.5a2 numbers_{lang}.py: the writer has no scientific parameter, so the row reads the plain number.",
 "zero_denominator": "numtag docs/values.md: \"A fraction with a zero denominator has no value\"; spell raises ZeroDivisionError.",
 "negative": "Ciberdúvidas 11493 (" + CIB + "numeros-fraccionarios/11493): «um meio», «um terço»; Ciberdúvidas 4181 (" + CIB + "um-doze-avos/4181): «Avo, no singular, só em um avo e meio avo». A numerator of one takes the singular, and the minus word leads, as for a negative cardinal.",
 "avos": "Ciberdúvidas 35323 (" + CIB + "denominadores-multiplos-de-1000-10-000-100-000-1000-000/35323), after Celso Cunha: «Quando o ordinal é expresso por mais que uma palavra, usa-se … o cardinal seguido do termo avos … 10 000 → dez mil avos»; Ciberdúvidas 4181: «escreve-se um doze avos, dois treze avos, sempre com avos no plural».",
 "ordinal_denominator": "Ciberdúvidas 35323, after Celso Cunha: «pode ser usada a mesma designação para o fracionário que para ordinal, se expresso numa só palavra … 1/1000000 → milionésimo»; Ciberdúvidas 38878 (" + CIB + "a-leitura-de-15000/38878), citing Cunha & Cintra p. 375: «pelo ordinal correspondente: quarto, quinto, centésimo»; Priberam, \"quadragésimo\", sense 2: «Um quarenta avos».",
 "big_ordinal": "numtag/lexicon/pt-PT.json, the scale_noun entries: the rank-th -illion is 10^(6 x rank) in the long scale, so \"sedecilião\" (rank 16) is 10^96 and 10^100 is \"dez mil sedecilionésimo\". No entry names 10^300, so its ordinal has no words.",
 "short_ordinal": "numtag/lexicon/pt-BR.json, the scale_noun entries and the short scale of pt-BR (Priberam, \"bilião\", sense 2: \"[Brasil] Mil milhões (10^9)\"): the rank-th -illion is 10^(3 x rank + 3), so \"nonilhão\" (rank 9) is 10^30.",
 "ducentesimo": "Priberam, \"ducentésimo\": «cada uma das partes da unidade dividida em 200 partes iguais»; Ciberdúvidas 11493: «1/200 designar-se por um ducentésimo»; Priberam has no entry \"duocentésimo\".",
}
BIG_BR = 'numtag/lexicon/pt-BR.json, the scale_noun entries and the short scale of pt-BR: the -illions run with no gap to "vigintilhão" (rank 20, 10^63), so an ordinal above 10^69 - 1 has no words.'
if lang == "pt-BR":
    SRC["big_ordinal"] = BIG_BR
DPD_UNO = "RAE, Diccionario panhispánico de dudas, 2.ª ed., «uno»: before a masculine noun the numeral takes the form «un», in compounds too: «Tengo veintiún años»."
SRC.update({
 "es_neutral": "Spanish has no neuter numeral. A call with no noun gender reads the bare number: CLDR RBNF es (unicode-rbnf 2.5.1), %spellout-numbering, 1 «uno», 21 «veintiuno».",
 "es_millardo": "CLDR RBNF es (unicode-rbnf 2.5.1), %spellout-numbering: 10^9 reads «mil millones», a count of millions. The lexicon reads «millardo» too.",
 "es_apocope": DPD_UNO,
 "es_short": "numtag/lexicon/es.json, the setting scale: Spanish counts in the long scale only («billón» is a million millions), so a call for the short scale reads the long one.",
 "es_improper": "RAE, Diccionario panhispánico de dudas, 2.ª ed., «fraccionarios»: the denominator word is «una sola palabra: treceava, catorceava, cientounava» after the numerator, so 3/2 reads «tres medios».",
 "onp_error": "ovos-number-parser raises NotImplementedError for this number; numtag reads it from the scale_noun entries of the lexicon, or raises ValueError past the last of them.",
 "digits_number": f"ovos-number-parser numbers_{lang}.py reads each decimal digit whatever `digits` says; numtag.spell(decimals=\"number\") reads the decimals as one number, as the call asks.",
})
def category_es(row, got):
    kw, out, mine = row.get("kw", {}), str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if out == "NotImplementedError": return "onp_error"
    head, _, last = mine.rpartition(" ")
    if kw.get("gender") == "masculine" and last in ("un", "veintiún") and out == f"{head} {last}o".strip().replace("veintiúno", "veintiuno"): return "es_apocope"
    if kw.get("gender") == "neutral" and mine.replace("uno", "un").replace("veintiun", "veintiún") == out: return "es_neutral"
    if "millardo" in out: return "es_millardo"
    if kw.get("scale") == "short" and re.search(r"(?:b|tr|cuatr|quint|sext|sept|oct|non|dec)illon", out): return "es_short"
    if row["fn"] == "fraction":
        top, bottom = (t.lstrip("-") for t in row["arg"].split("/"))
        if bottom == "0": return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
        if int(top) >= int(bottom) and " y " in out: return "es_improper"
    return None
CLDR_IT = "CLDR RBNF it (unicode-rbnf 2.5.1), %spellout-ordinal-masculine: an ordinal is one word, the cardinal and \"-esimo\" (1001 \"milleunesimo\", 110 \"centodecimo\")."
TRECCANI_FRAZIONARI = "Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali», § 2.3 Frazionari: \"formati da un aggettivo numerale cardinale e da un ordinale (un terzo, due quinti, quattro decimi, ecc.)\": the numerator is a cardinal, \"un\" before the denominator, and the denominator agrees with it."
SRC.update({
 "it_joined": "Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali» (Papers/Languages/Romance/Italian/treccani_enciclopedia_italiano_numerali.html): \"di milione , miliardo , bilione , ecc., che hanno un regolare plurale e che, per indicare una quantità determinata, devono essere necessariamente preceduti da un altro cardinale\", with \"cinquanta milioni\" and \"quattro miliardi di persone\": the scale word is a noun and stands as a word of its own; ovos-number-parser joins it to the count (\"seicentoventottomilioni\").",
 "it_one_plural": "Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali» (Papers/Languages/Romance/Italian/treccani_enciclopedia_italiano_numerali.html): \"di milione , miliardo , bilione , ecc., che hanno un regolare plurale\": a count of one takes the singular (\"un miliardo\"); ovos-number-parser writes the plural (\"unomiliardi\", \"bilioni\").",
 "it_short": "numtag/lexicon/it.json, the setting scale: Italian counts in the long scale only (CLDR RBNF it (unicode-rbnf 2.5.1): \"1000000000000: un bilione\"), so a call for the short scale reads the long one.",
 "it_apocope": "Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali», ex. 24-25: in a compound before a noun «uno» \"può essere apocopato ... ottantun votanti ... quarantun anni\"; gender=masculine reads the form before a noun, as CLDR RBNF it (unicode-rbnf 2.5.1) %spellout-cardinal-masculine.",
 "it_ordinal": CLDR_IT,
 "it_split": "Vocabolario Treccani, «ordinale»: \"centesimo decimo, millesimo primo, millesimo secondo, millesimo decimo, millesimo undecimo o undicesimo, ecc. (in questi casi la grafia staccata è preferita)\"; the last round hundred and 10 of a larger ordinal is spaced in the same way.",
 "it_mille": "CLDR RBNF it (unicode-rbnf 2.5.1), %spellout-numbering: \"1000: mille\"; \"mila\" is the plural after a count (\"2000: ←←mila\"), so -1000 is \"meno mille\".",
 "it_count": "Accademia della Crusca, consulenza 1077: \"21.000: ventunomila o ventunmila: entrambe le forme vanno bene\", the full form first; Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali», ex. 24-25: «uno» in a compound \"può essere apocopato\", so the apocope is optional and the full form \"ventuno\" is the unmarked one.",
 "it_mezzi": "SILVER: no saved source names the plural fraction \"mezzi\". Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali», § 2.3 gives the pattern \"un terzo, due quinti, quattro decimi\" and says \"discorso a parte va fatto per mezzo\"; the writer applies the pattern to the half (\"tre mezzi\") until a source names the form.",
 "it_fraction": TRECCANI_FRAZIONARI,
 "it_big": "numtag/lexicon/it.json, the scale_noun entries: milione 10^6, miliardo 10^9, bilione 10^12, biliardo 10^15, trilione 10^18, quadrilione 10^24 (CLDR RBNF it (unicode-rbnf 2.5.1) names up to biliardo). The lexicon has no \"triliardo\" or \"quintilione\", so 10^21 reads \"mille trilioni\" and 10^30 reads the exponent form.",
})
def category_it(row, got):
    kw, out, mine = row.get("kw", {}), str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if out == "NotImplementedError": return "onp_error"
    if re.search(r"triliard|quadriliard|quintilion", out): return "it_big"
    if out == "meno mila" and mine == "meno mille": return "it_mille"
    if row["fn"] == "fraction":
        top, bottom = (t.lstrip("-") for t in row["arg"].split("/"))
        if bottom == "0": return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
        return "it_mezzi" if bottom == "2" and top not in ("0", "1") else "it_fraction"
    if kw.get("scale") == "short" and out != mine:  # the long-scale reason of the row, else spacing, else the scale
        long = category_it({**row, "kw": {k: v for k, v in kw.items() if k != "scale"}}, got)
        if long: return long
        flat = lambda t: t.replace(" ", "").replace("uno", "un").replace("tré", "tre")
        if flat(out) == flat(mine): return "it_joined"
        one = lambda t: re.sub(r"(milion|miliard|bilion|biliard|trilion)[ieo]", r"\1", flat(t)).replace("unun", "un")
        return "it_one_plural" if one(out) == one(mine) or one("un" + out) == one(mine) else "it_short"
    if out != mine and out.replace(" ", "") == mine.replace(" ", "") and re.search(r"(milion|miliard|bilion|biliard|trilion)[ei]", mine): return "it_joined"
    if kw.get("gender") == "masculine" and re.sub(r"un\b", "uno", mine) == out: return "it_apocope"
    if row["fn"] == "ordinal" and " " not in mine.removeprefix("meno ") and " " in out.removeprefix("meno "): return "it_ordinal"
    if row["fn"] == "ordinal" and re.search(r"centesim[oa] decim[oa]$", mine) and mine.replace("esimo decimo", "odecimo").replace("esima decima", "odecima") == out: return "it_split"
    if mine.replace("uno", "un") == out.replace("uno", "un"): return "it_count"
    return None
FR_ACADEMIE = "Académie française, «Questions de langue: nombres»: the traditional spelling links with a space the \"et\" of 21, 31 ... 71 (\"vingt et un\"), and \"il est également possible, en accord avec les Rectifications de l'orthographe ... de lier par un trait d'union tous les éléments\". The writer prints the traditional spelling; ovos-number-parser joins only \"-et-\", which neither spelling does."
SRC.update({
 "fr_et": FR_ACADEMIE,
 "fr_fraction": "OQLF, Banque de dépannage linguistique 23494, «Pluriel des fractions»: the denominator is a noun that \"prend la marque du pluriel comme tout autre nom\" (\"deux cinquièmes\"), so \"trois demis\" and \"cinq onzièmes\"; ovos-number-parser reads an improper fraction as a mixed number. SILVER: the plural after \"zéro\".",
 "fr_big": "numtag/lexicon/fr-FR.json, the scale_noun entries: million 10^6, milliard 10^9, billion 10^12, billiard 10^15, trillion 10^18 (long scale), so 10^15 reads \"un billiard\" and the exponent form starts at 10^24.",
 "fr_zero": "CLDR RBNF fr, %spellout-ordinal-masculine: \"0: zéroième\"; the call asks for the ordinal, and ovos-number-parser reads the cardinal.",
 "fr_scale_count": "Académie française, «vingt et cent»: \"Ils restent également invariables lorsqu’ils sont employés comme adjectifs numéraux ordinaux\": \"quatre-vingt millionième\"; ovos-number-parser writes the plural s before the ordinal of a scale.",
 "fr_scale_one": "CLDR RBNF fr, %spellout-ordinal-masculine reads the ordinal of 10^6 as \"millionième\" with no \"un\"; numtag reads every scale ordinal so, \"billiardième\".",
 "fr_et_unieme": "Dictionnaire de l’Académie française, 9e éd., «unième»: \"Ne s’emploie qu’avec les nombres vingt, trente, quarante, cinquante, soixante, quatre-vingts, cent et mille, souvent précédé de et\", example \"la mille et unième nuit\"; ovos-number-parser writes \"cent unième\".",
 "fr_short": "numtag/lexicon/fr-FR.json, the setting scale: French counts in the long scale only, so a call for the short scale reads the long one.",
})
RO_DOOM = "DOOM 3 (2021), as quoted by dexonline (Papers/Languages/Romance/Romanian/)"
SRC.update({
 "ro_ordinal": RO_DOOM + ": \"sutălea (al o ~) ... f. a suta/a o suta\", \"mielea (al ~/al o ~) ... f. a mia/a o mia\", \"miilea (al + num. + ~)\", \"milioanelea (al + num. + ~) (referitor la milioane)\" (dexonline_milioanelea.html), \"milionulea (al ~/al un ~) (referitor la un milion)\" (dexonline_milionulea.html); ovos-number-parser writes \"al sutălea primul\" for 101 and \"al doi miliardulea\".",
 "ro_article": RO_DOOM + ": \"locul doi, parcela doi = al doilea/a doua\"; the article \"al\" is part of the ordinal, and ovos-number-parser drops it in the neuter.",
 "ro_zero": "numtag/lexicon/ro.json, the ro writer: an ordinal starts at 1, and no saved source gives an ordinal of 0.",
 "ro_gender": RO_DOOM + ": \"doi2 num. m., f. două\", \"!unu2 num. m., g.-d. unuia; f. una\"; the last word agrees with the gender of the call, also after a scale word (\"o mie una\", \"două milioane două\"); ovos-number-parser writes the masculine there.",
 "ro_range": "numtag/lexicon/ro.json, the ro writer: an ordinal goes from 1 to 10^21 - 1, and outside it spell() raises; ovos-number-parser writes these numbers.",
 "ro_fraction": "numtag/lexicon/ro.json, the ro fraction block: DOOM 3 lists jumătate, treime, pătrime and cincime as nouns; the count agrees with the feminine noun (\"o jumătate\"). ovos-number-parser writes \"una jumătăți\" and \"trei douăzeci și cinci părți\". SILVER: the reading \"trei pe douăzeci și cinci\".",
 "ro_decimal": "SILVER: CLDR RBNF ro x.x \"←← virgulă →→\" and numtag read each decimal digit; ovos-number-parser reads the digits as one number. No saved source.",
 "ro_big": "numtag/lexicon/ro.json, the ro writer: the scale words stop at trilion (10^18), so from 10^21 the writer reads the exponent.",
})
def category_ro(row, got):
    kw, out, mine = row.get("kw", {}), str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction":
        if row["arg"].split("/")[1].lstrip("-") == "0": return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
        return "ro_fraction"
    if row["fn"] == "number" and isinstance(row["arg"], float): return "ro_decimal"
    if row["fn"] == "ordinal" or kw.get("ordinals"):
        if str(row["arg"]) == "0": return "ro_zero"
        if got == {"err": "ValueError"}: return "ro_range"
        if kw.get("gender") == "neutral" and "al " + out == mine: return "ro_article"
        return "ro_ordinal" if mine.startswith(("al ", "a ", "primul", "prima")) else None
    if kw.get("gender") in ("feminine", "neutral") and out != mine:
        last = {"unu": "una" if kw["gender"] == "feminine" else "unu", "doi": "două", "doisprezece": "douăsprezece"}
        if re.sub(r"\b(unu|doi|doisprezece)$", lambda m: last[m.group(1)], out) == mine: return "ro_gender"
    if "ori zece la puterea" in mine:
        return "ro_decimal" if "ori zece la puterea" in out else "ro_big"
    return None
RU_CLDR = "CLDR RBNF ru (common/rbnf/ru.xml as shipped in unicode-rbnf 2.5.1)"
RU_ROSENTAL = "Д. Э. Розенталь, Справочник по правописанию и литературной правке (1985), § 45 (Papers/Languages/Slavic/rozental1985_spravochnik_pravopisanie_literaturnaya_pravka_ocr.pdf)"
SRC.update({
 "ru_one_scale": RU_CLDR + ", %spellout-cardinal-masculine: \"1000: ←%spellout-cardinal-feminine← $(cardinal,one{тысяча}few{тысячи}other{тысяч})$[ →→];\" and \"1000000: ←%spellout-cardinal-masculine← $(cardinal,one{миллион}…)$\": a scale noun keeps its count (\"одна тысяча\", \"один миллион\"); ovos-number-parser drops it.",
 "ru_decimal": "SILVER: the decimal word \"запятая\" (CLDR ru numbers write the decimal sign \",\"); ovos-number-parser writes \"точка\" and pads the decimals with \"ноль\".",
 "ru_long": "numtag/lexicon/ru.json, the setting scale: Russian counts in the short scale (CLDR RBNF ru: \"миллиард\", \"триллион\"); the writer has no long-scale reading, and ovos-number-parser writes \"биллион\".",
 "ru_fraction": RU_ROSENTAL + ", п. 3: \"Д р о б н ы е числительные пишутся раздельно, например: две пятых ( 2/ 5)\": the numerator in the feminine and the denominator an ordinal, -ая after one and -ых after other counts; ovos-number-parser writes the masculine (\"один миллионный\"), the nominative plural (\"две девятые\") or a mixed number.",
 "ru_range": "numtag/lexicon/ru.json, the ru writer: a cardinal goes up to 10^18 - 1 and an ordinal up to 10^15 - 1; past it the cardinal spells the power of ten and the ordinal raises ValueError.",
 "ru_negative": "numtag/lexicon/ru.json, the ru writer: a negative ordinal reads the minus word, as a negative cardinal; ovos-number-parser returns the digits.",
})
def category_ru(row, got):
    kw = row.get("kw", {})
    if kw.get("scale") == "long":
        if "биллион" in str(row.get("out")): return "ru_long"
        return category_ru({**row, "kw": {k: v for k, v in kw.items() if k != "scale"}}, got)
    out, mine = str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction" and row["arg"].split("/")[1].lstrip("-") == "0":
        return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
    if row["fn"] in ("ordinal", "number") and str(row["arg"]).startswith("-") and re.fullmatch(r"-\d+", out): return "ru_negative"
    if "умножить на десять" in mine or got == {"err": "ValueError"}: return "ru_range"
    flat = lambda t: re.sub(r"\b(один|одна) (?=(тысяч|миллион|миллиард|триллион|квадриллион))", "", t.replace("ё", "е"))
    if row["fn"] == "fraction":
        return "ru_fraction" if re.search(r"(ая|ых|ьих|ья)$", mine) else None
    if " запятая " in mine and flat(re.sub(r"( ноль)+$", "", out.replace(" точка ", " запятая "))) == flat(mine): return "ru_decimal"
    if flat(out) == flat(mine): return "ru_one_scale"
    return None
GL_NORMAS = "RAG e ILG, Normas ortográficas e morfolóxicas do idioma galego, 23.ª ed. (2012), §16 (Papers/Languages/Iberian/Galician/)"
SRC.update({
 "gl_cento": GL_NORMAS + ", p. 98: \"cento un, cento unha etc.\": no \"e\" after the hundreds; ovos-number-parser writes \"cento e un\" and \"novecentos e noventa\".",
 "gl_gender": GL_NORMAS + ", p. 98: \"un/unha\", \"dous/dúas\", \"douscentos / duascentas\", and one form for the other numerals (\"catro\", \"cinco\"); ovos-number-parser writes the masculine there or a feminine of an invariable numeral (\"catra\").",
 "gl_ordinal": GL_NORMAS + ", §16.2, p. 100: \"sétimo\", \"undécimo / décimo primeiro\", \"duodécimo / décimo segundo\", the first form of each pair; ovos-number-parser writes \"séptimo\" and leaves the ordinals of 200 to 900 empty. SILVER: \"ducentésimo\" and the other hundreds.",
 "gl_zero": "numtag/lexicon/gl.json, the gl writer: an ordinal starts at 1, and no saved source gives an ordinal of 0.",
 "gl_fraction": GL_NORMAS + ", §16.4, p. 101: \"a partir de 1/11 ... o partitivo faise engadindo ao cardinal o sufixo -avo: (1/16) un dezaseisavo, (2/29) dous vinte e noveavos\"; ovos-number-parser writes \"un medios\" and \"un trinta\".",
 "gl_short": "numtag/lexicon/gl.json, the setting scale: Galician counts in the long scale only (RAG, Dicionario, «billón»: \"Un millón de millóns.\"), so a call for the short scale reads the long one.",
 "gl_big": "numtag/lexicon/gl.json, the gl writer: the scale words stop at trillón (10^18), so from 10^24 the writer reads the exponent; ovos-number-parser writes words such as \"sexdecillóns\".",
 "gl_range": "numtag/lexicon/gl.json, the gl writer: an ordinal goes from 1 to 10^24 - 1, and outside it spell() raises; ovos-number-parser writes these numbers.",
 "gl_decimal": "SILVER: numtag reads each decimal digit, and ovos-number-parser reads the digits as one number. No saved source.",
})
GL_PAIRS = {("un", "unha"), ("dous", "dúas")}
def gl_tokens_agree(out, mine):
    a, b = out.split(), mine.split()
    return len(a) == len(b) and all(x == y or (x, y) in GL_PAIRS or (x.endswith(("centos", "centas")) and y.endswith("centas"))
                                    or (y.endswith("o") and x == y[:-1] + "a") for x, y in zip(a, b))
def category_gl(row, got):
    if row.get("kw", {}).get("scale") == "short":  # the reason of the same row in the long scale, else the scale
        long = category_gl({**row, "kw": {k: v for k, v in row["kw"].items() if k != "scale"}}, got)
        return long or ("gl_short" if re.search(r"illón|illóns", str(row.get("out"))) else None)
    kw, out, mine = row.get("kw", {}), str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction":
        if row["arg"].split("/")[1].lstrip("-") == "0": return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
        return "gl_fraction"
    if row["fn"] == "number" and isinstance(row["arg"], float): return "gl_decimal"
    if row["fn"] == "ordinal" or kw.get("ordinals"):
        if str(row["arg"]) == "0": return "gl_zero"
        if got == {"err": "ValueError"}: return "gl_range"
        return "gl_ordinal" if got.get("out") else None
    bare = re.sub(r"\b(cento|mil|\w+centos|\w+centas|\w+llóns?) e ", r"\1 ", out)
    if bare == mine: return "gl_cento"
    if gl_tokens_agree(bare, mine): return "gl_gender"
    if "por dez elevado a" in mine: return "gl_big"
    return None
CA_GIEC = "IEC, Gramàtica de la llengua catalana (2016), §17.2 (Papers/Languages/Iberian/Catalan/giec_17_2_numerals.html)"
SRC.update({
 "ca_ordinal": CA_GIEC + ", §17.2.5: the ordinals past 4 \"es formen d’una manera general a partir dels nombres cardinals i el sufix ‑è / ‑en(a), com els fraccionaris (vint-i-dosè, cent vint-i-cinquè, centè, dos-centè, milè)\", and \"cent dosè, cent tresè, dos milè\"; ovos-number-parser writes \"cent primer\" and \"milè primer\".",
 "ca_short": "numtag/lexicon/ca.json, the setting scale: Catalan counts in the long scale only (DIEC2, «bilió»: \"Milió de milions.\"), so a call for the short scale reads the long one.",
 "ca_range": "numtag/lexicon/ca.json, the ca writer: an ordinal goes from 1 to 10^36 - 1, and outside it spell() raises.",
 "ca_zero": "numtag/lexicon/ca.json, the ca writer: an ordinal starts at 1.",
 "ca_gender": CA_GIEC + ", quadre 17.1: \"1 un una 2 dos dues 21 vint-i-un vint-i-una\", \"200 dos-cents dues-centes\", and the other numerals have one form; ovos-number-parser writes \"seta\", \"vinta i una\" and the masculine after mil.",
 "ca_fraction": CA_GIEC + ", §17.2.2: the fractions take the ordinal form, with mig, meitat and terç, \"dos quarts\"; ovos-number-parser writes \"un migs\", \"un trentens\" and \"un deu mil\".",
 "ca_big": "numtag/lexicon/ca.json, the scale_noun entries: milió, miliard (10^9), bilió, trilió, quadrilió, quintilió; there is no \"biliard\", so 10^15 reads \"mil bilions\", and the exponent form starts at 10^36.",
})
CA_PAIRS = {("un", "una"), ("dos", "dues"), ("cents", "centes")}
def ca_tokens(text):
    return [t for t in re.split(r"[ -]", text) if t != "i"]
def category_ca(row, got):
    if row.get("kw", {}).get("scale") == "short":  # the reason of the same row in the long scale, else the scale
        long = category_ca({**row, "kw": {k: v for k, v in row["kw"].items() if k != "scale"}}, got)
        return long or ("ca_short" if re.search(r"ili(ó|ons|ard)", str(row.get("out"))) else None)
    kw, out, mine = row.get("kw", {}), str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction":
        if row["arg"].split("/")[1].lstrip("-") == "0": return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
        last = mine.split()[-1]
        one = row["arg"].lstrip("-").split("/")[0] == "1"
        named = {"mig", "terç", "quart"} if one else {"migs", "terços", "quarts"}
        return "ca_fraction" if last in named or last.endswith("è" if one else "ens") else None
    if row["fn"] == "ordinal" or kw.get("ordinals"):
        if str(row["arg"]) == "0": return "ca_zero"
        if got == {"err": "ValueError"}: return "ca_range"
        if " " not in mine and "-" not in mine and re.fullmatch(r"(primer|segon|tercer|quart)a?", mine): return "ca_ordinal"
        return "ca_ordinal" if re.search(r"(è|ena)$", mine) else None
    if kw.get("gender") == "feminine":
        a, b = ca_tokens(out), ca_tokens(mine)
        if len(a) == len(b) and all(x == y or (x, y) in CA_PAIRS or x == y + "a" for x, y in zip(a, b)): return "ca_gender"
    if re.search(r"biliard|triliard", out) or "per deu elevat a" in out + mine: return "ca_big"
    return None
NL_TA = "Taaladvies.net, «Aaneenschrijven van telwoorden (algemeen)» (Papers/Languages/Germanic/Dutch/taaladvies-aaneenschrijven-telwoorden.html)"
SRC.update({
 "nl_one_scale": "SILVER: a round scale ordinal has no count, \"miljoenste\", as \"honderdste\" and \"duizendste\", by the pattern of \"vier miljoenste\" (Taaladvies.net, «Aaneenschrijven van telwoorden (algemeen)»); ovos-number-parser writes \"één miljoenste\" after a higher scale word.",
 "nl_een": "Taaladvies.net, «Eén / een van de» (Papers/Languages/Germanic/Dutch/taaladvies-een-of-een-van-de.html): \"komen er bijvoorbeeld uitspraaktekens op een als men een precies aantal bedoelt: Hij heeft nog één rekening (en geen twee rekeningen) te betalen\"; numtag writes \"één\" for a 1 that is a word of its own and \"een\" inside a word; ovos-number-parser places the accent elsewhere.",
 "nl_decimal": "numtag docs/values.md: a value is a canonical digit string, so 2.25 has two decimals; ovos-number-parser pads the decimals with \"nul\" to three places.",
 "nl_negative": "numtag/lexicon/nl.json, the nl writer: a negative ordinal reads the minus word, as a negative cardinal; ovos-number-parser returns the digits.",
 "nl_range": "numtag/lexicon/nl.json, the nl writer: a number goes up to 10^24 - 1, the last scale word of this lexicon (triljard), and outside it spell() raises.",
 "nl_ordinals": "ovos-number-parser 0.31.5a2 numbers_nl.py: pronounce_number reads ordinals=True as a cardinal; numtag reads the ordinal.",
 "nl_improper": NL_TA + ": \"Bij breuken is de teller een hoofdtelwoord en de noemer een rangtelwoord.\", so 4/3 reads \"vier derde\"; ovos-number-parser reads an improper fraction as a mixed number (\"één en één derde\").",
 "nl_half": "SILVER: numtag reads n/2 with \"halve\" (\"vier halve\"), ovos-number-parser with the ordinal \"tweede\"; no saved rule for either.",
 "nl_short": "numtag/lexicon/nl.json, the setting scale: Dutch counts in the long scale only (Onze Taal 70 (2001): \"duizend miljoen is een miljard\"), so a call for the short scale reads the long one.",
})
def nl_fixed(out):
    """ovos-number-parser's text with its known differences undone: "één", decimals padded with "nul"."""
    return re.sub(r"(komma( \w+)*?)( nul)+$", r"\1", out.replace("één", "een"))
def category_nl(row, got):
    if row.get("kw", {}).get("scale") == "short":  # the reason of the same row in the long scale, else the scale
        long = category_nl({**row, "kw": {k: v for k, v in row["kw"].items() if k != "scale"}}, got)
        return long or ("nl_short" if re.search(r"iljo|iljar", str(row.get("out"))) else None)
    kw, out, mine = row.get("kw", {}), str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction" and row["arg"].split("/")[1].lstrip("-") == "0":
        return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
    if row["fn"] == "ordinal" and str(row["arg"]).startswith("-") and re.fullmatch(r"-\d+", out): return "nl_negative"
    if row["fn"] == "ordinal" and got == {"err": "ValueError"}: return "nl_range"
    if kw.get("ordinals") and not re.search(r"(de|ste)$", out) and re.search(r"(de|ste)$", mine): return "nl_ordinals"
    fixed = nl_fixed(out)
    if row["fn"] == "fraction" and " en " in fixed:  # "een en een derde" for 4/3: the word of the denominator agrees
        top, bottom = (int(x.lstrip("-")) for x in row["arg"].split("/"))
        whole, rest = divmod(top, bottom)
        sign = "min " if row["arg"].startswith("-") else ""
        word = mine.split()[-1].replace("halve", "half")
        mixed = f"{sign}{spell(str(whole), 'nl')[0].text} en {spell(str(rest), 'nl')[0].text} {word}"
        if top > bottom and rest and fixed == mixed.replace("één", "een"): return "nl_improper"
    if re.sub(r"\been (?=\w+(joen|jard)ste\b)", "", fixed) == mine.replace("één", "een") and re.search(r"\been \w+(joen|jard)ste\b", fixed): return "nl_one_scale"
    if fixed == mine.replace("één", "een"): return "nl_decimal" if row["fn"] == "number" and isinstance(row["arg"], float) else "nl_een"
    if row["fn"] == "fraction" and fixed.endswith(" tweede") and fixed[:-len("tweede")] + "halve" == mine.replace("één", "een"): return "nl_half"
    return None
EN_GPO = "U.S. Government Publishing Office, Style Manual (2016) (Papers/Languages/Germanic/English/GPO-STYLEMANUAL-2016.pdf)"
SRC.update({
 "en_hyphen": EN_GPO + ", 6.36: \"Print a hyphen between the elements of compound numbers from twenty-one to ninety-nine\"; ovos-number-parser writes \"twenty one\".",
 "en_ordinal_and": "numtag/lexicon/en.json, the en writer: the first ordinal variant is British, with \"and\" and the comma of the cardinal (Oxford Advanced Learner's Dictionary, «and»: \"two thousand, two hundred and sixty-four\"); ovos-number-parser writes the American ordinal, the second variant.",
 "en_and_last": "CLDR RBNF en (common/rbnf/en.xml as shipped in unicode-rbnf 2.5.1), %%commas: \"1: ' and =%spellout-cardinal-verbose=;\", so a last group below 100 follows \"and\" (\"ten thousand and one\"); ovos-number-parser writes a comma.",
 "en_long_ordinal": "numtag/lexicon/en.json, the en writer: an ordinal counts in the scale of the call, as the cardinal (Oxford Advanced Learner's Dictionary, «billion»: \"(British English, old-fashioned) 1 000 000 000 000; one million million\"); ovos-number-parser reads an ordinal in the short scale only.",
 "en_no_comma": "numtag/lexicon/en.json, the en writer writes the spoken form: a comma is no word, so the groups are joined by a space (OALD «and» prints \"two thousand, two hundred and sixty-four\"; the comma is print punctuation); ovos-number-parser writes the comma.",
 "en_range": "numtag/lexicon/en.json, the en writer: a number goes up to 10^33 - 1, the last scale word of this lexicon (nonillion), and outside it spells the power of ten or raises ValueError; ovos-number-parser raises NotImplementedError for an ordinal from 10^18 or writes scale words this lexicon does not list.",
 "en_one_hundredth": "CLDR RBNF en (common/rbnf/en.xml as shipped in unicode-rbnf 2.5.1), %spellout-ordinal: \"100: ←%spellout-numbering← hundred→%%th→;\", so 100th reads \"one hundredth\"; ovos-number-parser writes \"hundredth\".",
 "en_fraction_scale": "SILVER: a denominator 10^n drops its count (\"seven millionths\"; CLDR RBNF en %spellout-ordinal: \"1000000: ←%spellout-numbering← million→%%th→;\" gives the ordinal \"one millionth\"); no saved example; ovos-number-parser writes \"seven one millionths\".",
})
SRC["en_and_last_hyphen"] = "Both rules: " + SRC["en_and_last"] + " " + SRC["en_hyphen"]
def category_en(row, got, out=None):
    if row["fn"] == "ordinal" and row.get("kw", {}).get("scale") == "long":
        short = spell(str(row["arg"]), "en", form=SpokenForm.ORDINAL, scale="short")[0].text
        if category_en({**row, "kw": {k: v for k, v in row["kw"].items() if k != "scale"}}, {"out": short}): return "en_long_ordinal"
    kw, mine = row.get("kw", {}), str(got.get("out", got.get("err")))
    out = out or str(row.get("out", row.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction" and row["arg"].split("/")[1].lstrip("-") == "0":
        return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
    if out == "NotImplementedError" or "times ten to the power of" in mine or got == {"err": "ValueError"}: return "en_range"
    if row["fn"] == "number" and kw.get("ordinals") and mine == "one " + out: return "en_one_hundredth"
    flat = mine.replace("-", " ")
    if flat == out.replace("-", " ") and "-" in mine: return "en_hyphen"
    theirs = out.replace("-", " ")
    if re.sub(r", (?=((twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)( \w+)?|\w+)( \w+ths?)?$)", " and ", theirs).replace(",", "") == flat \
            and not re.search(r"hundred", flat.rsplit(" and ", 1)[-1]):
        return "en_and_last_hyphen" if "-" in mine and "-" not in out else "en_and_last"
    if "," in out:
        reason = category_en(row, {"out": mine}, out.replace(",", ""))
        return reason or ("en_no_comma" if out.replace(",", "") == mine else None)
    if row["fn"] != "number" and re.sub(r",| and(?= )", "", flat) == out.replace("-", " "): return "en_ordinal_and"
    if row["fn"] == "fraction" and re.sub(r" one (?=(hundred|thousand|\w+illion)ths?$)", " ", out.replace("-", " ")) == flat:
        return "en_fraction_scale"
    return None
NB_BM = "Bokmålsordboka (ord.uib.no; Papers/Languages/Germanic/Norwegian Bokmål/)"
NB_CLDR = "CLDR RBNF no (common/rbnf/no.xml as shipped in unicode-rbnf 2.5.1)"
NB_SR = "Språkrådet, «Tall, tid og dato» (Papers/Languages/Germanic/Norwegian Bokmål/sprakradet_tall-tid-dato.html)"
SRC.update({
 "nb_decimal": "numtag docs/values.md: a value is a canonical digit string, so 2.25 has two decimals; ovos-number-parser pads the decimals with \"null\".",
 "nb_accent": NB_BM + ", «million»: \"én million\"; " + NB_CLDR + ", %spellout-cardinal-reale: \"1000000: én million[ →→];\"; ovos-number-parser writes \"en million\" or no count.",
 "nb_groups": NB_CLDR + ", %spellout-cardinal-reale: \"2000000: ←← millioner[ →→];\" and %%and-small: \"100: =%%spellout-cardinal-reale=;\": \"og\" comes only after \"hundre\" and before a last group below 100 after \"tusen\"; ovos-number-parser writes \"og\" before every group.",
 "nb_fraction": NB_SR + ": \"Hovedregelen er at vi bruker grunntall i nevneren i brøker. åtte trettendeler ni trettifiredeler\", \"en tredel eller en tredjedel\"; ovos-number-parser writes the ordinal (\"ni tredje\", \"en åttendedel\").",
 "nb_range": "numtag/lexicon/nb.json, the nb writer: a number goes up to 10^21 - 1, the last scale word of this lexicon (trillion), and outside it spells the power of ten or raises ValueError.",
 "nb_negative": "numtag/lexicon/nb.json, the nb writer: a negative ordinal reads the minus word, as a negative cardinal; ovos-number-parser returns the digits.",
 "nb_zero": NB_CLDR + ", %spellout-ordinal-masculine: \"0: nullte;\"; ovos-number-parser writes \"nulte\".",
 "nb_short": "numtag/lexicon/nb.json, the setting scale: Norwegian counts in the long scale (" + NB_BM + ", «billion»: \"grunntallet 1 000 000 000 000\"); the writer has no short-scale reading.",
})
def category_nb(row, got):
    kw = row.get("kw", {})
    if kw.get("scale") == "short":
        long = category_nb({**row, "kw": {k: v for k, v in kw.items() if k != "scale"}}, got)
        return long or ("nb_short" if re.search(r"illi|illiard", str(row.get("out"))) else None)
    out, mine = str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction" and row["arg"].split("/")[1].lstrip("-") == "0":
        return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
    if row["fn"] in ("ordinal", "number") and str(row["arg"]).startswith("-") and re.fullmatch(r"-\d+", out): return "nb_negative"
    if out == "nulte" and mine == "nullte": return "nb_zero"
    if "ti opphøyd i" in mine or got == {"err": "ValueError"}: return "nb_range"
    if row["fn"] == "fraction":  # the numerator agrees, and the part is the cardinal and "del": "to tredeler"
        top, bottom = (int(x.lstrip("-")) for x in row["arg"].split("/"))
        theirs = out.removeprefix("minus ").split(" og ")[0] if top < bottom else out.removeprefix("minus ")
        same = mine.removeprefix("minus ").split()[0] == theirs.split()[0] or top > bottom
        return "nb_fraction" if same and re.search(r"(del|deler|halv|halve)$", mine) else None
    flat = lambda t: re.sub(r"\b(én|en) (?=\w*(illion|illiard))", "", t)
    if flat(re.sub(r"( null)+$", "", out)) == flat(mine) and " komma " in mine: return "nb_decimal"
    if flat(out) == flat(mine): return "nb_accent"
    if flat(out).replace(" og ", " ") == flat(mine).replace(" og ", " "): return "nb_groups"
    return None
DE_RR = "Rat für deutsche Rechtschreibung, Amtliches Regelwerk (2024) (Papers/Languages/Germanic/German/rechtschreibrat_amtliches_regelwerk_2024.pdf)"
DE_CLDR = "CLDR RBNF de (common/rbnf/de.xml as shipped in unicode-rbnf 2.5.1)"
SRC.update({
 "de_ordinal": DE_RR + ", § 36(1.6), p. 61: one word for \"allgemein um Ordinalzahlen\": \"der einhundertste Geburtstag, der fünfhunderttausendste Fall, der zweimillionste Besucher\"; ovos-number-parser writes \"zwei Millionenste\" and reads ordinals=True as a cardinal.",
 "de_negative": "numtag/lexicon/de.json, the de writer: a negative ordinal reads the minus word, as a negative cardinal; ovos-number-parser returns the digits.",
 "de_fraction": DE_RR + ", § 56(6) E5, p. 87: \"In allen übrigen Fällen schreibt man Bruchzahlen auf -tel und -stel entsprechend § 55 groß: ein Drittel, das erste Fünftel, neun Zehntel des Umsatzes\"; ovos-number-parser writes \"ein drittel\" and \"eins dreißigste\".",
 "de_decimal": "numtag docs/values.md: a value is a canonical digit string, so 2.25 has two decimals; ovos-number-parser pads the decimals with \"null\" to three places.",
 "de_gender": DE_CLDR + ", %spellout-cardinal-masculine: \"1: ein\" and \"100: ←%spellout-cardinal-masculine←hundert[→→]\", so a count before a masculine or neuter noun ends in \"ein\" (\"eintausendein\"); ovos-number-parser writes \"eins\".",
 "de_count": DE_CLDR + ", %spellout-numbering: \"2000000: ←%spellout-cardinal-feminine← Millionen[ →→]\": \"Million\" is a feminine noun, so the count before it ends in \"eine\" (\"einhunderteine Millionen\"); ovos-number-parser writes \"einhunderteins Millionen\".",
 "de_tausend": DE_CLDR + ", %spellout-numbering: \"1000: ←%spellout-cardinal-masculine←tausend[→→]\", so the count before \"tausend\" ends in \"ein\" (\"siebenhunderteintausend\"); ovos-number-parser writes \"siebenhunderteinstausend\".",
 "de_range": "numtag/lexicon/de.json, the de writer: a number goes up to 10^24 - 1, the last scale word of this lexicon (Trilliarde), and outside it spell() raises.",
 "de_improper": DE_RR + ", § 56(6) E5, p. 87: a fraction is the count and the -tel noun (\"um drei Viertel größer\"), so 3/2 reads \"drei Halbe\"; ovos-number-parser reads an improper fraction as a mixed number (\"eins und ein halb\").",
 "de_short": "numtag/lexicon/de.json, the setting scale: German counts in the long scale only (Duden, «Milliarde»: \"tausend Millionen\"; «Billion»: \"eine Million Millionen\"), so a call for the short scale reads the long one.",
})
def de_joined(out):
    """ovos-number-parser's ordinal as one lowercase word, with its count fixed: "zwei Millionenste" is "zweimillionste"."""
    out = re.sub(r"\beine (\w)", r"ein\1", out)
    out = re.sub(r"eins?e? (?=\w+illi)|einstausend", lambda m: "eintausend" if "t" in m[0] else "ein", out)
    out = re.sub(r"eins (?=\w)", "ein", out)
    return re.sub(r"\s+", "", re.sub(r"(illion|illiard)e?n?ste$", r"\1ste", out)).lower()
def category_de(row, got):
    if row.get("kw", {}).get("scale") == "short":  # the reason of the same row in the long scale, else the scale
        long = category_de({**row, "kw": {k: v for k, v in row["kw"].items() if k != "scale"}}, got)
        return long or ("de_short" if re.search(r"illi", str(row.get("out"))) else None)
    kw, out, mine = row.get("kw", {}), str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction":
        if row["arg"].split("/")[1].lstrip("-") == "0": return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
        if not re.search(r" (Halbe?|[A-ZÄÖÜ]\w*s?tel)$", mine): return None
        top, bottom = (int(x.lstrip("-")) for x in row["arg"].split("/"))
        if " und " in out and top > bottom: return "de_improper"
        count, word = mine.rsplit(" ", 1)
        count, word = count.replace(" ", "").lower(), word.lower()
        words = {word, re.sub(r"^halbe?$", "zweitel", word)}  # "zwei zweite"
        ours = {count + w for w in words} | {count + "ein" + w for w in words}  # "ein Hundertstel", "eins einhundertste"
        ours |= {o.removesuffix("l") for o in ours}  # "Drittel" against "dritte"
        return "de_fraction" if de_joined(out) in ours else None
    if row["fn"] == "ordinal" or kw.get("ordinals"):
        if str(row["arg"]).startswith("-") and re.fullmatch(r"-\d+", out): return "de_negative"
        if got == {"err": "ValueError"}: return "de_range"
        if not re.fullmatch(r"(minus )?\w+te", mine): return None
        spaced = de_joined(out)
        return "de_ordinal" if spaced == mine.lower() or kw.get("ordinals") and not out.endswith("te") else None
    if row["fn"] == "number" and isinstance(row["arg"], float):
        return "de_decimal" if re.sub(r"( null)+$", "", out) == mine else None
    if re.sub(r"eins( \w+illi)", r"eine\1", out) == mine: return "de_count"
    if out.replace("einstausend", "eintausend") == mine: return "de_tausend"
    if kw.get("gender") in ("masculine", "neutral") and re.sub(r"eins\b", "ein", out) == mine: return "de_gender"
    return None
def category_fr(row, got):
    kw, out, mine = row.get("kw", {}), str(row.get("out", row.get("err"))), str(got.get("out", got.get("err")))
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if kw.get("scientific"): return "scientific"
    if kw.get("digits") == "number": return "digits_number"
    if row["fn"] == "fraction":
        top, bottom = (t.lstrip("-") for t in row["arg"].split("/"))
        if bottom == "0": return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
        return "fr_fraction"
    if out == "NotImplementedError": return "onp_error"
    if kw.get("ordinals") and mine == "zéroième": return "fr_zero"
    if re.sub(r"(cent|mille) unième", r"\1 et unième", re.sub(r"-et-", " et ", out)) == mine and out != mine \
            and " et unième" in mine and re.sub(r"-et-", " et ", out) != mine: return "fr_et_unieme"
    if re.sub(r"-et-", " et ", out) == mine: return "fr_et"
    if row["fn"] == "ordinal" and re.sub(r"(vingt|cent) (mil+i\w+ième)", r"\1s \2", re.sub(r"-et-", " et ", out)) == mine: return "fr_scale_count"
    if row["fn"] == "ordinal" and out == "un " + mine: return "fr_scale_one"
    if "fois dix puissance" in out and "fois dix puissance" not in mine: return "fr_big"
    if kw.get("scale") == "short" and out != mine: return "fr_short"
    return None
def category_digits(row, got):
    return "digits_number" if row.get("kw", {}).get("digits") == "number" else None
def category(row, got):
    out, mine = row.get("out", ""), got.get("out", "")
    if row["fn"] == "ordinal" and len(str(row["arg"])) > 90: return "big_ordinal"
    if row["fn"] == "ordinal" and row["lang"] == "pt-BR" and len(str(row["arg"])) > 30 and "nonilionésimo" in mine: return "short_ordinal"
    if "quadrigentésim" in out and mine == out.replace("quadrigentésim", "quadringentésim"): return "quadringentesimo"
    if row["fn"] == "number" and isinstance(row["arg"], float) and row["arg"] == int(row["arg"]): return "whole_float"
    if row.get("kw", {}).get("scientific"): return "scientific"
    if row["fn"] == "fraction":
        top, bottom = row["arg"].split("/")
        if bottom.lstrip("-") == "0": return "zero_denominator" if got == {"err": "ZeroDivisionError"} else None
        if top.startswith("-") or bottom.startswith("-"): return "negative"
        if mine.endswith(" avos"): return "avos"
        if bottom == "200": return "ducentesimo"
        if "ésim" in mine.split()[-1]: return "ordinal_denominator"
    return None
rows = [r for r in gw.stored() if r["lang"] == lang]
bad = gw.mismatches(rows, {})
entries, left, count = [], [], collections.Counter()
for row, got in bad:
    c = {"es": category_es, "it": category_it, "de": category_de, "en": category_en, "nb": category_nb, "nl": category_nl, "ca": category_ca, "gl": category_gl, "ro": category_ro, "ru": category_ru, "fr-FR": category_fr, "fr-BE": category_fr, "fr-CH": category_fr, "id": category_digits, "ms": category_digits}.get(lang, category)(row, got)
    if c is None: left.append((row, got)); continue
    count[c] += 1
    e = {k: row[k] for k in ("lang", "fn", "arg") }
    if "kw" in row: e["kw"] = row["kw"]
    e.update(got); e["source"] = SRC[c]; entries.append(e)
print(len(bad), "in;", len(entries), "allowed;", len(left), "left;", dict(count))
for r, g in left: print("LEFT", r["fn"], r["arg"], r.get("kw"), r.get("out", r.get("err")), "|", g)
if left:
    sys.exit(f"{len(left)} rows have no category")
path = "tests/golden/onp-writers-allow.json"
text = open(path, encoding="utf-8").read()
kept = [line.rstrip(",") for line in text.strip()[1:-1].strip().split("\n") if line and f'"lang": "{lang}"' not in line]
lines = sorted(kept + [json.dumps(e, ensure_ascii=False) for e in entries], key=lambda line: json.loads(line)["lang"])  # stable
new = "[\n" + ",\n".join(lines) + "\n]\n"
if "--check" in sys.argv:
    old = [line.rstrip(",") for line in text.strip()[1:-1].strip().split("\n") if f'"lang": "{lang}"' in line]
    if sorted(old) != sorted(json.dumps(e, ensure_ascii=False) for e in entries):
        sys.exit(f"{path}: the {lang} entries differ from the golden rows")
else:
    open(path, "w", encoding="utf-8").write(new)
