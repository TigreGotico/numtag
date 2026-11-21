# Slavic languages

<!-- agent-hint
covers: What numtag reads in Russian, Ukrainian, Bulgarian, Polish, Czech, Slovak, Slovene, Croatian and Serbian.
source: numtag/lexicon/{ru,uk,bg,pl,cs,sk,sl,hr,sr}.json, the same names under tests/gold/*.jsonl
generated: no
verify: sed '/^\x60\x60\x60/d' docs/languages/slavic.md | python -m doctest -o NORMALIZE_WHITESPACE /dev/stdin && PYTHONPATH=tests python -c $'import re,sys\nfrom pathlib import Path\nfrom test_gold import score_file\nrows=re.findall(r"lexicon/([\\w-]+)\\.json\\x60 \\| \\w+ \\| (\\d+) \\| (\\d+) \\|",Path(sys.argv[1]).read_text())\ngot=[(r[0],str(s.rows),str(s.correct)) for r in rows for s in [score_file(Path("tests/gold/"+r[0]+".jsonl"))]]\nbad=[r for r,g in zip(rows,got) if r!=g]\nprint(len(rows),"rows",len(bad),"wrong",bad)\nsys.exit(1 if bad or not rows else 0)' docs/languages/slavic.md
see: ../rulings.md, ../adding-a-language.md
-->

numtag reads Russian, Ukrainian, Bulgarian, Polish, Czech, Slovak, Slovene, Croatian and Serbian. The number words decline, and each lexicon lists each case form as a word.

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| Russian | every `ru` tag | `numtag/lexicon/ru.json` | short | 191 | 190 |
| Ukrainian | every `uk` tag | `numtag/lexicon/uk.json` | short | 180 | 180 |
| Bulgarian | every `bg` tag | `numtag/lexicon/bg.json` | short | 156 | 156 |
| Polish | every `pl` tag | `numtag/lexicon/pl.json` | long | 163 | 163 |
| Czech | every `cs` tag | `numtag/lexicon/cs.json` | long | 176 | 175 |
| Slovak | every `sk` tag | `numtag/lexicon/sk.json` | long | 154 | 154 |
| Slovene | every `sl` tag | `numtag/lexicon/sl.json` | long | 162 | 162 |
| Croatian | every `hr` tag | `numtag/lexicon/hr.json` | long | 169 | 168 |
| Serbian | every `sr` tag | `numtag/lexicon/sr.json` | long | 149 | 149 |

The gold rows are in `tests/gold/<lexicon>.jsonl`. Each row holds a sentence, the numbers in it, and the source of its reading. No native speaker has checked these lexicons or their gold rows.

## Tens and units

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read('двадцать пять', 'ru')
[('двадцать пять', '25')]
>>> read('dwadzieścia pięć', 'pl')
[('dwadzieścia pięć', '25')]
>>> read('dvacet pět', 'cs')
[('dvacet pět', '25')]
>>> read('pětadvacet', 'cs')
[('pětadvacet', '25')]
>>> read('petindvajset', 'sl')
[('petindvajset', '25')]
```

## Examples from the gold rows

```python
>>> read('Ответ: три тысячи.', 'ru')
[('три тысячи', '3000')]
>>> read('Это пятый этаж.', 'ru')
[('пятый', '5')]
>>> read('Відповідь: три тисячі.', 'uk')
[('три тисячі', '3000')]
>>> read('Це сотий поверх.', 'uk')
[('сотий', '100')]
>>> read('Той плати хиляда лева.', 'bg')
[('хиляда', '1000')]
>>> read('Това е пети етаж.', 'bg')
[('пети', '5')]
>>> read('Wynik to tysiąc.', 'pl')
[('tysiąc', '1000')]
>>> read('To setna rocznica.', 'pl')
[('setna', '100')]
>>> read('Výsledek je tisíc.', 'cs')
[('tisíc', '1000')]
>>> read('Je to stý den.', 'cs')
[('stý', '100')]
>>> read('Bolo ich dvetisíc.', 'sk')
[('dvetisíc', '2000')]
>>> read('Je to stý deň.', 'sk')
[('stý', '100')]
>>> read('Rezultat je tisoč.', 'sl')
[('tisoč', '1000')]
>>> read('To je prvi dan.', 'sl')
[('prvi', '1')]
>>> read('Bilo ih je tisuća.', 'hr')
[('tisuća', '1000')]
>>> read('To je prvi dan.', 'hr')
[('prvi', '1')]
```

## Czech "jednou"

Czech "jednou" is the instrumental of "jedna" and also the adverb "once". Alone, it gets the low score 0.4 for a word with a second meaning.

```python
>>> from numtag import tag_numbers
>>> [(m.text, m.value, m.confidence) for m in tag_numbers('Ahoj ještě jednou.', 'cs')]
[('jednou', '1', 0.4)]
```

> SSJČ, "jednou": "jednou čísl. nás. příslovečná 1. k jeden; jedenkrát: j. dvě jsou dvě; j. za den"; "4. kdysi; někdy: byl j. jeden král"

## Croatian "stotina"

A count and the noun "stotina" write the hundreds of a cardinal, as "petsto" does. A scale word after them counts them. "stotinu" is the hundred "sto".

```python
>>> read('pet stotina tisuća', 'hr')
[('pet stotina tisuća', '500000')]
>>> read('stotinu tisuća ljudi', 'hr')
[('stotinu tisuća', '100000')]
```

> Hrvatski pravopis (Institut za hrvatski jezik i jezikoslovlje), 5.4.1. Jednorječnice: "glavni brojevi stotice do 1000: sto ili stotinu"; "Stotice do 1000 mogu se pisati i kao sveza glavnoga broja i imenice stotina: četiri stotine, devet stotina."

## Serbian in two scripts

The Serbian lexicon lists its words in the Latin script. Each Cyrillic letter reads as its Latin letter or digraph, so a text in either script reads. A date names its day with the genitive ordinal, and a year ends in an ordinal.

```python
>>> read('Видимо се двадесет петог маја.', 'sr')
[('двадесет петог', '25')]
>>> read('To se desilo dve hiljade dvadeset pete godine.', 'sr')
[('dve hiljade dvadeset pete', '2025')]
>>> read('Хиљаду и једна ноћ', 'sr')
[('Хиљаду и једна', '1001')]
>>> read('Rođen je 25. avgusta.', 'sr')
[('25', '25')]
```

> Vikipedija (sr), "Редни број": "Када се редни број пише цифрама тада се иза броја додаје тачка да би се разликовало од обичног броја: 13. страна, 25. август, 3. спрат."

## The scale

Each lexicon sets its default scale from these sources. Pass `scale="long"` or `scale="short"` to read the large scale words in the other scale. Read [../number-scale.md](../number-scale.md).

Russian, short scale:

> CLDR RBNF ru renders 10^9 as "один миллиард" and 10^12 as "один триллион": Russian names 10^9 "миллиард" and counts the -illions in the short scale. Wiktionary (en), "триллион": "trillion".

Ukrainian, short scale:

> CLDR RBNF uk renders 10^9 as "один мільярд" and 10^12 as "один більйон": Ukrainian names 10^9 "мільярд" and 10^12 "більйон", so a -illion counts in the short scale. Wiktionary (en), "трильйон": "trillion".

Bulgarian, short scale:

> CLDR RBNF bg renders 10^9 as "един милиард" and 10^12 as "един трилион": Bulgarian names 10^9 "милиард" and counts the -illions in the short scale.

Polish, long scale:

> CLDR RBNF pl renders 10^9 as "miliard" and 10^12 as "bilion": Polish counts in the long scale. Wiktionary (en), "bilion": "trillion", 10^12.

Czech, long scale:

> CLDR RBNF cs renders 10^9 as "jedna miliarda" and 10^12 as "jeden bilión": Czech counts in the long scale. Internetová jazyková příručka (ÚJČ AV ČR), "bilion": "milion milionů".

Slovak, long scale:

> CLDR RBNF sk renders 10^9 as "jedna miliarda" and 10^12 as "jeden bilión": Slovak counts in the long scale.

Slovene, long scale:

> CLDR RBNF sl renders 10^9 as "ena milijarda" and 10^12 as "en bilijon": Slovene counts in the long scale.

Croatian, long scale:

> CLDR RBNF hr renders 10^9 as "jedna milijarda" and 10^12 as "jedan bilijun": Croatian counts in the long scale.

Serbian, long scale:

> Vikipedija (sr), "Билион": "Билион је назив за позитиван природан број који се записује као 1.000.000.000.000".

Each word and each setting in a lexicon carries the source of its rule. [../adding-a-language.md](../adding-a-language.md) describes the lexicon format.

---
[← Baltic languages](baltic.md) · [Home](../index.md) · [French, Italian, Romanian, Basque, Indonesian and Malay →](fr-it-ro-eu-id.md)
