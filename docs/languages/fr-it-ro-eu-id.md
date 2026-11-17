# French, Italian, Romanian, Basque and Indonesian

numtag reads French, Italian, Romanian, Basque and Indonesian. French has three lexicons: Belgium and Switzerland say "septante" and "nonante", and Switzerland also says "huitante".

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| French (France) | `fr`, `fr-FR` and every other `fr` tag | `numtag/lexicon/fr-FR.json` | long | 190 | 189 |
| French (Belgium) | `fr-BE` | `numtag/lexicon/fr-BE.json` | long | 22 | 22 |
| French (Switzerland) | `fr-CH` | `numtag/lexicon/fr-CH.json` | long | 20 | 20 |
| Italian | every `it` tag | `numtag/lexicon/it.json` | long | 187 | 185 |
| Romanian | every `ro` tag | `numtag/lexicon/ro.json` | long | 157 | 157 |
| Basque | every `eu` tag | `numtag/lexicon/eu.json` | long | 168 | 168 |
| Indonesian | every `id` tag | `numtag/lexicon/id.json` | short | 175 | 174 |

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
>>> read('ventitré', 'it')
[('ventitré', '23')]
>>> read('douăzeci și cinci', 'ro')
[('douăzeci și cinci', '25')]
>>> read('hogeita bost', 'eu')
[('hogeita bost', '25')]
>>> read('dua puluh lima', 'id')
[('dua puluh lima', '25')]
```

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

"erdi" (half), "heren" (third) and "laurden" (quarter) take the article -a. The lexicon lists "erdia", "herena" and "laurdena" as words of their own. numtag reads "erdia" as 0.5, "herena" as 1/3 and "laurdena" as 0.25. Euskaltzaindia rule 203 says that the article joins the word with no space:

> artikulua eta kasu-marka zuzenean lotzen zaizkio zenbatzaileari, beste edozein hitzi bezala, bien artean ezer jarri gabe eta bien artean zuriunerik utzi gabe

The rule does not name these three words. The value comes from the noun, and the Euskaltzaindia dictionary gives the forms: "Bizitzaren erdia.", "Liburuaren laurdena ere ez du irakurri.", "Lehen herena." A noun before "erdia" is no part of the number. In "ordu erdia" (half an hour) the number is "erdia".

A lone article form is a weak number. "erdi" is also "middle" ("Erdiko bideari nagokio."), and "laurden" is also the quarter-final, so these words score 0.4, as "erdi" does. A count of two or more takes the plural -ak in Basque ("Europaren bi herenak."). numtag does not read the plural forms of these nouns.

```python
>>> read('Biribilaren laurdena da.', 'eu')
[('laurdena', '0.25')]
>>> read('lehenengo ordu erdia', 'eu')
[('lehenengo', '1'), ('erdia', '0.5')]
>>> read('kilo bat eta erdia', 'eu')
[('bat eta erdia', '1.5')]
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

Each word and each setting in a lexicon carries the source of its rule. [../adding-a-language.md](../adding-a-language.md) describes the lexicon format.
