# Baltic languages

<!-- agent-hint
covers: What numtag reads in Lithuanian.
source: numtag/lexicon/lt.json, tests/gold/lt.jsonl
generated: no
verify: sed '/^\x60\x60\x60/d' docs/languages/baltic.md | python -m doctest -o NORMALIZE_WHITESPACE /dev/stdin && PYTHONPATH=tests python -c $'import re,sys\nfrom pathlib import Path\nfrom test_gold import score_file\nrows=re.findall(r"lexicon/([\\w-]+)\\.json\\x60 \\| \\w+ \\| (\\d+) \\| (\\d+) \\|",Path(sys.argv[1]).read_text())\ngot=[(r[0],str(s.rows),str(s.correct)) for r in rows for s in [score_file(Path("tests/gold/"+r[0]+".jsonl"))]]\nbad=[r for r,g in zip(rows,got) if r!=g]\nprint(len(rows),"rows",len(bad),"wrong",bad)\nsys.exit(1 if bad or not rows else 0)' docs/languages/baltic.md
see: ../rulings.md, ../adding-a-language.md
-->

numtag reads Lithuanian. Lithuanian declines its numbers: a cardinal takes the case and gender of the noun it counts, and the hundreds and thousands are nouns with their own case forms. A date names its day with the pronominal ordinal, and a year ends in an ordinal.

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| Lithuanian | every `lt` tag | `numtag/lexicon/lt.json` | short | 167 | 167 |

The gold rows are in `tests/gold/lt.jsonl`. Each row holds a sentence, the numbers in it, and the source of its reading. No native speaker has checked this lexicon or its gold rows.

## Cardinals in every case

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read('Grįšiu po penkių dienų.', 'lt')
[('penkių', '5')]
>>> read('Knyga turi du šimtus puslapių.', 'lt')
[('du šimtus', '200')]
>>> read('Žygyje dalyvavo dešimt tūkstančių žmonių.', 'lt')
[('dešimt tūkstančių', '10000')]
```

## Dates and years

```python
>>> read('Susitiksime birželio dvidešimt pirmąją.', 'lt')
[('dvidešimt pirmąją', '21')]
>>> read('Du tūkstančiai dvidešimt penktieji metai buvo šilti.', 'lt')
[('Du tūkstančiai dvidešimt penktieji', '2025')]
>>> read('Vasario 16-oji yra šventė.', 'lt')
[('16-oji', '16')]
```

> Visaginas municipality, "Skaičių rašymo atmintinė", "Parengta pagal www.vlkk.lt informaciją" (knowledge/wiki/audits/numtag/lexicons/lt/pages/visaginas-skaiciu-atmintine.txt): "Žymint eilę arabiškais skaitmenimis, prie jų po brūkšnelio gali būti pridedamos kelintinio skaitvardžio galūnės".

## Fractions

A fraction counts parts named by the pronominal feminine ordinal. "ir" joins a whole number to a fraction, and joins nothing else.

```python
>>> read('Trys penktosios mokinių išlaikė egzaminą.', 'lt')
[('Trys penktosios', '0.6')]
>>> read('Nupirkau tris ir pusę kilogramo obuolių.', 'lt')
[('tris ir pusę', '3.5')]
>>> read('Penki ir šeši yra skirtingi skaičiai.', 'lt')
[('Penki', '5'), ('šeši', '6')]
```

## The scale

Lithuanian counts in the short scale: "trilijonas" is 10^12. Pass `scale="long"` to read the large scale words in the long scale. Read [../number-scale.md](../number-scale.md).

> Vikipedija (lt), "Trilijonas" (knowledge/wiki/audits/numtag/lexicons/lt/pages/ltwp-trilijonas.txt): "Lietuvoje naudojama trumpoji skalė, todėl trilijono vertė laikoma" 10^12.

Each word and each setting in a lexicon carries the source of its rule. [../adding-a-language.md](../adding-a-language.md) describes the lexicon format.

---
[← Uralic and Turkic languages](uralic-turkic.md) · [Home](../index.md) · [Slavic languages →](slavic.md)
