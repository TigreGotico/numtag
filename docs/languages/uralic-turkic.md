# Uralic and Turkic languages

numtag reads Finnish, Estonian, Hungarian, Turkish and Azerbaijani. Finnish and Hungarian write a number below a thousand as one word. A period after digits can make an ordinal: "3." is "third".

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| Finnish | every `fi` tag | `numtag/lexicon/fi.json` | long | 181 | 181 |
| Estonian | every `et` tag | `numtag/lexicon/et.json` | long | 170 | 170 |
| Hungarian | every `hu` tag | `numtag/lexicon/hu.json` | long | 191 | 189 |
| Turkish | every `tr` tag | `numtag/lexicon/tr.json` | short | 187 | 187 |
| Azerbaijani | every `az` tag | `numtag/lexicon/az.json` | short | 176 | 176 |

The gold rows are in `tests/gold/<lexicon>.jsonl`. Each row holds a sentence, the numbers in it, and the source of its reading. No native speaker has checked these lexicons or their gold rows.

## Tens and units

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read('kaksikymmentäviisi', 'fi')
[('kaksikymmentäviisi', '25')]
>>> read('kakskümmend viis', 'et')
[('kakskümmend viis', '25')]
>>> read('huszonöt', 'hu')
[('huszonöt', '25')]
>>> read('yirmi beş', 'tr')
[('yirmi beş', '25')]
>>> read('iyirmi beş', 'az')
[('iyirmi beş', '25')]
```

## Examples from the gold rows

```python
>>> read('Oikea luku on tuhat.', 'fi')
[('tuhat', '1000')]
>>> read('Tämä on sadas kerta.', 'fi')
[('sadas', '100')]
>>> read('Vastus on kaks tuhat.', 'et')
[('kaks tuhat', '2000')]
>>> read('Sõin pool kooki.', 'et')
[('pool', '0.5')]
>>> read('A válasz ezeregy.', 'hu')
[('ezeregy', '1001')]
>>> read('A 3. sor üres.', 'hu')
[('3', '3')]
>>> read('Cevap bin bir.', 'tr')
[('bin bir', '1001')]
>>> read('Biz 5. kattayız.', 'tr')
[('5', '5')]
>>> read('Cavab iki min.', 'az')
[('iki min', '2000')]
>>> read('Bu mininci ildir.', 'az')
[('mininci', '1000')]
```

## The scale

Each lexicon sets its default scale from these sources. Pass `scale="long"` or `scale="short"` to read the large scale words in the other scale. Read [../number-scale.md](../number-scale.md).

Finnish, long scale:

> Wiktionary, "biljoona" (knowledge/wiki/audits/numtag/lang-ports/uralic-turkic/sources/wikt-fi-biljoona.wikitext): "[[trillion]] {{q|short scale}}, [[billion]] {{q|long scale}}, 10<sup>12</sup>" [...]

Estonian, long scale:

> CLDR 48 RBNF et %spellout-cardinal, ICU 78 rendering of 1000000000000: "üks biljon"; CLDR 48 RBNF et %spellout-cardinal, ICU 78 rendering of 1000000000000000: "üks biljard": 'biljon' is 10^12, a million millions, so Estonian counts in the long scale.

Hungarian, long scale:

> CLDR 48 RBNF hu %spellout-cardinal, ICU 78 rendering of 1000000000: "egymilliárd"; CLDR 48 RBNF hu %spellout-cardinal, ICU 78 rendering of 1000000000000: "egybillió"; CLDR 48 RBNF hu %spellout-cardinal, ICU 78 rendering of 1000000000000000: "egybilliárd": 'milliárd' is 10^9 and 'billió' 10^12, the long scale.

Turkish, short scale:

> CLDR 48 RBNF tr %spellout-cardinal, ICU 78 rendering of 1000000000: "bir milyar"; CLDR 48 RBNF tr %spellout-cardinal, ICU 78 rendering of 1000000000000: "bir trilyon": the word for 10^12 is the short-scale 'trilyon', and 10^9 has its own word.

Azerbaijani, short scale:

> CLDR 48 RBNF az %spellout-cardinal, ICU 78 rendering of 1000000000: "bir milyard"; CLDR 48 RBNF az %spellout-cardinal, ICU 78 rendering of 1000000000000: "bir trilyon": the word for 10^12 is the short-scale 'trilyon', and 10^9 has its own word.

## Hungarian parts

Hungarian writes a decimal as a whole, "egész", and a count of parts: "három egész két tized" is 3.2. A count glued to the word for a hundredth or a thousandth multiplies it, as it multiplies the scale word: "tízezred" is a ten-thousandth, as "tízezer" is ten thousand. The parts go up to "kvadrilliárdod", 10^27.

```python
>>> read('három egész egy tízezred', 'hu')
[('három egész egy tízezred', '3.0001')]
>>> read('nulla egész kétezer-ötszáz milliomod', 'hu')
[('nulla egész kétezer-ötszáz milliomod', '0.0025')]
```

> Wiktionary, "milliomod" (knowledge/wiki/audits/numtag/follow-up-prs/hu-denominators/render/milliomod.raw): "[[millionth]] {{gloss|one of a million equal parts of a whole}}"

Each word and each setting in a lexicon carries the source of its rule. [../adding-a-language.md](../adding-a-language.md) describes the lexicon format.
