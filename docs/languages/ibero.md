# Iberian languages and Occitan

numtag reads Spanish, Galician, Catalan, Asturian, Aragonese, Occitan and Mirandese. All of them count in the long scale: "billón" and its cognates are 10^12.

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| Spanish | every `es` tag | `numtag/lexicon/es.json` | long | 235 | 232 |
| Galician | every `gl` tag | `numtag/lexicon/gl.json` | long | 185 | 184 |
| Catalan | every `ca` tag | `numtag/lexicon/ca.json` | long | 214 | 211 |
| Asturian | every `ast` tag | `numtag/lexicon/ast.json` | long | 176 | 175 |
| Aragonese | every `an` tag | `numtag/lexicon/an.json` | long | 153 | 153 |
| Occitan | every `oc` tag | `numtag/lexicon/oc.json` | long | 173 | 173 |
| Mirandese | every `mwl` tag | `numtag/lexicon/mwl.json` | long | 162 | 162 |

The gold rows are in `tests/gold/<lexicon>.jsonl`. Each row holds a sentence, the numbers in it, and the source of its reading. No native speaker has checked these lexicons or their gold rows.

## Tens and units

```python
>>> from numtag import tag_numbers
>>> def read(text, lang):
...     return [(m.text, m.value) for m in tag_numbers(text, lang)]
>>> read('veintitrés', 'es')
[('veintitrés', '23')]
>>> read('vinte e tres', 'gl')
[('vinte e tres', '23')]
>>> read('vint-i-tres', 'ca')
[('vint-i-tres', '23')]
>>> read('vint e tres', 'oc')
[('vint e tres', '23')]
```

## The Spanish joiner "y"

In Spanish, "y" joins a ten and a unit. Between "mil" and a one it also makes one number, as in the title "Las mil y una noches". Older texts also write "y" between the thousands and the hundreds, as in the inscription "mil y quinientos y cinco" (1505). After "entre", the "y" joins the two limits of a range. Other uses of "y" after "mil" stay two numbers, and no "y" joins a group after "millón".

```python
>>> read('Las mil y una noches', 'es')
[('mil y una', '1001')]
>>> read('dentro de mil y un días', 'es')
[('mil y un', '1001')]
>>> read('mil y quinientos y cinco', 'es')
[('mil y quinientos y cinco', '1505')]
>>> read('entre mil y quinientos', 'es')
[('mil', '1000'), ('quinientos', '500')]
>>> read('mil y veinte', 'es')
[('mil', '1000'), ('veinte', '20')]
>>> read('un millón y dos', 'es')
[('un millón', '1000000'), ('dos', '2')]
>>> read('uno y dos', 'es')
[('uno', '1'), ('dos', '2')]
```

The old spelling "diez y seis" is 16, and so are "diez y siete" to "diez y nueve" for 17 to 19. "diez y uno" to "diez y cinco" are two numbers.

```python
>>> read('diez y seis', 'es')
[('diez y seis', '16')]
>>> read('diez y cinco', 'es')
[('diez', '10'), ('cinco', '5')]
```

> DPD "cardinales" §2: "Las grafías pluriverbales" "diez y seis" "son anticuadas y deben evitarse"

Alone, "ciento" is the noun for a hundred, so it gets the homograph score. "un ciento" and "ciento por ciento" are 100. After a number, "por ciento" is the percent sign, and with no number before it ("tanto por ciento") it holds no number. "cien por cien" is also 100, because "por cien" is the percent sign after "cien". After any other number, "por cien" keeps its hundred, because the DPD accepts that form only for the whole: "el noventa por cien" is 90 and 100.

```python
>>> [(m.text, m.value, m.confidence) for m in tag_numbers('Éramos ciento y la madre.', 'es')]
[('ciento', '100', 0.4)]
>>> read('un ciento de platos', 'es')
[('un ciento', '100')]
>>> read('el ciento por ciento', 'es')
[('ciento', '100')]
>>> read('cinco por ciento', 'es')
[('cinco', '5')]
>>> read('el tanto por ciento', 'es')
[]
>>> read('Al cien por cien.', 'es')
[('cien', '100')]
>>> read('el noventa por cien', 'es')
[('noventa', '90'), ('cien', '100')]
```

