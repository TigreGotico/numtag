"""numtag: find every number in a text, with exact values and character spans."""
from numtag.lexicon import UnsupportedLanguageError
from numtag.mention import (Form, Kind, NumberMention, Part, Reason, Role, Scale, VagueKind, VagueQuantity,
                            is_canonical_value)
from numtag.tagger import ARTICLE_CONFIDENCE, revision, tag_numbers
from numtag.vague import tag_vague_quantities

__all__ = ["ARTICLE_CONFIDENCE", "Form", "Kind", "NumberMention", "Part", "Reason", "Role", "Scale", "Spelling",
           "SpellingReason", "SpokenForm", "UnsupportedLanguageError", "VagueKind", "VagueQuantity",
           "is_canonical_value", "revision", "spell", "tag_numbers", "tag_vague_quantities"]

_WRITER = frozenset(("Spelling", "SpellingReason", "SpokenForm", "spell"))


def __getattr__(name: str):
    """The writer loads on its first use, so a program that only reads pays nothing for it."""
    if name in _WRITER:
        from numtag import writer
        return getattr(writer, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
