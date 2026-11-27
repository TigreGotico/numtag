# numtag

<!-- agent-hint
covers: What numtag does, how to install it, a first example and the way into docs/.
source: numtag/__init__.py:__all__, numtag/tagger.py:tag_numbers, numtag/lexicon/*.json
generated: no
verify: diff <(awk '/^\x60\x60\x60python/{n++;f=(n==1);next} /^\x60\x60\x60/{f=0} f' README.md | python -) <(awk '/^\x60\x60\x60text/{f=1;next} /^\x60\x60\x60/{f=0} f' README.md)
see: docs/index.md, docs/getting-started.md, AGENTS.md
-->

numtag finds every number in a text. For each number it gives the exact words, their character offsets, an exact value, the kind of number and how it is written. It reads number words ("duas dúzias"), digits ("1.234,5") and both together ("2 milhões"), in more than 50 lexicons.

Try it in the browser: [TigreGotico/numtag Space](https://huggingface.co/spaces/TigreGotico/numtag).

## Install

numtag needs Python 3.11 or later.

```bash
uv pip install --prerelease=allow numtag
```

## Quickstart

```python
from numtag import tag_numbers

for m in tag_numbers("Comprou duas dúzias de ovos e ganhou um milhão de euros.", "pt-PT"):
    print(m.char_span, repr(m.text), m.value, m.kind.value)
```

```text
(8, 19) 'duas dúzias' 24 cardinal
(37, 46) 'um milhão' 1000000 cardinal
```

A value is a canonical digit string such as `"24"`, `"2.5"` or `"1/3"`, never an `int` or a `float`. The span slices the original text.

## Documentation

| Page | What you get there |
|---|---|
| [docs/index.md](docs/index.md) | The map of the documentation |
| [docs/getting-started.md](docs/getting-started.md) | A walk-through of the first calls and the common tasks |
| [docs/api.md](docs/api.md) | Every public name |
| [docs/values.md](docs/values.md) | The value strings and how to convert them |
| [docs/number-scale.md](docs/number-scale.md) | Long and short scale |
| [docs/confidence-and-homographs.md](docs/confidence-and-homographs.md) | Articles, words with two meanings, low scores |
| [docs/rulings.md](docs/rulings.md) | The reading rules, each with its source |
| [docs/languages/index.md](docs/languages/index.md) | The support table and the score of each language |
| [docs/adding-a-language.md](docs/adding-a-language.md) | How to add a language: the source rule, gold rows and test gates |
| [docs/design.md](docs/design.md) | How the tagger works inside |
| [docs/benchmarks.md](docs/benchmarks.md) | Accuracy against ovos-number-parser |
| [docs/roadmap.md](docs/roadmap.md) | Planned features |

Contributors and agents find the setup and test commands in [AGENTS.md](AGENTS.md).

## License

Apache-2.0. The `writer` blocks of the lexicons hold rules from the Unicode CLDR rule-based number formats (CLDR 44), copyright Unicode, Inc., under the Unicode License v3. The text is in [LICENSE-CLDR](LICENSE-CLDR).
