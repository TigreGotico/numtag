# Benchmarks

This page compares numtag with ovos-number-parser on accuracy, memory and time. Both libraries read the same gold corpus, `tests/gold/`, in their own process. The script is `benchmarks/bench.py`, and every number on this page comes from one run of it per library.

## What was measured

| Item | Value |
|---|---|
| numtag | commit ef3a883, the pt-PT, pt-BR and en engine |
| ovos-number-parser | 0.24.62a1 from PyPI, `extract_number_spans(text, lang, ordinals=True)` |
| Corpus | `tests/gold/`: 458 pt-PT rows, 456 pt-BR rows, 420 en rows |
| Python | 3.14.6, the uv interpreter of the laptop (the JSON reports do not record it) |
| Machine | a laptop with an Intel Core i9-11900H |

The parser runs with ordinals on, because that mode finds more of the gold mentions.

## Commands

Each library gets its own virtual environment, so that the memory numbers belong to one library.

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e .
uv venv .venv-parser
uv pip install --python .venv-parser/bin/python --prerelease=allow ovos-number-parser
.venv/bin/python benchmarks/bench.py numtag tests/gold numtag.json
.venv-parser/bin/python benchmarks/bench.py parser tests/gold parser.json
```

Each run writes a JSON report and prints it.

## Accuracy

A row is right when the set of (start, end, value) that the library gives equals the gold set. A gold mention marked `low_confidence` counts when the library reports it at all. A mention is found when the library gives the same span and value.

| Language | Rows | numtag rows right | parser rows right | Gold mentions | numtag found | parser found |
|---|---|---|---|---|---|---|
| pt-PT | 458 | 452 | 384 | 493 | 491 | 400 |
| pt-BR | 456 | 450 | 386 | 492 | 490 | 404 |
| en | 420 | 419 | 353 | 440 | 440 | 373 |

The rows that numtag misses are in [languages/pt.md](languages/pt.md) and [languages/en.md](languages/en.md). The gold values come from sources and hand arithmetic, not from either library.

## Memory

| Measure | numtag | parser |
|---|---|---|
| Resident memory of the bare interpreter | 17.9 MiB | 17.7 MiB |
| Resident memory after the import | 20.6 MiB | 28.4 MiB |
| Resident memory after the whole run | 23.4 MiB | 29.6 MiB |
| Python allocations in the first call per language (tracemalloc peak) | 736 KiB | 65 KiB |

numtag loads the JSON lexicon of a language on the first call for that language. The parser builds its tables when it is imported, and its import also loads its dependencies.

## Time

| Measure | numtag | parser |
|---|---|---|
| Import | 0.018 s | 0.062 s |
| Per gold sentence, median (pt-PT / pt-BR / en) | 0.31 / 0.32 / 0.34 ms | 3.13 / 3.13 / 2.09 ms |
| Per gold sentence, 95th percentile (pt-PT / pt-BR / en) | 0.87 / 0.89 / 0.82 ms | 7.01 / 6.95 / 6.58 ms |
| Short command, median (pt-PT / pt-BR / en) | 0.56 / 0.59 / 0.53 ms | 7.59 / 8.01 / 5.16 ms |
| 2000 words of pt-PT text, best of 3 | 0.103 s | 1.077 s |

The per-sentence times come from 5 passes over each corpus after a first call. The short command is read 200 times. It is "quanto é vinte e três mais quarenta e cinco" in Portuguese and "what is twenty three plus forty five" in English. The long text is the first 2000 words of the pt-PT gold sentences, joined.

Times depend on the machine and its load. Compare the two columns of one run, not numbers from different runs.

---
[← Design](design.md) · [Home](index.md) · [Roadmap →](roadmap.md)
