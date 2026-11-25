# Greek, Arabic, Hebrew, Persian, Kabyle and Maltese

<!-- agent-hint
covers: What numtag reads in Greek, Arabic, Hebrew, Persian, Kabyle and Maltese.
source: numtag/lexicon/{el,ar,he,fa,kab,mt}.json, the same names under tests/gold/*.jsonl
generated: no
verify: sed '/^\x60\x60\x60/d' docs/languages/el-ar-he-fa-kab.md | python -m doctest -o NORMALIZE_WHITESPACE /dev/stdin && PYTHONPATH=tests python -c $'import re,sys\nfrom pathlib import Path\nfrom test_gold import score_file\nrows=re.findall(r"lexicon/([\\w-]+)\\.json\\x60 \\| \\w+ \\| (\\d+) \\| (\\d+) \\|",Path(sys.argv[1]).read_text())\ngot=[(r[0],str(s.rows),str(s.correct)) for r in rows for s in [score_file(Path("tests/gold/"+r[0]+".jsonl"))]]\nbad=[r for r,g in zip(rows,got) if r!=g]\nn=len(re.findall(r"^\\|.*lexicon/",Path(sys.argv[1]).read_text(),re.M))\nprint(len(rows),"rows",n,"table rows",len(bad),"wrong",bad)\nsys.exit(1 if bad or not rows or n!=len(rows) else 0)' docs/languages/el-ar-he-fa-kab.md
see: ../rulings.md, ../adding-a-language.md
-->

numtag reads Greek, Arabic, Hebrew, Persian, Kabyle and Maltese. Arabic and Persian text can use the Arabic-Indic digits, and numtag reads them as digits.

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| Greek | every `el` tag | `numtag/lexicon/el.json` | short | 161 | 161 |
| Arabic | every `ar` tag | `numtag/lexicon/ar.json` | short | 157 | 156 |
| Hebrew | every `he` tag | `numtag/lexicon/he.json` | long | 160 | 157 |
| Persian | every `fa` tag | `numtag/lexicon/fa.json` | short | 153 | 153 |
| Kabyle | every `kab` tag | `numtag/lexicon/kab.json` | short | 163 | 163 |
| Maltese | every `mt` tag | `numtag/lexicon/mt.json` | short | 185 | 177 |

The gold rows are in `tests/gold/<lexicon>.jsonl`. Each row holds a sentence, the numbers in it, and the source of its reading. No native speaker has checked these lexicons or their gold rows.

## Tens and units

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read('٣٤٥ كتابا', 'ar')
[('٣٤٥', '345')]
>>> read('خمسة وعشرون', 'ar')
[('خمسة وعشرون', '25')]
>>> read('نحو 2 مليون و500 ألف نسمة', 'ar')
[('2 مليون و500 ألف', '2500000')]
>>> read('۱۲۳ کتاب', 'fa')
[('۱۲۳', '123')]
>>> read('بیست و پنج', 'fa')
[('بیست و پنج', '25')]
>>> read('עשרים וחמישה', 'he')
[('עשרים וחמישה', '25')]
>>> read('είκοσι πέντε', 'el')
[('είκοσι πέντε', '25')]
>>> read('ħamsa u għoxrin', 'mt')
[('ħamsa u għoxrin', '25')]
```

## Spoken Arabic

The Arabic lexicon also reads the one-word teens, the tens and the hundreds of spoken Egyptian, Levantine, Moroccan and Gulf Arabic. The forms come from the Wiktionary number lists of each lect. A word that is also a Standard Arabic word stays a word: "تنين" is the dragon, "ثمن" the price and "زوج" the spouse. "ميتين" is also the plural of "dead", so it is weak alone.

```python
>>> read('عمره حداشر سنة', 'ar')
[('حداشر', '11')]
>>> read('الف وخمستعش', 'ar')
[('الف وخمستعش', '1015')]
>>> read('ثم ظهر التنين', 'ar')
[]
```

## Examples from the gold rows

```python
>>> read('Πήρα χίλια ευρώ.', 'el')
[('χίλια', '1000')]
>>> read('Η 2η θέση.', 'el')
[('2η', '2')]
>>> read('حضر ألفان شخص.', 'ar')
[('ألفان', '2000')]
>>> read('ربع ساعة.', 'ar')
[('ربع', '0.25')]
>>> read('קיבלתי אלף שקל.', 'he')
[('אלף', '1000')]
>>> read('רבע שעה.', 'he')
[('רבע', '0.25')]
>>> read('هزار تومان.', 'fa')
[('هزار', '1000')]
>>> read('اول شد.', 'fa')
[('اول', '1')]
>>> read('Amḍan-a d 2025.', 'kab')
[('2025', '2025')]
>>> read('D azgen.', 'kab')
[('azgen', '0.5')]
```

## The scale

Each lexicon sets its default scale from these sources. Pass `scale="long"` or `scale="short"` to read the large scale words in the other scale. Read [../number-scale.md](../number-scale.md).

Greek, short scale:

> [...] en.wiktionary page δισεκατομμύριο: "billion , thousand million ( 10 9 )" [...]

Arabic, short scale:

> en.wikipedia "Long and short scale": "Use of the short scale is found in most English -speaking and Arabic -speaking countries" [...]

Hebrew, long scale:

> CLDR RBNF, common/rbnf/he.xml (unicode-org/cldr, cldrVersion 50): "1000000000: מיליארד", "1000000000000: ביליון": the milliard is 10^9 and ביליון is 10^12. he.wikipedia "ביליון" (redirects to מיליארד): "מיליארד (1,000,000,000) הוא מספר טבעי השווה לאלף מיליונים" [...]

Persian, short scale:

> CLDR RBNF, common/rbnf/fa.xml (unicode-org/cldr, cldrVersion 50): "1000000000: << میلیارد" and "1000000000000: << هزار میلیارد": میلیارد is 10^9 and 10^12 is a thousand of them, the short-scale values.

Kabyle, short scale:

> languagesandnumbers.com, "Counting in Kabyle": "amelyun [1 million]", "amelyar [1 billion]": each word has one fixed value.

Maltese, short scale:

> CLDR RBNF mt (unicode-org/cldr release-49, common/rbnf/mt.xml): "1000000000: biljun[ u >>];" names 10^9, the short scale.

Each word and each setting in a lexicon carries the source of its rule. [../adding-a-language.md](../adding-a-language.md) describes the lexicon format.

---
[← English](en.md) · [Home](../index.md) · [Germanic languages →](germanic.md)
