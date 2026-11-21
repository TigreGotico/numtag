# Benchmarks

<!-- agent-hint
covers: Accuracy, memory and time of numtag against ovos-number-parser, with the commands that produce them.
source: benchmarks/bench.py, tests/gold/
generated: no
verify: python -m pytest tests/test_docs.py -q
see: design.md
-->

This page compares numtag with ovos-number-parser on accuracy, memory and time. Both libraries read the same gold corpus, `tests/gold/`, in their own process. The script is `benchmarks/bench.py`, and every number on this page comes from one run of it per library.

## What was measured

| Item | Value |
|---|---|
| numtag | 0.19.1a1 |
| ovos-number-parser | 0.24.62a1 from PyPI, `extract_number_spans(text, lang, ordinals=True)` |
| Corpus | `tests/gold/`: 479 pt-PT rows, 470 pt-BR rows, 444 en rows |
| Python | 3.14.6, the uv interpreter of the laptop |
| Machine | a laptop with an Intel Core i9-11900H, with a load average of about 45 during the runs |

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

Each run writes a JSON report and prints it. The parser version is pinned because later versions of ovos-number-parser read numbers with numtag. A run of such a version gives the numtag scores in both columns.

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

## Time

| Measure | numtag | parser |
|---|---|---|
| Import | 0.42 s | 2.69 s |
| Per gold sentence, median (pt-PT / pt-BR / en) | 1.80 / 1.60 / 1.47 ms | 10.72 / 12.56 / 6.52 ms |
| Per gold sentence, 95th percentile (pt-PT / pt-BR / en) | 22.37 / 10.50 / 7.63 ms | 70.32 / 66.89 / 77.95 ms |
| Short command, median (pt-PT / pt-BR / en) | 2.74 / 2.12 / 2.38 ms | 15.38 / 16.59 / 9.47 ms |
| 2000 words of pt-PT text, best of 3 | 0.760 s | 6.874 s |

The per-sentence times come from 5 passes over each corpus after a first call. The short command is read 200 times. It is "quanto é vinte e três mais quarenta e cinco" in Portuguese and "what is twenty three plus forty five" in English. The long text is the first 2000 words of the pt-PT gold sentences, joined.

Times depend on the machine and its load. Compare the two columns of one run, not numbers from different runs.

---
[← Design](design.md) · [Home](index.md) · [Roadmap →](roadmap.md)
