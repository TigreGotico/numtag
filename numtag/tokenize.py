"""Split a text into words and digit strings, each with its character offsets."""
import re
from dataclasses import dataclass, replace
from functools import cache

# A digit string keeps its group and decimal marks ("1.000.000,5"). A minus
# sign or a lone mark belongs to it only at the start of a word ("-5" and
# ".5", not "5-7" or "...5"). The pattern takes digits of every script, so
# that a run with any digit outside 0-9 ("٣", "１２") is found whole and then
# dropped.
_TOKEN = re.compile(r"(?P<digits>(?:(?<![^\s(\[])[-−.,])?\d+(?:[.,]\d+)*)|(?P<word>[^\W\d_]+)")
_ASCII_DIGITS = re.compile(r"[-−.,]?[0-9]+(?:[.,][0-9]+)*")
_LONE_MARK = re.compile(r"[.,][0-9]+")


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
    # The lexicon word of a compound read as one token ("dètz-e-sèt" for
    # "dètz e sèt").
    key: str = ""

    @property
    def norm(self) -> str:
        return self.key or self.text.casefold()

    @property
    def digits(self) -> str:
        """A digit string without its ordinal suffix."""
        return self.text[:len(self.text) - len(self.suffix)].rstrip(".") if self.suffix else self.text

    def links_to_previous(self) -> bool:
        """True when this token can continue a number that the previous
        token is part of: only a space or a hyphen lies between them."""
        return self.gap == "-" or (self.gap != "" and self.gap.isspace())


def tokenize(text: str, ordinal_suffixes: frozenset[str] = frozenset(),
             lone_decimal_marks: frozenset[str] = frozenset(),
             abbreviations: frozenset[str] = frozenset(),
             number_words: frozenset[str] | None = None,
             compounds: frozenset[str] = frozenset()) -> list[Token]:
    """Words and digit strings of ``text``; punctuation only shows in gaps.

    A word glued to a digit string is its ordinal suffix when the language
    lists it, after an optional dot ("1.º"). A digit string glued to the end
    of a word ("mp3") is part of a name and is dropped, and so is a digit
    string with a digit outside 0-9. A digit string keeps a mark before its
    first digit only when the language lists the mark as a lone decimal mark
    and only digits follow it (".5"). An abbreviation is a listed word with a
    period that no sentence end follows ("dez. 2025"); it is dropped, so it
    breaks the link between the words around it. Given ``number_words``, a
    hyphenated compound with a word outside them is one noun
    ("segunda-feira"): its words are dropped in the same way. The words of
    a listed compound become one token ("dètz-e-sèt", "bint'i un").
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
        if not is_digits and match.group().casefold() in abbreviations and _abbreviated(text, match.end()):
            continue
        start = match.start()
        if is_digits and match.group()[0] in ".," and not (
                match.group()[0] in lone_decimal_marks and _LONE_MARK.fullmatch(match.group())):
            start += 1
        gap = text[previous_end:start]
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
        tokens.append(Token(text[start:end], start, end, is_digits, gap, suffix))
        previous_end = end
    if compounds:
        tokens = _join_compounds(text, tokens, compounds)
    return tokens if number_words is None else _drop_compound_nouns(text, tokens, number_words)


# The marks that may stand between the words of a compound. A hyphen and a
# space stand for each other ("dètz-e-sèt", "dètz e sèt"); the typographic
# apostrophe stands for the straight one; a period stands for the middle dot
# ("mil.lèsim").
COMPOUND_MARK = re.compile(r"[-\s'’·.]")
_MARK_CLASS = {"-": "-", "'": "'", "’": "'", "·": "·", ".": "·"}


def _mark(gap: str) -> str | None:
    if gap and gap.isspace():
        return "-"
    return _MARK_CLASS.get(gap)


def compound_parts(word: str) -> tuple[tuple[str, ...], tuple[str | None, ...]]:
    """The words of a compound and the class of each mark between them."""
    parts = COMPOUND_MARK.split(word.casefold())
    marks = tuple(_mark(m) for m in COMPOUND_MARK.findall(word))
    return tuple(parts), marks


@cache
def _shapes(compounds: frozenset[str]) -> list[tuple[tuple[str, ...], tuple[str | None, ...], str]]:
    """(words, marks, key) of each compound, the longest first."""
    return sorted((compound_parts(c) + (c.casefold(),) for c in compounds), key=lambda shape: -len(shape[0]))


def _join_compounds(text: str, tokens: list[Token], compounds: frozenset[str]) -> list[Token]:
    """The tokens with the words of each listed compound joined into one
    token, the longest compound first."""
    shapes = _shapes(compounds)
    joined: list[Token] = []
    i = 0
    while i < len(tokens):
        for parts, marks, key in shapes:
            run = tokens[i:i + len(parts)]
            if (len(run) == len(parts) and all(not t.is_digits for t in run)
                    and tuple(t.norm for t in run) == parts
                    and tuple(_mark(t.gap) for t in run[1:]) == marks):
                joined.append(Token(text[run[0].start:run[-1].end], run[0].start, run[-1].end,
                                    False, run[0].gap, key=key))
                i += len(parts)
                break
        else:
            joined.append(tokens[i])
            i += 1
    return joined


def _drop_compound_nouns(text: str, tokens: list[Token], number_words: frozenset[str]) -> list[Token]:
    """The tokens without the words of each hyphenated compound that holds
    a word outside ``number_words``. The token after a dropped word gets the
    text since the last kept token as its gap, so it links to nothing."""
    dropped = set()
    start = 0
    for i in range(1, len(tokens) + 1):
        if i < len(tokens) and tokens[i].gap == "-":
            continue
        compound = tokens[start:i]
        if len(compound) > 1 and any(not t.is_digits and t.norm not in number_words for t in compound):
            dropped.update(k for k in range(start, i) if not tokens[k].is_digits)
        start = i
    kept: list[Token] = []
    for i, token in enumerate(tokens):
        if i in dropped:
            continue
        if i and i - 1 in dropped:
            token = replace(token, gap=text[kept[-1].end if kept else 0:token.start])
        kept.append(token)
    return kept


def _abbreviated(text: str, end: int) -> bool:
    """True when a period follows the word that ends at ``end`` and no
    sentence end does: after the period comes a digit, a lower-case word or
    more punctuation, not a capital or the end of the text."""
    if not text.startswith(".", end):
        return False
    rest = text[end + 1:].lstrip()
    return bool(rest) and not rest[0].isupper()
