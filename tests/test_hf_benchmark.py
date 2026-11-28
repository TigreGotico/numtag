"""Scores numtag on the Hugging Face dataset TigreGotico/numtag-benchmark.

The dataset is downloaded once, at the revision that hf_benchmark_floor.json
pins, into ~/.cache/numtag-bench. A row scores when tag_numbers returns a
mention with the row's char_span and the same value as a fraction. Each
(language, kind, tier) group must reach its floor. Tier is "gold" or
"silver", the first word of the row's source.

To move to a new revision: change "revision", run this file with
NUMTAG_BENCH_WRITE=1 to measure the floors, and read the diff.
"""
import json
import os
import urllib.request
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pytest

from numtag import tag_numbers

HERE = Path(__file__).parent
FLOORS = HERE / "hf_benchmark_floor.json"
CONFIG = json.loads(FLOORS.read_text(encoding="utf-8"))
URL = "https://huggingface.co/datasets/{repo}/resolve/{revision}/{path}"
CACHE = Path.home() / ".cache" / "numtag-bench"


def load_rows() -> list[dict]:
    target = CACHE / f"{CONFIG['revision']}-{Path(CONFIG['path']).name}"
    if not target.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(URL.format(**CONFIG), timeout=60) as response:
                data = response.read()
        except OSError as error:
            if os.environ.get("CI"):
                raise
            pytest.skip(f"no network for {CONFIG['repo']}: {error}")
        target.with_suffix(".part").write_bytes(data)
        target.with_suffix(".part").rename(target)
    return [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]


def row_scores(row: dict) -> bool:
    for mention in tag_numbers(row["text"], row["lang"]):
        if list(mention.char_span) == row["char_span"]:
            return Fraction(mention.value) == Fraction(row["value"])
    return False


def measure(rows: list[dict]) -> dict[str, float]:
    hits, totals = Counter(), Counter()
    for row in rows:
        group = f"{row['lang']} {row['kind']} {row['source'].split(':')[0]}"
        totals[group] += 1
        hits[group] += row_scores(row)
    return {group: hits[group] / totals[group] for group in sorted(totals)}


def test_each_group_reaches_its_floor():
    scores = measure(load_rows())
    if os.environ.get("NUMTAG_BENCH_WRITE"):
        CONFIG["floors"] = {group: int(score * 1000) / 1000 for group, score in scores.items()}
        FLOORS.write_text(json.dumps(CONFIG, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    assert scores.keys() == CONFIG["floors"].keys(), "the groups changed: measure the floors again"
    below = {group: (round(score, 3), CONFIG["floors"][group])
             for group, score in scores.items() if score < CONFIG["floors"][group]}
    assert not below, f"score below floor (score, floor): {below}"
