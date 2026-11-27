"""The writer blocks and the allow-list entries are what their scripts write."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

import golden_writers

ROOT = Path(__file__).parent.parent
LEXICONS = ROOT / "numtag" / "lexicon"
WRITERS = sorted(path.stem for path in LEXICONS.glob("*.json")
                 if json.loads(path.read_text(encoding="utf-8")).get("writer"))
# scripts/writer_<lang>.py writes the lexicon <lang> or each variety <lang>-*.
SCRIPTS = [(path.name, name) for path in sorted((ROOT / "scripts").glob("writer_*.py"))
           for name in WRITERS if name.split("-")[0] == path.stem.removeprefix("writer_")]


def check(script: str, lang: str) -> None:
    run = subprocess.run([sys.executable, f"scripts/{script}", lang, "--check"], cwd=ROOT,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def test_every_writer_script_writes_a_lexicon():
    scripts = sorted(path.name for path in (ROOT / "scripts").glob("writer_*.py"))
    assert sorted({script for script, _ in SCRIPTS}) == scripts


@pytest.mark.parametrize(("script", "lang"), SCRIPTS)
def test_the_writer_block_is_what_the_script_writes(script, lang):
    check(script, lang)


def test_the_allow_list_entries_are_what_the_script_writes(subtests):
    langs = sorted({row["lang"] for row in golden_writers.stored() if golden_writers.has_writer(row["lang"])})
    assert {"id", "ms", "pt-PT", "es", "nb"} <= set(langs)
    for lang in langs:
        with subtests.test(lang=lang):
            check("allow_list.py", lang)
