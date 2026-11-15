"""Check every gold file against the format in README.md.

Run: python tests/gold/check_gold.py [file.jsonl ...]
It prints "<file>: N in, N out" per file and exits non-zero when a row fails.
"""
import json
import re
import sys
import unicodedata
from fractions import Fraction
from math import gcd
from pathlib import Path

from numtag import is_canonical_value

GOLD_DIR = Path(__file__).parent
KINDS = {"cardinal", "ordinal", "fraction", "decimal"}
ROW_KEYS = {"text", "mentions", "source"}
MENTION_KEYS = {"start", "end", "value", "kind"}
OPTIONAL_MENTION_KEYS = {"low_confidence"}
WHOLE = re.compile(r"-?[0-9]+")


def _is_edge_noise(ch: str) -> bool:
    return ch.isspace() or unicodedata.category(ch)[0] in "PSZ"


def _has_finite_decimal(denominator: int) -> bool:
    for p in (2, 5):
        while denominator % p == 0:
            denominator //= p
    return denominator == 1


def check_value(value, kind) -> None:
    assert isinstance(value, str) and is_canonical_value(value), f"value {value!r} is not canonical"
    assert kind in KINDS, f"kind {kind!r} is not one of {sorted(KINDS)}"
    whole = bool(WHOLE.fullmatch(value))
    if kind in ("cardinal", "ordinal"):
        assert whole, f"a {kind} has a whole value, not {value!r}"
    else:
        assert not whole, f"a {kind} value {value!r} is whole, so its kind is cardinal"
    if kind == "decimal":
        assert "." in value, f"a decimal value is written with a point, not {value!r}"
    if "/" in value:
        num, den = (abs(int(part)) for part in value.split("/"))
        assert gcd(num, den) == 1, f"fraction {value!r} is not in lowest terms"
        assert not _has_finite_decimal(den), f"fraction {value!r} has a finite decimal form, {Fraction(value)}"


def check_row(row) -> None:
    """Raise AssertionError when one parsed row breaks the format."""
    assert isinstance(row, dict), "a row is a JSON object"
    assert set(row) == ROW_KEYS, f"row keys {sorted(row)} are not {sorted(ROW_KEYS)}"
    text, mentions, source = row["text"], row["mentions"], row["source"]
    assert isinstance(text, str) and text.strip(), "text is a non-empty string"
    assert isinstance(source, str) and source.strip(), "source is a non-empty string"
    assert isinstance(mentions, list), "mentions is a list"
    previous_end = 0
    for m in mentions:
        assert isinstance(m, dict), "a mention is a JSON object"
        keys = set(m)
        assert MENTION_KEYS <= keys <= MENTION_KEYS | OPTIONAL_MENTION_KEYS, f"mention keys {sorted(keys)}"
        start, end = m["start"], m["end"]
        assert type(start) is int and type(end) is int, "start and end are integers"
        assert 0 <= start < end <= len(text), f"span ({start}, {end}) does not fit the text"
        assert start >= previous_end, f"mention at {start} overlaps or precedes the one ending at {previous_end}"
        previous_end = end
        span = text[start:end]
        first = span[0]
        if first in "-−" and m["value"].startswith("-") and len(span) > 1:
            first = span[1]
        assert not _is_edge_noise(first), f"span {span!r} starts with space, punctuation or a symbol"
        assert not _is_edge_noise(span[-1]), f"span {span!r} ends with space, punctuation or a symbol"
        check_value(m["value"], m["kind"])
        if "low_confidence" in m:
            assert m["low_confidence"] is True, "low_confidence is present only as true"


def check_file(path: Path) -> tuple[int, list[str]]:
    """Return the number of lines read and one message per failing line."""
    lines = path.read_text(encoding="utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    errors = []
    for number, line in enumerate(lines, 1):
        try:
            check_row(json.loads(line))
        except (ValueError, AssertionError) as exc:
            errors.append(f"{path.name}:{number}: {exc}")
    return len(lines), errors


def main(paths: list[str]) -> int:
    files = [Path(p) for p in paths] or sorted(GOLD_DIR.glob("*.jsonl"))
    failed = False
    for path in files:
        n_in, errors = check_file(path)
        print(f"{path.name}: {n_in} in, {n_in - len(errors)} out")
        for error in errors:
            print("  " + error)
        failed = failed or bool(errors)
    return 1 if failed or not files else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
