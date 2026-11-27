# numtag: agent guide

<!-- agent-hint
covers: The repository map, the setup, the hard rules and the checks to run before a push.
source: numtag/, tests/, tests/gold_floor.json, docs/index.md, .github/workflows/build-tests.yml
generated: no
verify: for p in $(grep -P '^\| \x60' AGENTS.md | cut -d'|' -f2 | grep -oP '\x60[^\x60]*\x60' | tr -d '\140' | sed 's#<lang>#en#'); do ls -d $p >/dev/null || exit 1; done
see: docs/index.md, docs/adding-a-language.md, docs/rulings.md
-->

Read this file before you change anything in the repository. It gives the map, the setup, the hard rules and the checks to run before a push. The documentation index is [docs/index.md](docs/index.md).

numtag finds every number in a text and returns one mention per number. A mention holds the exact words, the character span, an exact value as a digit string, the kind and the form. The tagger reads numbers, `spell` writes a value as words from the `writer` block of a lexicon, and the package has one runtime dependency, linguatag, which reads language tags.

## Repository map

| Path | Holds |
|---|---|
| `numtag/tagger.py` | `tag_numbers`, `revision`, the confidence constants and the choice of lexicon (`lexicon_name`) |
| `numtag/tokenize.py`, `numtag/grammar.py`, `numtag/roman.py` | Tokens, the number grammar and Roman numerals |
| `numtag/digits.py` | Arithmetic on digit strings. No value passes through `int` or `float` |
| `numtag/mention.py` | `NumberMention`, `Kind`, `Form`, `Scale`, `Reason`, `is_canonical_value` |
| `numtag/vague.py` | `tag_vague_quantities` |
| `numtag/lexicon/*.json` | One lexicon per language. This is the language data |
| `numtag/writer.py` | `spell`, `Spelling`, `SpokenForm` and the interpreter of the `writer` block. It names no language |
| `numtag/lexicon.schema.json` | The JSON Schema of a lexicon. [docs/lexicon-format.md](docs/lexicon-format.md) specifies the format |
| `tests/gold/<lang>.jsonl` | Gold rows of real sentences, one file per lexicon |
| `tests/gold_floor.json` | The lowest accepted gold score of each language |
| `tests/golden/readings.jsonl.gz` | Every field of every mention of every gold and consumer text, at both scales. `python tests/golden.py` writes it |
| `tests/golden/onp-writers.jsonl.gz` | What the ovos-number-parser writers said, row by row: 488,631 calls over 43 tags. `tests/golden_writers.py` runs the rows of each lexicon with a `writer` block through `numtag.spell`. `tests/golden/onp-writers-allow/<lang>.json` lists the rows where the stored words are a known defect, each with a source |
| `tests/golden/revisions/<lang>.txt` | The revision of a lexicon that has no `writer` block. It never changes |
| `tests/consumers/` | The readings that each consumer of numtag depends on |
| `benchmarks/bench.py` | The accuracy, memory and time script |
| `docs/` | The documentation. `docs/index.md` sets the reading order |

## Setup and tests

```bash
unset VIRTUAL_ENV
uv venv .venv
uv pip install -p .venv/bin/python --prerelease=allow -e ".[test]"
.venv/bin/python -m pytest tests
```

The full suite takes several minutes. `tests/test_docs.py` runs every example in `README.md` and `docs/`, so run it after any docs edit:

```bash
.venv/bin/python -m pytest tests/test_docs.py -q
```

## Hard rules

1. Language facts are data. A lexicon carries each word and each setting with a `source` ([adding-a-language.md](docs/adding-a-language.md)).
2. No module, function or branch is keyed on a language, a script or a language family. A language that needs new behaviour extends the lexicon format. The same PR bumps the format version and changes the page that specifies the format ([lexicon-format.md](docs/lexicon-format.md)).
3. Every quote in a block quote of `docs/` comes from a `source` field of a lexicon or a gold file. `tests/test_docs.py` checks it. Keep every quote and citation as the source writes it.
4. A reading rule lives in [docs/rulings.md](docs/rulings.md) with its example and its source.
5. A gold value comes from hand arithmetic or a quoted source, never from a run of numtag or another parser ([adding-a-language.md](docs/adding-a-language.md#gold-rows)).
6. A value is a canonical digit string ([values.md](docs/values.md)).
7. A language that you add has a floor in `tests/gold_floor.json`, at least 150 gold rows, and grammar tests that fail before the change and pass after it.
8. Every example in the docs runs as a test and shows the output it gives.
9. `numtag/version.py` is never edited by hand. The release workflow bumps it from the conventional-commit prefix.

## Before you push

1. Run the full test suite.
2. If you added, removed, renamed or moved a page of `docs/`, list it in `docs/index.md` and fix the navigation footers of its neighbours.
3. If a change moves a reading on purpose, write the golden file again with `python tests/golden.py` and name the changed rows in the commit.
