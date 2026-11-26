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
LEADERS = ["pt-PT", "pt-BR", "es", "fr-FR", "it", "de", "nl", "da", "kab", "hi", "bn", "mwr"]
NOTES = {"es": "es-CO resolves to es"}
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

Each row is one lexicon in `numtag/lexicon/`. A lexicon reads cardinals when it has unit entries, ordinals when it has ordinal entries or entries with an ordinal form, and fractions when it has half, denominator, fraction or rational entries. It has a writer when the file has a `writer` block. "Gold rows" is the number of rows in `tests/gold/<lang>.jsonl`, and "right" is the number of rows that numtag reads right, from `benchmarks/results.json`. A dash means the language has no gold file.

The leader languages come first. The other languages follow in alphabetical order.

| Language | Cardinals | Ordinals | Fractions | Writer | Gold rows | Right | Page |
|---|---|---|---|---|---|---|---|
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
    langs = sorted(path.stem for path in LEXICONS.glob("*.json"))
    order = LEADERS + [lang for lang in langs if lang not in LEADERS]
    yes = lambda flag: "yes" if flag else "no"
    lines = []
    for lang in order:
        name = f"`{lang}`" + (f" ({NOTES[lang]})" if lang in NOTES else "")
        if lang not in langs:
            lines.append(f"| {name} | not supported | | | | | | |")
            continue
        found = roles(lang)
        writer = "writer" in json.loads((LEXICONS / f"{lang}.json").read_text(encoding="utf-8"))
        score = results.get(lang)
        rows, right = (score["rows"], score["rows_right"]) if score else ("-", "-")
        lines.append(f"| {name} | {yes('unit' in found)} | {yes(found & ORDINAL_ROLES)} | "
                     f"{yes(found & FRACTION_ROLES)} | {yes(writer)} | {rows} | {right} | {page_for(lang)} |")
    return HEADER + "\n".join(lines) + "\n\n---\n[← Home](../index.md)\n"


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
