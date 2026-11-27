from numtag import tag_numbers
from numtag.lexicon import V3_ENTRY_KEYS, V3_SETTINGS, V3_VERSION, WRITER_VERSION


def read(text: str, lang: str, **options) -> list[tuple[str, str, str]]:
    """(words, value, kind) of each mention, after checking each span."""
    mentions = tag_numbers(text, lang, **options)
    for mention in mentions:
        start, end = mention.char_span
        assert text[start:end] == mention.text
    return [(m.text, m.value, m.kind.value) for m in mentions]


def sure(text: str, lang: str) -> list[tuple[str, str, float]]:
    """(words, value, confidence) of each mention."""
    return [(m.text, m.value, round(m.confidence, 1)) for m in tag_numbers(text, lang)]


def holds_v3_keys(data: dict) -> bool:
    """The file holds a key that only version 3 reads."""
    return bool(set(data.get("settings", {})) & V3_SETTINGS) or any(
        set(spec) & V3_ENTRY_KEYS.get(spec["role"], set()) for spec in data.get("entries", ()))


def expected_version(data: dict) -> int:
    """The lowest version that reads the file: 3 for a key of version 3, 2 for a writer block, else 1."""
    return V3_VERSION if holds_v3_keys(data) else WRITER_VERSION if "writer" in data else 1