> DPD "ciento" §2: "Quien hace un cesto hace ciento"

> DPD "ciento" §3: "cuando el porcentaje expresa totalidad son igualmente válidas las expresiones ciento por ciento (preferida en América), cien por ciento y cien por cien (preferida en España)"

## Examples from the gold rows

```python
>>> read('El tren lleva mil pasajeros.', 'es')
[('mil', '1000')]
>>> read('Costó 99,95 euros.', 'es')
[('99,95', '99.95')]
>>> read('O tren leva mil pasaxeiros.', 'gl')
[('mil', '1000')]
>>> read('É a 2.ª vez.', 'gl')
[('2.ª', '2')]
>>> read('Hi havia tres mil persones.', 'ca')
[('tres mil', '3000')]
>>> read('Va quedar 3r.', 'ca')
[('3r', '3')]
>>> read('Hai un millón llobos.', 'ast')
[('un millón', '1000000')]
>>> read('Ye la 2.ª vegada.', 'ast')
[('2.ª', '2')]
>>> read('Contemos dica mil.', 'an')
[('mil', '1000')]
>>> read('Costó 25,95 €.', 'an')
[('25,95', '25.95')]
>>> read('Cent mila personas.', 'oc')
[('Cent mila', '100000')]
>>> read('Es lo premièr.', 'oc')
[('premièr', '1')]
>>> read('Ganhou un bilion.', 'mwl')
[('un bilion', '1000000000000')]
>>> read('Chegou nono.', 'mwl')
[('nono', '9')]
```

## Catalan words with a second meaning

Catalan "nou" is nine and also "new", and "u" is one and also the name of a letter. Alone, each gets the low score 0.4 for a word with a second meaning. Inside a longer number the reading is clear, so "vint-i-nou" and "cent u" keep the full score.

```python
>>> from numtag import tag_numbers
>>> [(m.text, m.value, m.confidence) for m in tag_numbers('Crea un esdeveniment nou.', 'ca')]
[('un', '1', 0.3), ('nou', '9', 0.4)]
>>> [(m.text, m.value, m.confidence) for m in tag_numbers('Té vint-i-nou anys.', 'ca')]
[('vint-i-nou', '29', 1.0)]
```

> DIEC2 "nou" 2 1: "Vuit més un. Aviat farà nou anys."; DIEC2 "nou" 3 1 1: "Originat o ocorregut fa poc, aparegut de poc, que apareix per primera vegada. Una moda nova. Un règim nou."

## The scale

Each lexicon sets its default scale from these sources. Pass `scale="long"` or `scale="short"` to read the large scale words in the other scale. Read [../number-scale.md](../number-scale.md).

Spanish, long scale:

> DPD "billón": "'un millón de millones (10 12)' [...] no se recomienda su empleo en español con el sentido de 'mil millones'" [...]

Galician, long scale:

> Dicionario da Real Academia Galega, "billón": "Un millón de millóns."

Catalan, long scale:

> en.wiktionary (Catalan; refs IEC DIEC2, GDLC): "milió: million 10^6", "miliard: billion 10^9", "bilió: trillion 10^12", "trilió (10^18)" [...]

Asturian, long scale:

> en.wiktionary, Asturian "millón": "million [...] 1,000,000" [...] "billón": "trillion [...] 10^12"

Aragonese, long scale:

> [...] "Lo numero mil y los substantivos millón, billón, trillón" follow the Spanish and Catalan long scale, as ovos-number-parser numbers_an.py DEFAULT_SCALE (a lead).

Occitan, long scale:

> ovos-number-parser numbers_oc.py, a lead that cites Lo Congrès dicod'Òc: [...] "bilion" 10^12 in the long scale [...] "miliard" names 10^9, so "bilion" is 10^12.

Mirandese, long scale:

> ovos-number-parser numbers_mwl.py (a lead): DEFAULT_SCALE=Scale.LONG, DECIMAL_MARKER=["bírgula", "ponto", "birgula", ...], NEGATIVE_SIGN=["menos"], fractions "meio", "tércio", "quarto", "meia" ("ũa i meia -> 1.5") [...]

Each word and each setting in a lexicon carries the source of its rule. [../adding-a-language.md](../adding-a-language.md) describes the lexicon format.
