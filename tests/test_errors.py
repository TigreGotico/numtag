from pathlib import Path

import pytest

import numtag
from numtag import UnsupportedLanguageError, tag_numbers
from numtag.lexicon import load

LEXICONS = Path(numtag.__file__).parent / "lexicon"


def test_a_language_with_no_lexicon_raises_unsupported_language_error():
    with pytest.raises(UnsupportedLanguageError, match="no lexicon for language 'hi'"):
        tag_numbers("मेरे पास दो किताबें हैं", "hi")


def test_unsupported_language_error_is_a_value_error():
    with pytest.raises(ValueError):
        tag_numbers("two", "hi")


def test_a_bad_scale_is_no_unsupported_language():
    with pytest.raises(ValueError) as raised:
        tag_numbers("one", "en", scale="medium")
    assert not isinstance(raised.value, UnsupportedLanguageError)


def test_the_package_exports_the_error():
    assert "UnsupportedLanguageError" in numtag.__all__


def _three(lexicon):
    """The plainest word for 3, or the digit where no word stands alone."""
    words = [word for word, entries in lexicon.readings.items()
             if any(e.role == "unit" and e.value == "3" and not (e.ambiguous or e.bound or e.part or e.final)
                    for e in entries)]
    return min(words, key=len) if words else "3"


@pytest.mark.parametrize("lang", sorted(path.stem for path in LEXICONS.glob("*.json")))
def test_a_joiner_or_a_marker_word_at_the_edge_of_the_text(lang):
    # nothing follows the joiner or the marker: the number before it stays
    # a number of its own ("Ich habe drei und")
    lexicon = load(lang)
    three = _three(lexicon)
    for word in sorted(lexicon.joiners | lexicon.decimal_markers):
        assert [m.value for m in tag_numbers(f"{three} {word}", lang)][:1] == ["3"], word
    for marker in sorted(lexicon.decimal_markers):
        tag_numbers(marker, lang)
        tag_numbers(f"{marker} {three}", lang)
