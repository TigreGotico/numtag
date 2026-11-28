"""Scores numtag on the Hugging Face dataset TigreGotico/numtag-benchmark.

The dataset is downloaded once, at the revision that hf_benchmark_floor.json
pins, into ~/.cache/numtag-bench. It has one file per language.

Reading: a row scores when tag_numbers returns a mention with the row's
char_span, kind and value (compared as a fraction). Groups are (language,
kind, tier), where tier is "gold" or "silver", the first word of the source.

Speaking compares spell(value, lang, form, gender, case) with the row's
surface, ignoring letter case. On a canonical row (a cited source gives the
form) the first spelling must match. On a variant row (a natural form that no
source picks) any spelling may match. A spell() error is a miss. Groups are
(language, kind, canonical or variant). A row with a case and no gender is
left out, because spell() needs the gender to inflect for case.

Each group must reach its floor. To move to a new revision: change
"revision", run this file with NUMTAG_BENCH_WRITE=1 to measure the floors,
and read the diff.
"""
import json
import os
import urllib.error
import urllib.request
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pytest

from numtag import SpokenForm, spell, tag_numbers

HERE = Path(__file__).parent
FLOORS = HERE / "hf_benchmark_floor.json"
CONFIG = json.loads(FLOORS.read_text(encoding="utf-8"))
URL = "https://huggingface.co/datasets/{repo}/resolve/{revision}/data/{lang}.jsonl"
CACHE = Path.home() / ".cache" / "numtag-bench" / CONFIG["revision"]


def download(lang: str) -> Path:
    target = CACHE / f"{lang}.jsonl"
    if target.exists():
        return target
    CACHE.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(URL.format(lang=lang, **CONFIG), timeout=60) as response:
            data = response.read()
    except urllib.error.HTTPError:
        raise
    except OSError as error:
        if os.environ.get("CI"):
            raise
        pytest.skip(f"no network for {CONFIG['repo']}: {error}")
    part = target.with_suffix(".part")
    part.write_bytes(data)
    part.rename(target)
    return target


def load_rows() -> list[dict]:
    rows = []
    for lang in CONFIG["langs"]:
        rows += [json.loads(line) for line in download(lang).read_text(encoding="utf-8").splitlines()]
    return rows


def reads(row: dict) -> bool:
    for mention in tag_numbers(row["text"], row["lang"]):
        if list(mention.char_span) == row["char_span"]:
            return mention.kind.value == row["kind"] and Fraction(mention.value) == Fraction(row["value"])
    return False


def speaks(row: dict) -> bool:
    form = SpokenForm.ORDINAL if row["kind"] == "ordinal" else SpokenForm.CARDINAL
    try:
        spellings = spell(row["value"], row["lang"], form=form, gender=row["gender"], case=row["case"])
    except ValueError:
        return False
    if row["canonical"]:
        spellings = spellings[:1]
    return row["surface"].casefold() in {spelling.text.casefold() for spelling in spellings}


def measure(rows: list[dict]) -> dict[str, float]:
    hits, totals = Counter(), Counter()
    for row in rows:
        group = f"read {row['lang']} {row['kind']} {row['source'].split(':')[0]}"
        totals[group] += 1
        hits[group] += reads(row)
        tier = "canonical" if row["canonical"] else "variant" if row["variant"] else None
        if tier and not (row["case"] and not row["gender"]):
            group = f"speak {row['lang']} {row['kind']} {tier}"
            totals[group] += 1
            hits[group] += speaks(row)
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
