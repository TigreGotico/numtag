# Germanic languages

numtag reads German, Dutch, West Frisian, Danish, Swedish and the two written forms of Norwegian. German, Dutch, West Frisian and Danish say the unit before the ten: German "einundzwanzig" is 21. Swedish says the ten first, and Norwegian has both orders. German writes a number below a million as one word.

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| German | every `de` tag | `numtag/lexicon/de.json` | long | 191 | 191 |
| Dutch | every `nl` tag | `numtag/lexicon/nl.json` | long | 186 | 186 |
| West Frisian | every `fy` tag | `numtag/lexicon/fy.json` | long | 156 | 156 |
| Danish | every `da` tag | `numtag/lexicon/da.json` | long | 181 | 181 |
| Swedish | every `sv` tag | `numtag/lexicon/sv.json` | long | 176 | 176 |
| Norwegian Bokmål | `nb`, `no` | `numtag/lexicon/nb.json` | long | 178 | 178 |
| Norwegian Nynorsk | every `nn` tag | `numtag/lexicon/nn.json` | long | 157 | 157 |

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

## German "halb" before an hour

German "halb" before an hour names the half hour before that hour, so "um halb drei" is 2:30. The hour is the number, and "halb" is no half of it. The `clock_half` setting holds this rule. A half with no number after it is still a weak half.

```python
>>> from numtag import tag_numbers
>>> [(m.text, m.value) for m in tag_numbers('weck mich um halb drei', 'de')]
[('drei', '3')]
>>> [(m.text, m.value, m.confidence) for m in tag_numbers('halb so viel', 'de')]
[('halb', '0.5', 0.4)]
```

> DWDS, "halb", 1c: "es ist halb zwölf Uhr (= elf Uhr dreißig)", "das Essen auf halb eins ansetzen"

## West Frisian clock hours

After "healwei" (half before), "kertier oer" (quarter past) and "kertier foar" (quarter to), West Frisian names the hour with an inflected form: "fiven" for 5, "tolven" for 12. Such a form reads as a sure number only after "healwei", "oer" or "foar". Elsewhere it may be a plural noun, so it gets the score of a homograph. The form ends the number, so it is never the first part of a compound word: "achtenfjirtich" stays 48.

```python
>>> read('Yn de Greidhoeke begûn men tusken 4 oere en healwei fiven.', 'fy')
[('4', '4'), ('fiven', '5')]
>>> read('Koelstra waard om kertier foar trijen moarns eksekutearre.', 'fy')
[('trijen', '3')]
>>> read('Hy wie achtenfjirtich jier.', 'fy')
[('achtenfjirtich', '48')]
>>> [m.confidence for m in tag_numbers('de achten', 'fy')]
[0.4]
```

> Wikipedia (fy), "Haadstjoertiid" (knowledge/wiki/audits/numtag/issue-fixes/fy-143/sources/Haadstjoertiid.wikitext): "fan healwei sânen oant sân oere jûns"

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
