"""Rebuild the allow-list entries of one language from the writer golden file: each row where the
writer differs from ovos-number-parser gets the output of numtag and the source of its category.

usage: python scripts/allow_list.py LANG [--check]
A row with no category stops the script, so every entry has a source.
"""
import sys, json, collections, os, re
from pathlib import Path
os.chdir(Path(__file__).parents[1])
sys.path.insert(0, "tests"); import golden_writers as gw
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
 "it_short": "numtag/lexicon/it.json, the setting scale: Italian counts in the long scale only (CLDR RBNF it (unicode-rbnf 2.5.1): \"1000000000000: un bilione\"), so a call for the short scale reads the long one.",
 "it_apocope": "Enciclopedia dell'Italiano (Treccani, 2010-11), «numerali», ex. 24-25: in a compound before a noun «uno» \"può essere apocopato ... ottantun votanti ... quarantun anni\"; gender=masculine reads the form before a noun, as CLDR RBNF it (unicode-rbnf 2.5.1) %spellout-cardinal-masculine.",
 "it_ordinal": CLDR_IT,
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
    if kw.get("scale") == "short" and out != mine: return "it_short"
    if kw.get("gender") == "masculine" and re.sub(r"un\b", "uno", mine) == out: return "it_apocope"
    if row["fn"] == "ordinal" and " " not in mine.removeprefix("meno ") and " " in out.removeprefix("meno "): return "it_ordinal"
    if mine.replace("uno", "un") == out.replace("uno", "un"): return "it_count"
    return None
FR_ACADEMIE = "Académie française, «Questions de langue: nombres»: the traditional spelling links with a space the \"et\" of 21, 31 ... 71 (\"vingt et un\"), and \"il est également possible, en accord avec les Rectifications de l'orthographe ... de lier par un trait d'union tous les éléments\". The writer prints the traditional spelling; ovos-number-parser joins only \"-et-\", which neither spelling does."
SRC.update({
 "fr_et": FR_ACADEMIE,
 "fr_fraction": "SILVER: no saved source on the reading of a fraction in French. numtag reads the numerator as a cardinal and the denominator as a plural ordinal after a numerator other than 1, \"trois demis\", \"zéro cinquièmes\".",
 "fr_big": "numtag/lexicon/fr-FR.json, the scale_noun entries: million 10^6, milliard 10^9, billion 10^12, billiard 10^15, trillion 10^18 (long scale), so 10^15 reads \"un billiard\" and the exponent form starts at 10^24.",
 "fr_zero": "CLDR RBNF fr, %spellout-ordinal-masculine: \"0: zéroième\"; the call asks for the ordinal, and ovos-number-parser reads the cardinal.",
 "fr_scale_count": "SILVER: the count before a scale noun keeps the plural s (Académie française, «Questions de langue: nombres»: \"Milliard, million et millier, étant des noms\"), so the exact ordinal reads \"quatre-vingts millionième\"; no saved source names this ordinal.",
 "fr_scale_one": "CLDR RBNF fr, %spellout-ordinal-masculine reads the ordinal of 10^6 as \"millionième\" with no \"un\"; numtag reads every scale ordinal so, \"billiardième\".",
 "fr_short": "numtag/lexicon/fr-FR.json, the setting scale: French counts in the long scale only, so a call for the short scale reads the long one.",
})
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
    c = {"es": category_es, "it": category_it, "fr-FR": category_fr, "fr-BE": category_fr, "fr-CH": category_fr, "id": category_digits, "ms": category_digits}.get(lang, category)(row, got)
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
new = "[\n" + ",\n".join(kept + [json.dumps(e, ensure_ascii=False) for e in entries]) + "\n]\n"
if "--check" in sys.argv:
    old = [line.rstrip(",") for line in text.strip()[1:-1].strip().split("\n") if f'"lang": "{lang}"' in line]
    if sorted(old) != sorted(json.dumps(e, ensure_ascii=False) for e in entries):
        sys.exit(f"{path}: the {lang} entries differ from the golden rows")
else:
    open(path, "w", encoding="utf-8").write(new)
