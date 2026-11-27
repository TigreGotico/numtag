# French, Italian, Romanian, Basque, Indonesian and Malay

<!-- agent-hint
covers: What numtag reads in French, Italian, Romanian, Basque, Indonesian and Malay.
source: numtag/lexicon/{fr-FR,fr-BE,fr-CH,it,ro,eu,id,ms}.json, the same names under tests/gold/*.jsonl
generated: no
verify: sed '/^\x60\x60\x60/d' docs/languages/fr-it-ro-eu-id.md | python -m doctest -o NORMALIZE_WHITESPACE /dev/stdin && PYTHONPATH=tests python -c $'import re,sys\nfrom pathlib import Path\nfrom test_gold import score_file\nrows=re.findall(r"lexicon/([\\w-]+)\\.json\\x60 \\| \\w+ \\| (\\d+) \\| (\\d+) \\|",Path(sys.argv[1]).read_text())\ngot=[(r[0],str(s.rows),str(s.correct)) for r in rows for s in [score_file(Path("tests/gold/"+r[0]+".jsonl"))]]\nbad=[r for r,g in zip(rows,got) if r!=g]\nn=len(re.findall(r"^\\|.*lexicon/",Path(sys.argv[1]).read_text(),re.M))\nprint(len(rows),"rows",n,"table rows",len(bad),"wrong",bad)\nsys.exit(1 if bad or not rows or n!=len(rows) else 0)' docs/languages/fr-it-ro-eu-id.md
see: ../rulings.md, ../adding-a-language.md
-->

numtag reads French, Italian, Romanian, Basque, Indonesian and Malay. French has three lexicons. They read the same words: every French tag reads "septante", "huitante", "octante" and "nonante" ([rulings](../rulings.md#regional-words-septante-huitante-octante-nonante)). They differ in how they write numbers, and Switzerland groups digits with an apostrophe. Belgium and Switzerland write "septante" and "nonante", and Switzerland also writes "huitante".

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| French (France) | `fr`, `fr-FR` and every other `fr` tag | `numtag/lexicon/fr-FR.json` | long | 205 | 203 |
| French (Belgium) | `fr-BE` | `numtag/lexicon/fr-BE.json` | long | 22 | 22 |
| French (Switzerland) | `fr-CH` | `numtag/lexicon/fr-CH.json` | long | 20 | 20 |
| Italian | every `it` tag | `numtag/lexicon/it.json` | long | 194 | 191 |
| Romanian | every `ro` tag | `numtag/lexicon/ro.json` | long | 157 | 157 |
| Basque | every `eu` tag | `numtag/lexicon/eu.json` | long | 168 | 168 |
| Indonesian | every `id` tag | `numtag/lexicon/id.json` | short | 175 | 174 |
| Malay | every `ms` tag | `numtag/lexicon/ms.json` | short | 162 | 161 |

The gold rows are in `tests/gold/<lexicon>.jsonl`. Each row holds a sentence, the numbers in it, and the source of its reading. No native speaker has checked these lexicons or their gold rows.

## Tens and units

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read('quatre-vingt-dix-sept', 'fr')
[('quatre-vingt-dix-sept', '97')]
>>> read('nonante-sept', 'fr-BE')
[('nonante-sept', '97')]
>>> read('huitante', 'fr-CH')
[('huitante', '80')]
>>> read('septante-cinq', 'fr-CA')
[('septante-cinq', '75')]
>>> read('ventitré', 'it')
[('ventitré', '23')]
>>> read('douăzeci și cinci', 'ro')
[('douăzeci și cinci', '25')]
>>> read('hogeita bost', 'eu')
[('hogeita bost', '25')]
>>> read('dua puluh lima', 'id')
[('dua puluh lima', '25')]
>>> read('lapan puluh lima', 'ms')
[('lapan puluh lima', '85')]
```

## Italian ordinals from primo to nono

A longer Italian ordinal is one word that ends in "-esimo" ("ventiduesimo", "centotreesimo"). "primo" to "nono" never end a longer ordinal. So a cardinal and one of these words are two numbers: "dieci secondi" is 10 and the time unit "secondi", never 12. "decimo" can end one ("centodecimo"), so "cento decimo" is 110.

```python
>>> from numtag import tag_numbers
>>> [(m.text, m.value, m.kind.value) for m in tag_numbers('tra dieci secondi', 'it')]
[('dieci', '10', 'cardinal'), ('secondi', '2', 'ordinal')]
>>> [(m.text, m.value, m.kind.value) for m in tag_numbers('cento decimo', 'it')]
[('cento decimo', '110', 'ordinal')]
```

> CLDR 48 RBNF it: "2: secondo;", "11: undicesimo;". Treccani, "Ordinali": "I primi dieci ordinali presentano una forma propria derivata dal latino: primo, secondo, terzo, quarto, quinto, sesto, settimo, ottavo, nono, decimo."

## Examples from the gold rows

```python
>>> read('Elle a lu mille vingt pages.', 'fr-FR')
[('mille vingt', '1020')]
>>> read('Rendez-vous le 1er mai.', 'fr-FR')
[('1er', '1')]
>>> read('Il y a septante mille personnes dans la salle.', 'fr-BE')
[('septante mille', '70000')]
>>> read("C'est le nonantième anniversaire.", 'fr-BE')
[('nonantième', '90')]
>>> read("Le stade compte 12'500 places.", 'fr-CH')
[("12'500", '12500')]
>>> read("C'est le nonantième anniversaire.", 'fr-CH')
[('nonantième', '90')]
>>> read('Ha letto tremila pagine.', 'it')
[('tremila', '3000')]
>>> read('Abita al primo piano.', 'it')
[('primo', '1')]
>>> read('Cartea costă o mie unu lei.', 'ro')
[('o mie unu', '1001')]
>>> read('Locul al 2-lea.', 'ro')
[('2-lea', '2')]
>>> read('Herriak mila biztanle ditu.', 'eu')
[('mila', '1000')]
>>> read('Prezioa 3,5 eurokoa da.', 'eu')
[('3,5', '3.5')]
>>> read('Seigarrena hartu du.', 'eu')
[('Seigarrena', '6')]
>>> read('Harga tiket seribu rupiah.', 'id')
[('seribu', '1000')]
>>> read('Panjangnya 12,5 m.', 'id')
[('12,5', '12.5')]
```

## Minus words that are no sign

French "moins" after an hour counts the minutes before that hour. TLFi, "moins", gives this use: "Dans le décompte de l'heure, précédant le nom de nombre correspondant au nombre des minutes manquant". The hour is "heure", the symbol "h", "midi" or "minuit". French "à tout le moins" and Italian "quanto meno" mean "at least", so the minus word in them is no sign either.

```python
>>> read('Il est midi moins dix.', 'fr')
[('dix', '10')]
>>> read('Il est 9h moins 10.', 'fr')
[('9', '9'), ('10', '10')]
>>> read('Il faut à tout le moins trois jours.', 'fr')
[('trois', '3')]
>>> read('Ci vogliono quanto meno tre ore.', 'it')
[('tre', '3')]
>>> read('Il fait moins trois degrés.', 'fr')
[('moins trois', '-3')]
```

A point right before the first digit marks decimals, because a group mark stands only between digits. So "-.5" is -0.5 in French, Italian and Romanian, as ",5" is 0.5.

```python
>>> read('-.5', 'fr'), read('-.5', 'it'), read('-.5', 'ro')
([('-.5', '-0.5')], [('-.5', '-0.5')], [('-.5', '-0.5')])
```

## Basque ordinals with the article

A Basque ordinal takes the article -a with no space, as any other word does. numtag reads "lehena" as 1 and "hirugarrena" as 3. Euskaltzaindia rule 203 gives the form as a pronoun:

> Izenordain ere izan daitezke: seigarrena hartu du.

```python
>>> read('Lasterketan hirugarrena izan zen.', 'eu')
[('hirugarrena', '3')]
>>> read('Maiatzaren Lehena kalean bizi da.', 'eu')
[('Lehena', '1')]
```

## Basque fractions with the article

"erdi" (half), "heren" (third) and "laurden" (quarter) take the article -a. The lexicon lists "erdia", "herena" and "laurdena" as words of their own. numtag reads them as 0.5, 1/3 and 0.25. Euskaltzaindia rule 203 says that the article joins the word with no space:

> artikulua eta kasu-marka zuzenean lotzen zaizkio zenbatzaileari, beste edozein hitzi bezala, bien artean ezer jarri gabe eta bien artean zuriunerik utzi gabe

The rule does not name these three words. The value comes from the noun, and the Euskaltzaindia dictionary gives the forms: "Bizitzaren erdia.", "Liburuaren laurdena ere ez du irakurri.", "Lehen herena." A noun before "erdia" is no part of the number. In "ordu erdia" (half an hour) the number is "erdia".

A lone article form is a weak number. "erdi" is also "middle" ("Erdiko bideari nagokio."), and "laurden" is also the quarter-final, so these words score 0.4, as "erdi" does. The bare nouns "laurden" and "heren" with no count also read one part at 0.4. So "ordu laurden" reads "laurden" as 0.25, as "ordu erdi" reads "erdi" as 0.5. A clock phrase such as "hirurak eta laurden" (Euskaltzaindia rule 35) reads no number, because the hour word before "eta" is no number word. A count of two or more takes the plural -ak in Basque ("Europaren bi herenak."). numtag does not read the plural forms of these nouns.

```python
>>> read('Biribilaren laurdena da.', 'eu')
[('laurdena', '0.25')]
>>> read('lehenengo ordu erdia', 'eu')
[('lehenengo', '1'), ('erdia', '0.5')]
>>> read('kilo bat eta erdia', 'eu')
[('bat eta erdia', '1.5')]
>>> read('ordu laurden', 'eu')
[('laurden', '0.25')]
>>> read('hirurak eta laurden', 'eu')
[]
```

## The scale

Each lexicon sets its default scale from these sources. Pass `scale="long"` or `scale="short"` to read the large scale words in the other scale. Read [../number-scale.md](../number-scale.md).

French (France), French (Belgium) and French (Switzerland), long scale:

> [...] TLFi, BILLION: "B. — Un million de millions (10^12)." [...]

Italian, long scale:

> [...] Treccani, "bilione": "corrispondente a un milione di milioni, cioè a mille miliardi".

Romanian, long scale:

> [...] DEX '09, "bilion": "Număr egal cu o mie de miliarde sau (în unele țări) cu un miliard." [...]

Basque, long scale:

> Euskaltzaindia, 203. araua, EBO (VI), "Zenbakizko adierazpenak": "Euskaraz, eskala luzea erabiltzen da, gaztelaniaz eta frantsesez bezala."

Indonesian, short scale:

> KBBI VI Daring, "triliun": "12 nol (000.000.000.000) [...] (di Amerika Serikat dan Prancis, digunakan juga di Indonesia)". "miliar" is 10^9 and "triliun" 10^12 in Indonesia, so the scale changes no value.

Malay, short scale:

> Kamus Dewan Edisi Keempat, "bilion": "1. (di Britain) satu juta juta, ditulis sbg 1 000 000 000 000 atau 1012; 2. (di AS) satu ribu juta, ditulis sbg 1 000 000 000 atau 109"; [...]

Each word and each setting in a lexicon carries the source of its rule. [../adding-a-language.md](../adding-a-language.md) describes the lexicon format.

---
[← Slavic languages](slavic.md) · [Home](../index.md) · [Iberian languages and Occitan →](ibero.md)
