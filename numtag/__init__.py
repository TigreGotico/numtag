"""numtag: find every number in a text, with exact values and character spans."""
from numtag.lexicon import UnsupportedLanguageError
from numtag.mention import Form, Kind, NumberMention, Part, Reason, Role, Scale, is_canonical_value
from numtag.tagger import ARTICLE_CONFIDENCE, tag_numbers

__all__ = ["ARTICLE_CONFIDENCE", "Form", "Kind", "NumberMention", "Part", "Reason", "Role", "Scale",
           "UnsupportedLanguageError", "is_canonical_value", "tag_numbers"]
