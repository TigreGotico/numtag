from numtag import tag_numbers


def read(text: str, lang: str, **options) -> list[tuple[str, str, str]]:
    """(words, value, kind) of each mention, after checking each span."""
    mentions = tag_numbers(text, lang, **options)
    for mention in mentions:
        start, end = mention.char_span
        assert text[start:end] == mention.text
    return [(m.text, m.value, m.kind.value) for m in mentions]
