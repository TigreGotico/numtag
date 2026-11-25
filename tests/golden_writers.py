"""The writer golden file: what the ovos-number-parser writers said for every language.

``tests/golden/onp-writers.jsonl.gz`` holds one call of ``pronounce_number``,
``pronounce_ordinal`` or ``pronounce_fraction`` per row, with the words it
returned or the name of the exception it raised. ``result`` runs the same call
through ``numtag.spell``. A row where the stored output is a known defect is on
the allow-list, ``tests/golden/onp-writers-allow.json``, with the output that a
cited source gives.
"""
import gzip
import json
from decimal import Decimal
from functools import cache
from pathlib import Path

from numtag import SpokenForm, spell
from numtag.lexicon import writer_block
from numtag.tagger import lexicon_name

GOLDEN = Path(__file__).parent / "golden" / "onp-writers.jsonl.gz"
ALLOW = Path(__file__).parent / "golden" / "onp-writers-allow.json"

# ovos-number-parser spells the third gender "neutral"; a lexicon spells it "neuter".
GENDERS = {"masculine": "masculine", "feminine": "feminine", "neutral": "neuter"}


def digit_string(number) -> str:
    """The canonical digit string of the int or float that a row holds."""
    if isinstance(number, int):
        return str(number)
    text = format(Decimal(repr(number)), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def stored() -> list[dict]:
    with gzip.open(GOLDEN, "rt", encoding="utf-8") as file:
        return [json.loads(line) for line in file]


@cache
def has_writer(tag: str) -> bool:
    return writer_block(lexicon_name(tag)) is not None


def result(row: dict) -> dict:
    """``{"out": words}`` or ``{"err": exception class name}`` of the row's call through ``spell``."""
    kw = row.get("kw", {})
    arg = row["arg"] if row["fn"] == "fraction" else digit_string(row["arg"])
    options = {"gender": GENDERS[kw["gender"]] if "gender" in kw else None, "scale": kw.get("scale"),
               "case": kw.get("case"), "places": kw.get("places"), "scientific": kw.get("scientific", False),
               "form": SpokenForm.ORDINAL if row["fn"] == "ordinal" or kw.get("ordinals") else SpokenForm.CARDINAL,
               "decimals": "digits" if kw.get("digits") == "digit" else None}
    try:
        return {"out": spell(arg, row["lang"], **options)[0].text}
    except Exception as error:
        return {"err": type(error).__name__}


def outcome(row: dict) -> dict:
    return {k: row[k] for k in ("out", "err") if k in row}


def key(row: dict) -> str:
    return json.dumps([row["lang"], row["fn"], row["arg"], row.get("kw", {})], sort_keys=True)


def allowed() -> dict[str, dict]:
    """The allow-list by row key: each entry names the row and the output that a source gives."""
    return {key(entry): entry for entry in json.loads(ALLOW.read_text(encoding="utf-8"))}


def mismatches(rows: list[dict], allow: dict[str, dict]) -> list[tuple[dict, dict]]:
    """The rows whose result differs from the stored output, each with that result. An allow-list entry
    replaces the stored output of its row."""
    found = []
    for row in rows:
        entry = allow.get(key(row))
        got = result(row)
        if got != outcome(entry or row):
            found.append((row, got))
    return found
