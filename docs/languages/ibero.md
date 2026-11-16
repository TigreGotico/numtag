# Iberian languages and Occitan

numtag reads Spanish, Galician, Catalan, Asturian, Aragonese, Occitan and Mirandese. All of them count in the long scale: "billón" and its cognates are 10^12.

| Language | Tags | Lexicon | Default scale | Gold rows | Rows that pass |
|---|---|---|---|---|---|
| Spanish | every `es` tag | `numtag/lexicon/es.json` | long | 221 | 218 |
| Galician | every `gl` tag | `numtag/lexicon/gl.json` | long | 182 | 181 |
| Catalan | every `ca` tag | `numtag/lexicon/ca.json` | long | 211 | 208 |
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
