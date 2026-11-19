# numtag

numtag finds every number in a text. For each number it gives the exact words, their character offsets, an exact value, the kind of number and how it is written. It reads number words ("duas dúzias"), digits ("1.234,5") and both together ("2 milhões").

```python
from numtag import tag_numbers

for m in tag_numbers("Comprou duas dúzias de ovos e ganhou um milhão de euros.", "pt-PT"):
    print(m.char_span, repr(m.text), m.value, m.kind.value)
```

```text
(8, 19) 'duas dúzias' 24 cardinal
(37, 46) 'um milhão' 1000000 cardinal
```

## Install

numtag needs Python 3.11 or later and has no dependencies.

```bash
uv pip install --prerelease=allow numtag
```

To work on the library, install it from a clone with its test extra and run the tests:

```bash
uv pip install -e ".[test]"
pytest tests
```

## Quickstart

`tag_numbers(text, lang)` returns a list of `NumberMention` objects in reading order. The mentions never overlap.

```python
>>> from numtag import tag_numbers
>>> mention = tag_numbers("The tower is one hundred and twenty-five point five metres tall.", "en")[0]
>>> mention.text, mention.char_span, mention.value
('one hundred and twenty-five point five', (13, 51), '125.5')
>>> mention.kind, mention.form
(<Kind.DECIMAL: 'decimal'>, <Form.WORDS: 'words'>)
```

The span slices the original text, so `text[start:end]` is always `mention.text`. Use the span to replace or mark the number in place.

## Values

A value is a canonical digit string, never an `int` or a `float`. It has one of three forms.

| Form | Examples |
|---|---|
| whole number | `"24"`, `"-42"`, `"1000000"` |
| decimal | `"125.5"`, `"0.75"` |
| fraction in lowest terms | `"1/3"`, `"7/3"` |

numtag computes each value with string arithmetic on digits, so a value has no length limit and no rounding error. Convert a value when you need a number. `int()` reads a whole number, `decimal.Decimal()` reads a whole number or a decimal, and `fractions.Fraction()` reads all three forms.

```python
>>> from fractions import Fraction
>>> Fraction(tag_numbers("dois e um terço", "pt-PT")[0].value)
Fraction(7, 3)
```

Read [docs/values.md](docs/values.md) for the full contract.

## Languages

| `lang` | Lexicon | Default scale |
|---|---|---|
| `pt-BR` | Brazilian Portuguese | short: "bilhão" is 10^9 |
| every other `pt` tag (`pt`, `pt-PT`, `pt-AO`) | European Portuguese | long: "bilião" is 10^12 |
| every `en` tag (`en`, `en-US`, `en-GB`) | English | short: "billion" is 10^9 |
| `el`, `ar`, `he`, `fa`, `kab` | Greek, Arabic, Hebrew, Persian, Kabyle | per lexicon, in [el-ar-he-fa-kab.md](docs/languages/el-ar-he-fa-kab.md) |
| `de`, `nl`, `fy`, `da`, `sv`, `nb` (and `no`), `nn` | German, Dutch, West Frisian, Danish, Swedish, Norwegian | per lexicon, in [germanic.md](docs/languages/germanic.md) |
| `fi`, `et`, `hu`, `tr`, `az` | Finnish, Estonian, Hungarian, Turkish, Azerbaijani | per lexicon, in [uralic-turkic.md](docs/languages/uralic-turkic.md) |
| `ru`, `uk`, `bg`, `pl`, `cs`, `sk`, `sl`, `hr` | Russian, Ukrainian, Bulgarian, Polish, Czech, Slovak, Slovene, Croatian | per lexicon, in [slavic.md](docs/languages/slavic.md) |
| `sr` | Serbian, in the Latin and the Cyrillic script | long: "bilion" is 10^12, in [slavic.md](docs/languages/slavic.md) |
| `fr` (`fr-BE` and `fr-CH` have their own lexicons), `it`, `ro`, `eu`, `id` | French, Italian, Romanian, Basque, Indonesian | per lexicon, in [fr-it-ro-eu-id.md](docs/languages/fr-it-ro-eu-id.md) |
| `es`, `gl`, `ca`, `ast`, `an`, `oc`, `mwl` | Spanish, Galician, Catalan, Asturian, Aragonese, Occitan, Mirandese | per lexicon, in [ibero.md](docs/languages/ibero.md) |

Each language page gives the default scale of each lexicon. Pass `scale="long"` or `scale="short"` to read the large scale words in the other scale. Another language tag raises `UnsupportedLanguageError`, a subclass of `ValueError`.

Each language is one JSON file in `numtag/lexicon/`. Each word and each setting in the file carries the source of its rule.

## Documentation

| Guide | Content |
|---|---|
| [docs/index.md](docs/index.md) | The map of the documentation |
| [docs/getting-started.md](docs/getting-started.md) | First calls and common tasks |
| [docs/api.md](docs/api.md) | Every public name |
| [docs/values.md](docs/values.md) | The value strings and how to convert them |
| [docs/number-scale.md](docs/number-scale.md) | Long and short scale |
| [docs/confidence-and-homographs.md](docs/confidence-and-homographs.md) | Articles, words with two meanings, low scores |
| [docs/rulings.md](docs/rulings.md) | The reading rules, each with its source |
| [docs/languages/](docs/languages/) | What each language reads |
| [docs/adding-a-language.md](docs/adding-a-language.md) | The lexicon format and the gates for a new language |
| [docs/design.md](docs/design.md) | How the tagger works inside |
| [docs/benchmarks.md](docs/benchmarks.md) | Accuracy, memory and time against ovos-number-parser |
| [docs/roadmap.md](docs/roadmap.md) | Planned features |

## License

Apache-2.0.
