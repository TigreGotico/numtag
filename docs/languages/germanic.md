# Germanic languages

numtag reads German, Dutch, West Frisian, Danish, Swedish and the two written forms of Norwegian. German, Dutch, West Frisian and Danish say the unit before the ten: German "einundzwanzig" is 21. Swedish says the ten first, and Norwegian has both orders. German writes a number below a million as one word.

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| German | every `de` tag | `numtag/lexicon/de.json` | long | 191 | 191 |
| Dutch | every `nl` tag | `numtag/lexicon/nl.json` | long | 186 | 186 |
| West Frisian | every `fy` tag | `numtag/lexicon/fy.json` | long | 150 | 150 |
| Danish | every `da` tag | `numtag/lexicon/da.json` | long | 181 | 181 |
| Swedish | every `sv` tag | `numtag/lexicon/sv.json` | long | 176 | 176 |
| Norwegian Bokmål | `nb`, `no` | `numtag/lexicon/nb.json` | long | 176 | 176 |
| Norwegian Nynorsk | every `nn` tag | `numtag/lexicon/nn.json` | long | 154 | 154 |

The gold rows are in `tests/gold/<lexicon>.jsonl`. Each row holds a sentence, the numbers in it, and the source of its reading. No native speaker has checked these lexicons or their gold rows.

## Tens and units

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read('Er wurde einundzwanzig.', 'de')
[('einundzwanzig', '21')]
>>> read('Es kostet zweitausenddreihundertvierundfünfzig Euro.', 'de-AT')
[('zweitausenddreihundertvierundfünfzig', '2354')]
>>> read('Hij is eenentwintig jaar.', 'nl')
[('eenentwintig', '21')]
>>> read('Det kostar tjugoen kronor.', 'sv')
[('tjugoen', '21')]
>>> read('Hun er enogtyve år.', 'da')
[('enogtyve', '21')]
>>> read('Det kostet tusen og to kroner.', 'no')
[('tusen og to', '1002')]
```

## Examples from the gold rows

```python
>>> read('Tausend Dank!', 'de')
[('Tausend', '1000')]
>>> read('Er zahlte 12,50 Euro.', 'de')
[('12,50', '12.5')]
>>> read('Duizend dank!', 'nl')
[('Duizend', '1000')]
>>> read('Het kost 3,99 euro.', 'nl')
[('3,99', '3.99')]
>>> read('Hy rint achttûzen meter.', 'fy')
[('achttûzen', '8000')]
>>> read('It is de twadde dei.', 'fy')
[('twadde', '2')]
>>> read('Tusind tak!', 'da')
[('Tusind', '1000')]
>>> read('Hun vandt 1. præmie.', 'da')
[('1', '1')]
>>> read('Tusen tack!', 'sv')
[('Tusen', '1000')]
>>> read('Hon kom 1:a i loppet.', 'sv')
[('1:a', '1')]
>>> read('Tusen takk!', 'nb')
[('Tusen', '1000')]
>>> read('Hun vant 1. premie.', 'nb')
[('1', '1')]
>>> read('Tusen takk!', 'nn')
[('Tusen', '1000')]
>>> read('Vi bur i tredje etasje.', 'nn')
[('tredje', '3')]
```

## Halves and vague phrases

A half before a part word halves that part. German "ein halbes Viertel" is a half of a quarter, so it reads 1/8. The rule follows Duden, "halb": "die Hälfte von etwas umfassend".

```python
>>> read('Er trank ein halbes Viertel Wein.', 'de')
[('ein halbes Viertel', '0.125')]
```

Dutch "een paar" before a noun is an indefinite pronoun: "meerdere, maar niet heel veel" (nl.wiktionary, "paar"). So a scale word after the phrase names no exact number. "een" keeps its reading as an article, a weak 1, so a reader that knows the phrase can join the two words.

```python
>>> read('Neem jij een paar appels mee?', 'nl')
[('een', '1')]
>>> read('Er kwamen een paar honderd mensen.', 'nl')
[('een', '1')]
```

## The scale

Each lexicon sets its default scale from these sources. Pass `scale="long"` or `scale="short"` to read the large scale words in the other scale. Read [../number-scale.md](../number-scale.md).

German, long scale:

> German uses the long scale: CLDR RBNF de (unicode-rbnf 2.4.1 data, de.xml), %spellout-numbering: "1000000000: eine Milliarde[ →→]", "1000000000000: eine Billion[ →→]", "1000000000000000: eine Billiarde[ →→]"

Dutch, long scale:

> Dutch uses the long scale: CLDR RBNF nl (unicode-rbnf 2.4.1 data, nl.xml), %spellout-cardinal: "1000000000: ←← miljard[ →→]", "1000000000000: ←← biljoen[ →→]", "1000000000000000: ←← biljard[ →→]"

West Frisian, long scale:

> West Frisian uses the long scale: "miljard" is 10^9 and "biljoen" 10^12 (ovos-number-parser numbers_fy.py (a lead; no Frisian dictionary entry was checked for this word))

Danish, long scale:

> Danish uses the long scale: CLDR RBNF da (unicode-rbnf 2.4.1 data, da.xml), %spellout-cardinal-common: "1000000000: milliard[ →→]", "1000000000000: billion[ →→]", "1000000000000000: billiard[ →→]"

Swedish, long scale:

> Swedish uses the long scale: CLDR RBNF sv (unicode-rbnf 2.4.1 data, sv.xml), %spellout-numbering: "1000000000: en miljard[ →→]", "1000000000000: en biljon[ →→]", "1000000000000000: en biljard[ →→]"

Norwegian Bokmål, long scale:

> Norwegian Bokmål uses the long scale: CLDR RBNF nb (unicode-rbnf 2.4.1 data, no.xml), %spellout-cardinal-reale: "1000000000: én milliard[ →→]", "1000000000000: én billion[ →→]"

Norwegian Nynorsk, long scale:

> Norwegian Nynorsk uses the long scale: CLDR RBNF nn (unicode-rbnf 2.4.1 data, nn.xml), %spellout-cardinal-reale: "1000000000: éin milliard[ →→]", "1000000000000: éin billion[ →→]"

Each word and each setting in a lexicon carries the source of its rule. [../adding-a-language.md](../adding-a-language.md) describes the lexicon format.
