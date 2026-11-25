"""The golden file: what every shipped lexicon makes of every gold and consumer text.

``python tests/golden.py`` writes ``tests/golden/readings.jsonl.gz`` from the
installed numtag. Each row is one text at one scale with every field of every
mention, and, at the default scale, of every vague quantity.
"""
import gzip
import json
import sys
from dataclasses import asdict
from pathlib import Path

from numtag import Scale, tag_numbers, tag_vague_quantities

HERE = Path(__file__).parent
GOLDEN = HERE / "golden" / "readings.jsonl.gz"


def _inputs() -> list[tuple[str, str]]:
    found = []
    for path in sorted((HERE / "gold").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                found.append((path.stem, json.loads(line)["text"]))
    for path in sorted((HERE / "consumers").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                found.append((row["lang"], row["text"]))
    return found


def _fields(mention) -> dict:
    """Every field of a mention but ``lang``, which the golden rows name already."""
    return {key: value for key, value in asdict(mention).items() if key != "lang"}


def _line(row: dict) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True, default=sorted)


def rows() -> list[str]:
    """One JSON line for each text, at the default scale and at the long scale."""
    lines = []
    for lang, text in _inputs():
        lines.append(_line({"lang": lang, "scale": "default", "text": text,
                            "mentions": [_fields(m) for m in tag_numbers(text, lang)],
                            "vague": [asdict(v) for v in tag_vague_quantities(text, lang)]}))
        lines.append(_line({"lang": lang, "scale": "long", "text": text,
                            "mentions": [_fields(m) for m in tag_numbers(text, lang, scale=Scale.LONG)]}))
    return lines


def stored() -> list[str]:
    with gzip.open(GOLDEN, "rt", encoding="utf-8") as file:
        return file.read().splitlines()


if __name__ == "__main__":
    out = rows()
    with open(GOLDEN, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as file:
        file.write(("\n".join(out) + "\n").encode("utf-8"))
    print(f"{len(out)} rows", file=sys.stderr)
