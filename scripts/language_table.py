"""Write docs/languages/index.md, the support table, from the lexicons and benchmarks/results.json.

usage: python scripts/language_table.py [--measure] [--check]
--measure  runs tag_numbers over tests/gold/*.jsonl and writes benchmarks/results.json.
--check    compares the files with what the script writes and changes nothing.
A row scores as in tests/test_gold.py.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
LEXICONS = ROOT / "numtag" / "lexicon"
GOLD = ROOT / "tests" / "gold"
RESULTS = ROOT / "benchmarks" / "results.json"
PAGE = ROOT / "docs" / "languages" / "index.md"
LEADERS = ["pt-PT", "pt-BR", "es-CO", "fr-FR", "it-IT", "de-DE", "nl-NL", "da-DK", "kab", "hi-IN", "bn-IN", "mwr"]
FEW_ROWS = 100
ORDINAL_ROLES = {"ordinal", "ordinal_scale", "ordinal_suffix"}
FRACTION_ROLES = {"half", "denominator", "fraction", "rational"}

HEADER = """# Supported languages

<!-- agent-hint
covers: Per lexicon, what numtag reads and writes, and its score on the gold corpus.
source: numtag/lexicon/*.json, benchmarks/results.json
generated: yes, by scripts/language_table.py; do not edit by hand
verify: python scripts/language_table.py --check
see: ../adding-a-language.md, ../benchmarks.md
-->

Each row is one lexicon in `numtag/lexicon/`. A lexicon reads cardinals when it has unit entries, ordinals when it has ordinal entries or entries with an ordinal form, and fractions when it has half, denominator, fraction or rational entries. It has a writer when the file has a `writer` block. "Gold rows" is the number of rows in `tests/gold/<lang>.jsonl`, "Rows right" is the number of rows that numtag reads right, from `benchmarks/results.json`, and "Share" is rows right divided by gold rows. A dash means the language has no gold file.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../img/coverage-dark.svg">
  <img alt="Of 53 lexicons, 53 read cardinals, 52 read ordinals, 51 read fractions and 25 have a writer." src="../img/coverage.svg">
</picture>

`img/plot_coverage.py` makes this figure from `numtag/lexicon/*.json`.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../img/share-dark.svg">
  <img alt="33 of 51 gold sets score 100 %. The lowest are mt at 95.7 %, he at 98.1 %, it at 98.5 %." src="../img/share.svg">
</picture>

`img/plot_share.py` makes this figure from `benchmarks/results.json`.

The leader languages come first, each named by its full tag and the lexicon that the tag resolves to. The other languages follow in alphabetical order.

| Language | Cardinals | Ordinals | Fractions | Writer | Gold rows | Rows right | Share | Page |
|---|---|---|---|---|---|---|---|---|
"""


def roles(lang: str) -> set[str]:
    data = json.loads((LEXICONS / f"{lang}.json").read_text(encoding="utf-8"))
    found = {entry["role"] for entry in data.get("entries", ())}
    if any(entry.get("ordinal") for entry in data.get("entries", ())):
        found.add("ordinal")
    if "extends" in data:
        found |= roles(data["extends"])
    return found


def page_for(lang: str) -> str:
    base = lang.split("-")[0]
    for path in sorted(PAGE.parent.glob("*.md")):
        if path == PAGE:
            continue
        text = path.read_text(encoding="utf-8")
        if path.stem in (lang, base) or f"`{lang}`" in text or f"`{base}`" in text:
            return f"[{path.name}]({path.name})"
    return ""


def measure() -> dict:
    sys.path.insert(0, str(ROOT / "tests"))
    from test_gold import score_file
    results = {}
    for path in sorted(GOLD.glob("*.jsonl")):
        score = score_file(path)
        results[score.lang] = {"rows": score.rows, "rows_right": score.correct}
    return results


def render(results: dict) -> str:
    from numtag import UnsupportedLanguageError
    from numtag.tagger import lexicon_name
    langs = sorted(path.stem for path in LEXICONS.glob("*.json"))
    leaders = []
    for tag in LEADERS:
        try:
            leaders.append((tag, lexicon_name(tag)))
        except UnsupportedLanguageError:
            leaders.append((tag, None))
    order = leaders + [(lang, lang) for lang in langs if lang not in {lex for _, lex in leaders}]
    yes = lambda flag: "yes" if flag else "no"
    lines, notes = [], []
    for tag, lang in order:
        name = f"`{tag}`" if lang in (tag, None) else f"`{tag}` (resolves to `{lang}`)"
        if lang is None:
            lines.append(f"| {name} | not supported | | | | | | | |")
            continue
        found = roles(lang)
        writer = "writer" in json.loads((LEXICONS / f"{lang}.json").read_text(encoding="utf-8"))
        score = results.get(lang)
        if score:
            rows, right = score["rows"], score["rows_right"]
            share = f"{100 * right / rows:.1f}%"
            if rows < FEW_ROWS:
                notes.append(f"[^{lang}]: The score of `{lang}` rests on {rows} rows.")
                share += f"[^{lang}]"
        else:
            rows = right = share = "-"
        lines.append(f"| {name} | {yes('unit' in found)} | {yes(found & ORDINAL_ROLES)} | "
                     f"{yes(found & FRACTION_ROLES)} | {yes(writer)} | {rows} | {right} | {share} | {page_for(lang)} |")
    footer = "\n\n" + "\n\n".join(notes) if notes else ""
    return HEADER + "\n".join(lines) + footer + "\n\n---\n[← Home](../index.md)\n"


def main() -> int:
    check = "--check" in sys.argv
    outputs = {}
    if "--measure" in sys.argv:
        outputs[RESULTS] = json.dumps(measure(), indent=1, sort_keys=True) + "\n"
        results = json.loads(outputs[RESULTS])
    else:
        results = json.loads(RESULTS.read_text(encoding="utf-8"))
    outputs[PAGE] = render(results)
    stale = [path for path, text in outputs.items()
             if not path.exists() or path.read_text(encoding="utf-8") != text]
    if check:
        for path in stale:
            print(f"{path.relative_to(ROOT)} differs from what scripts/language_table.py writes")
        return 1 if stale else 0
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
    print(f"{len(results)} gold sets in, {len(outputs)} files written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
