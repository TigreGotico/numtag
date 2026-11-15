"""Split a text into words and digit strings, each with its character offsets."""
import re
from dataclasses import dataclass

# A digit string keeps its group and decimal marks ("1.000.000,5"). A minus
# sign belongs to it only at the start of a word ("-5", not "5-7"). The
# pattern takes digits of every script, so that a run with any digit outside
# 0-9 ("٣", "１２") is found whole and then dropped.
_TOKEN = re.compile(r"(?P<digits>(?:(?<![^\s(\[])[-−])?\d+(?:[.,]\d+)*)|(?P<word>[^\W\d_]+)")
_ASCII_DIGITS = re.compile(r"[-−]?[0-9]+(?:[.,][0-9]+)*")


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int
    is_digits: bool
    # Text between the previous token and this one.
    gap: str = ""
    # Ordinal suffix glued to a digit string ("º" in "1.º", "st" in "21st").
    suffix: str = ""

    @property
    def norm(self) -> str:
        return self.text.casefold()

    @property
    def digits(self) -> str:
        """A digit string without its ordinal suffix."""
        return self.text[:len(self.text) - len(self.suffix)].rstrip(".") if self.suffix else self.text

    def links_to_previous(self) -> bool:
        """True when this token can continue a number that the previous
        token is part of: only a space or a hyphen lies between them."""
        return self.gap == "-" or (self.gap != "" and self.gap.isspace())


def tokenize(text: str, ordinal_suffixes: frozenset[str] = frozenset()) -> list[Token]:
    """Words and digit strings of ``text``; punctuation only shows in gaps.

    A word glued to a digit string is its ordinal suffix when the language
    lists it, after an optional dot ("1.º"). A digit string glued to the end
    of a word ("mp3") is part of a name and is dropped, and so is a digit
    string with a digit outside 0-9.
    """
    tokens: list[Token] = []
    previous_end = 0
    matches = list(_TOKEN.finditer(text))
    skip_until = -1
    for index, match in enumerate(matches):
        if match.start() < skip_until:
            continue
        is_digits = match.lastgroup == "digits"
        if is_digits and not _ASCII_DIGITS.fullmatch(match.group()):
            continue
        gap = text[previous_end:match.start()]
        if is_digits and gap == "" and tokens and not tokens[-1].is_digits:
            previous_end = match.end()
            continue
        end, suffix = match.end(), ""
        if is_digits and index + 1 < len(matches):
            following = matches[index + 1]
            between = text[match.end():following.start()]
            if (following.lastgroup == "word" and between in ("", ".")
                    and following.group().casefold() in ordinal_suffixes):
                end, suffix = following.end(), following.group()
                skip_until = following.end()
        tokens.append(Token(text[match.start():end], match.start(), end, is_digits, gap, suffix))
        previous_end = end
    return tokens
