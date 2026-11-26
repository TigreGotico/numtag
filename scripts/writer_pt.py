"""Write the writer block of pt-PT or pt-BR from CLDR RBNF and the -illion words of the lexicon.

usage: python scripts/writer_pt.py pt-PT|pt-BR [--check]
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from splice_writer import splice
variety = sys.argv[1]
BR = variety == "pt-BR"
SRC = "CLDR 38 RBNF pt (common/rbnf/pt.xml as shipped in unicode-rbnf 2.5.1)" if BR else "CLDR 38 RBNF pt_PT (common/rbnf/pt_PT.xml as shipped in unicode-rbnf 2.5.1)"
lex = json.load(open("numtag/lexicon/pt-PT.json"))
ill = sorted(dict(sorted({(e["rank"], e["word"]) for e in lex["entries"] if e.get("role") == "scale_noun" and e.get("rank", 0) > 1 and e["word"].endswith("ão") and ("lh" in e["word"]) == BR}, reverse=True)).items())
units = ("zero um dois três quatro cinco seis sete oito nove dez onze doze treze " + ("quatorze quinze dezesseis dezessete dezoito dezenove" if BR else "catorze quinze dezasseis dezassete dezoito dezanove")).split()
tens = "vinte trinta quarenta cinquenta sessenta setenta oitenta noventa".split()
hund_m = "duzentos trezentos quatrocentos quinhentos seiscentos setecentos oitocentos novecentos".split()
ord_u_m = "zero primeiro segundo terceiro quarto quinto sexto sétimo oitavo nono".split()
ord_t = "décim vigésim trigésim quadragésim quinquagésim sexagésim septuagésim octogésim nonagésim".split()
ord_h = "centésim ducentésim trecentésim quadringentésim quingentésim sexcentésim septingentésim octingentésim noningentésim".split()
def R(v, t): return {"value": str(v), "text": t + ";"}
def plural(w): return w[:-2] + "ões"
def cardinal(g, scale):
    w = f"%cardinal-{g}-{scale}-e"
    r = [R("-x", "menos →→")]
    u = units[:] 
    if g == "f": u[1], u[2] = "uma", "duas"
    r += [R(i, x) for i, x in enumerate(u)]
    r += [R(20 + 10 * i, f"{x}[ e →→]") for i, x in enumerate(tens)]
    r += [R(100, "cem"), R(101, "cento e →→")]
    h = hund_m if g == "m" else [x[:-2] + "as" for x in hund_m]
    r += [R(200 + 100 * i, f"{x}[ e →→]") for i, x in enumerate(h)]
    r += [R(1000, f"mil[→{w}→]"), R(2000, f"←← mil[→{w}→]")]
    m = f"←%cardinal-m-{scale}←"
    words = [(6, "milhão")] + [((6 * k if scale == "long" else 3 * k + 3), x) for k, x in ill]
    for exp, word in words:
        r += [R(10 ** exp, f"um {word}[→{w}→]"), R(2 * 10 ** exp, f"{m} {plural(word)}[→{w}→]")]
    return r, words
def ordinal(g, scale):
    e = "o" if g == "m" else "a"
    u = [x[:-1] + e if i else x for i, x in enumerate(ord_u_m)]
    r = [R("-x", "menos →→")] + [R(i, x) for i, x in enumerate(u)]
    r += [R(10 * (i + 1), f"{x}{e}[ →→]") for i, x in enumerate(ord_t)]
    r += [R(100 * (i + 1), f"{x}{e}[ →→]") for i, x in enumerate(ord_h)]
    c = f"←%cardinal-m-{scale}←"
    r += [R(1000, f"milésim{e}[ →→]"), R(2000, f"{c} milésim{e}[ →→]")]
    for exp, word in cardinal(g, scale)[1]:
        o = word.replace("lh", "li")[:-2] + "onésim" + e
        r += [R(10 ** exp, f"{o}[ →→]"), R(2 * 10 ** exp, f"{c} {o}[ →→]")]
    return r
rs = {}
for scale in ("long", "short"):
    for g in "mf":
        rs[f"cardinal-{g}-{scale}"] = {"source": SRC, "rules": cardinal(g, scale)[0]}
        rs[f"cardinal-{g}-{scale}-e"] = {"source": SRC + ", %%spellout-cardinal-*-with-e", "rules": [R(0, f" e =%cardinal-{g}-{scale}="), R(100, f"→%optional-e→=%cardinal-{g}-{scale}="), R(1000, f" =%cardinal-{g}-{scale}=")]}
        rs[f"ordinal-{g}-{scale}"] = {"source": SRC, "rules": ordinal(g, scale)}
rs["optional-e"] = {"source": SRC + ", %%optional-e", "rules": [R(0, " e "), R(1, " ")]}
def form(kind, scale):
    v = lambda g: [{"ruleset": f"{kind}-{g}-{scale}", "reason": "standard"}]
    return {"variants": v("m"), "gender": {"masculine": v("m"), "feminine": v("f")}}
forms = {}
for kind in ("cardinal", "ordinal"):
    f = form(kind, "long"); f["scale"] = {"short": form(kind, "short")}
    forms[kind] = f
forms["ordinal"]["minimum"] = "0"
top = next(k for k in range(1, 1000) if k + 1 not in dict(ill))  # the -illions run 2..top with no gap
for f in forms.values():
    f["maximum"] = "9" * (6 * top + 6)
    f["scale"]["short"]["maximum"] = "9" * (3 * top + 9)
block = {"source": SRC + ". Changed from it: the scale words past \"" + ("bilhão" if BR else "bilião") + "\" come from the scale_noun entries of this lexicon, and a quotient of a scale word reads up to 999999 (\"nove mil novecentos e noventa e nove milhões\") as ovos-number-parser 0.30.1a1 writes it, with no class \"mil milhões\" of its own. The conjunction joins only the last class, when it is below 100 or a round hundred: Cunha & Cintra, Nova Gramática do Português Contemporâneo (1984), p. 372, «Não se emprega a conjunção entre os milhares e as centenas, salvo quando o número terminar numa centena com dois zeros», and Ciberdúvidas 34389 («mil e vinte», «mil e um»), as quoted in ovos-number-parser numbers_pt.py. 300th is \"trecentésimo\", the main entry of Priberam (\"tricentésimo\": «O mesmo que trecentésimo»). The count before an ordinal scale word is masculine in both genders (\"dois milésima\"), as ovos-number-parser writes it.",
         "rulesets": rs, "forms": forms,
         "decimal": {"word": "vírgula", "places": 3, "read": "number", "source": SRC + ", %spellout-cardinal-masculine x.x: \"←← vírgula →→\": the decimals read as one number. ovos-number-parser 0.30.1a1 keeps three decimals by default: 1234.5678 reads \"mil duzentos e trinta e quatro vírgula quinhentos e sessenta e oito\"."},
         "scientific": {"times": "vezes dez elevado a", "source": "ovos-number-parser 0.30.1a1, the writer golden file of numtag: 10^300 reads \"um vezes dez elevado a trezentos\"."},
         "fraction": {"mixed": False, "limit": 10, "single": "um {denominator}", "plural": "s",
                      "named": dict(zip(map(str, range(2, 11)), "meio terço quarto quinto sexto sétimo oitavo nono décimo".split())),
                      "denominator": "{cardinal} avos", "source": "Ciberdúvidas 11493 (https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/numeros-fraccionarios/11493): «designa se 1/4, 1/5, etc., por um quarto, um quinto, etc. (mas um meio, um terço), 1/10 por um décimo». Ciberdúvidas 35323 (https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/denominadores-multiplos-de-1000-10-000-100-000-1000-000/35323), after Celso Cunha: «pode ser usada a mesma designação para o fracionário que para ordinal, se expresso numa só palavra [...] Quando o ordinal é expresso por mais que uma palavra, usa-se [...] o cardinal seguido do termo avos». Ciberdúvidas 4181 (https://ciberduvidas.iscte-iul.pt/consultorio/perguntas/um-doze-avos/4181): «escreve-se um doze avos, dois treze avos, sempre com avos no plural»."}}
splice(Path(f"numtag/lexicon/{variety}.json"), block, check="--check" in sys.argv)
