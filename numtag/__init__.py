"""numtag: find every number in a text, with exact values and character spans."""
from numtag.mention import Form, Kind, NumberMention, Scale, is_canonical_value
from numtag.tagger import tag_numbers

__all__ = ["Form", "Kind", "NumberMention", "Scale", "is_canonical_value", "tag_numbers"]
