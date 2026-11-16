import pytest

import numtag
from numtag import UnsupportedLanguageError, tag_numbers


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
