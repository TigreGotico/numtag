# Benchmarks

<!-- agent-hint
covers: Accuracy and memory of numtag against ovos-number-parser, with the commands that produce them.
source: benchmarks/bench.py, tests/gold/
generated: no
verify: diff <(python -c "import json,subprocess as s; n,p=[json.loads(s.check_output([c,'benchmarks/bench.py',k,'tests/gold','/dev/null'])) for c,k in (('.venv/bin/python','numtag'),('.venv-parser/bin/python','parser'))]; [print('| %s | %d | %d | %d | %d | %d | %d |'%(l,n['accuracy'][l]['rows'],n['accuracy'][l]['rows_right'],p['accuracy'][l]['rows_right'],n['accuracy'][l]['gold_mentions'],n['accuracy'][l]['mentions_found'],p['accuracy'][l]['mentions_found'])) for l in ('pt-PT','pt-BR','en')]") <(grep -E '^\| (pt-PT|pt-BR|en) \| [0-9]' docs/benchmarks.md)
see: design.md
-->

This page compares numtag with ovos-number-parser on accuracy and memory. Both libraries read the same gold corpus, `tests/gold/`, in their own process. The script is `benchmarks/bench.py`, and every number on this page comes from one run of it per library.

## What was measured

| Item | Value |
|---|---|
| numtag | 0.19.1a1 |
| ovos-number-parser | 0.24.62a1 from PyPI, `extract_number_spans(text, lang, ordinals=True)` |
| Corpus | `tests/gold/`: 479 pt-PT rows, 470 pt-BR rows, 444 en rows |
| Python | 3.14.6, the uv interpreter of the laptop |
| Machine | a laptop with an Intel Core i9-11900H |

The parser runs with ordinals on, because that mode finds more of the gold mentions.

## Commands

Each library gets its own virtual environment, so that the memory numbers belong to one library.

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e .
uv venv .venv-parser
uv pip install --python .venv-parser/bin/python --prerelease=allow "ovos-number-parser==0.24.62a1"
.venv/bin/python benchmarks/bench.py numtag tests/gold numtag.json
.venv-parser/bin/python benchmarks/bench.py parser tests/gold parser.json
```

Each run writes a JSON report and prints it. The parser version is pinned because ovos-number-parser reads numbers with numtag from 0.25.0a1 (it requires `numtag>=0.12.12a1`). A run of such a version gives the numtag scores in both columns.

## Accuracy

A row is right when the set of (start, end, value) that the library gives equals the gold set. A gold mention marked `low_confidence` counts when the library reports it at all. A mention is found when the library gives the same span and value.

| Language | Rows | numtag rows right | parser rows right | Gold mentions | numtag found | parser found |
|---|---|---|---|---|---|---|
| pt-PT | 479 | 473 | 388 | 530 | 528 | 414 |
| pt-BR | 470 | 464 | 390 | 513 | 511 | 410 |
| en | 444 | 442 | 358 | 486 | 485 | 400 |

The rows that numtag misses are in [languages/pt.md](languages/pt.md) and [languages/en.md](languages/en.md). The gold values come from sources and hand arithmetic, not from either library.

## Memory

| Measure | numtag | parser |
|---|---|---|
| Resident memory of the bare interpreter | 18.1 MiB | 18.2 MiB |
| Resident memory after the import | 22.6 MiB | 32.9 MiB |
| Resident memory after the whole run | 27.8 MiB | 33.6 MiB |
| Python allocations in the first call per language (tracemalloc peak) | 2933 KiB | 64 KiB |

numtag loads the JSON lexicon of a language on the first call for that language. The parser builds its tables when it is imported, and its import also loads its dependencies.

---
[← Design](design.md) · [Home](index.md) · [Roadmap →](roadmap.md)
