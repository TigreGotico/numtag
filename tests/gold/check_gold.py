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
OPTIONAL_MENTION_KEYS = {"low_confidence", "number_scale", "reasons"}
REASONS = {"article", "homograph"}
SCALES = {"long", "short"}
WHOLE = re.compile(r"-?[0-9]+")
#: the marks that make a value a decimal, per gold file: a digit mark or a word
DECIMAL_MARKS = {"pt-PT": (",", "vírgula", "virgula"), "pt-BR": (",", "vírgula", "virgula"),
                 "en": (".", "point"), "de": (",", "komma"), "nl": (",", "komma"), "fy": (",", "komma"),
                 "da": (",", "komma"), "sv": (",", "komma"), "nb": (",", "komma"), "nn": (",", "komma"),
                 "fi": (",", "pilkku"), "et": (",", "koma"), "hu": (",", "egész"),
                 "tr": (",", "virgül"), "az": (",", "tam", "vergül"),
                 "el": (",", "κόμμα"), "ar": (".", "٫", "فاصلة", "فاصل"), "he": (".", "נקודה"),
                 "fa": (".", "٫", "ممیز"), "kab": (",",),
                 "ru": (",", "целых", "целая", "целой", "запятая"), "uk": (",", "цілих", "ціла", "цілої", "кома"),
                 "bg": (",", "цяло", "цели", "запетая"), "pl": (",", "przecinek", "całych", "cała", "całe"),
                 "cs": (",", "celá", "celé", "celých", "čárka"), "sk": (",", "celá", "celé", "celých", "čiarka"),
                 "sl": (",", "cela", "celi", "cele", "celih", "vejica"), "hr": (",", "zarez", "cijela", "cijelih", "cijele"),
                 "sr": (",", "zarez", "koma"),
                 "fr-FR": (",", "virgule"), "fr-BE": (",", "virgule"), "fr-CH": (",", "virgule"),
                 "it": (",", "virgola"), "ro": (",", "virgulă", "virgula"), "eu": (",", "koma"),
                 "id": (",", "koma", "titik"), "hi": (".", "दशमलव"),
                 "ms": (".", "perpuluhan"),
                 "es": (",", "coma", "punto"), "gl": (",", "coma"), "ca": (",", "coma"),
                 "ast": (",", "coma", "puntu"), "an": (",", "coma"), "oc": (",", "virgula"),
                 "mwl": (",", "bírgula", "birgula", "ponto"),
                 "lt": (",", "kablelis"),
                 "mt": (".", "punt")}


def _is_edge_noise(ch: str) -> bool:
    return ch.isspace() or unicodedata.category(ch)[0] in "PSZ"


def _same_run(a: str, b: str) -> bool:
    return a.isalpha() and b.isalpha() or a.isdigit() and b.isdigit()


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


def check_row(row, lang: str = "") -> None:
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
        # a unit may touch digits ("3,5kg"); a letter run or a digit run may not go on
        assert start == 0 or not _same_run(text[start - 1], span[0]), f"span {span!r} starts inside a word"
        assert end == len(text) or not _same_run(span[-1], text[end]), f"span {span!r} ends inside a word"
        assert not (span[-1].isdigit() and text[end:end + 1] in (",", ".")
                    and text[end + 1:end + 2].isdigit()), f"span {span!r} stops before a digit mark"
        assert not (span[0].isdigit() and start >= 2 and text[start - 1] in (",", ".")
                    and text[start - 2].isdigit()), f"span {span!r} starts after a digit mark"
        check_value(m["value"], m["kind"])
        if lang in DECIMAL_MARKS and m["kind"] in ("decimal", "fraction"):
            words = re.findall(r"\w+|[.,٫]", span.lower())
            marked = any(mark in words for mark in DECIMAL_MARKS[lang])
            assert marked == (m["kind"] == "decimal"), \
                f"span {span!r} is {m['kind']}, but a decimal is exactly the kind with a decimal mark"
        if "low_confidence" in m:
            assert m["low_confidence"] is True, "low_confidence is present only as true"
        if "reasons" in m or "low_confidence" in m:
            assert m.get("low_confidence") is True and "reasons" in m, "low_confidence and reasons go together"
            assert isinstance(m["reasons"], list) and m["reasons"] and set(m["reasons"]) <= REASONS, \
                f"reasons {m['reasons']!r} is not a non-empty list from {sorted(REASONS)}"
        if "number_scale" in m:
            assert m["number_scale"] in SCALES, f"number_scale {m['number_scale']!r} is not one of {sorted(SCALES)}"


def check_file(path: Path) -> tuple[int, list[str]]:
    """Return the number of lines read and one message per failing line."""
    lines = path.read_text(encoding="utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if path.stem not in DECIMAL_MARKS:
        return len(lines), [f"{path.name}: no decimal marks are known for {path.stem!r}; add them to DECIMAL_MARKS"]
    errors, seen = [], {}
    for number, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
            check_row(row, path.stem)
            assert row["text"] not in seen, f"text repeats line {seen.get(row['text'])}"
            seen[row["text"]] = number
        except (ValueError, AssertionError) as exc:
            errors.append(f"{path.name}:{number}: {exc}")
    return len(lines), errors


def main(paths: list[str]) -> int:
    files = [Path(p) for p in paths] or sorted(GOLD_DIR.glob("*.jsonl"))
    failed = False
    for path in files:
        n_in, errors = check_file(path)
        n_out = n_in - len(errors) if path.stem in DECIMAL_MARKS else 0
        print(f"{path.name}: {n_in} in, {n_out} out")
        for error in errors:
            print("  " + error)
        failed = failed or bool(errors)
    return 1 if failed or not files else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
