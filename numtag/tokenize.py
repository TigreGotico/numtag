"""Split a text into words and digit strings, each with its character offsets."""
import re
from dataclasses import dataclass, replace

# A digit string keeps its group and decimal marks ("1.000.000,5"). A minus
# sign or a lone mark belongs to it only at the start of a word ("-5" and
# ".5", not "5-7" or "...5"). The pattern takes digits of every script, so
# that a run with any digit outside 0-9 ("٣", "１２") is found whole and then
# dropped.
_TOKEN = re.compile(r"(?P<digits>(?:(?<![^\s(\[])(?:[-−][.,]?|[.,]))?\d+(?:[.,]\d+)*)|(?P<word>[^\W\d_]+)")
_ASCII_DIGITS = re.compile(r"(?:[-−][.,]?|[.,])?[0-9]+(?:[.,][0-9]+)*")
_LONE_MARK = re.compile(r"[.,][0-9]+")
# Apostrophes that a language may keep inside a word ("п'ять"); a word's
# normal form writes each of them as "'".
_APOSTROPHES = str.maketrans({"\u2019": "'", "\u02bc": "'"})


def fold(word: str) -> str:
    """The form a lexicon looks a word up by."""
    return word.casefold().translate(_APOSTROPHES)


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
    # A part of a compound word after its first part ("dvadsať|jeden").
    joined: bool = False

    @property
    def norm(self) -> str:
        return fold(self.text)

    @property
    def digits(self) -> str:
        """A digit string without its ordinal suffix."""
        return self.text[:len(self.text) - len(self.suffix)].rstrip(".-") if self.suffix else self.text

    def links_to_previous(self) -> bool:
        """True when this token can continue a number that the previous
        token is part of: only a space or a hyphen lies between them, or
        both are parts of one compound word."""
        return self.joined or self.gap == "-" or (self.gap != "" and self.gap.isspace())


def tokenize(text: str, ordinal_suffixes: frozenset[str] = frozenset(),
             lone_decimal_marks: frozenset[str] = frozenset(),
             abbreviations: frozenset[str] = frozenset(),
             number_words: frozenset[str] | None = None,
             apostrophes: frozenset[str] = frozenset(), suffix_marks: frozenset[str] = frozenset(),
             compound_parts: frozenset[str] = frozenset()) -> list[Token]:
    """Words and digit strings of ``text``; punctuation only shows in gaps.

    A word glued to a digit string is its ordinal suffix when the language
    lists it, after an optional dot ("1.º"). A digit string glued to the end
    of a word ("mp3") is part of a name and is dropped, and so is a digit
    string with a digit outside 0-9. A digit string keeps a mark before its
    first digit, also after a sign, only when the language lists the mark as
    a lone decimal mark and only digits follow it (".5", "-.5"). An abbreviation is a listed word with a
    period that no sentence end follows ("dez. 2025"); it is dropped, so it
    breaks the link between the words around it. Given ``number_words``, a
    hyphenated compound with a word outside them is one noun
    ("segunda-feira"): its words are dropped in the same way.

    A language may list ``apostrophes`` that join letters into one word
    ("п'ять"), ``suffix_marks`` that may stand between a digit string and its
    ordinal suffix besides a dot ("2-й"), and ``compound_parts``: a word
    that is no number word but a sequence of these parts ("dvadsaťjeden") is
    split into them.
    """
    tokens: list[Token] = []
    previous_end = 0
    pattern = _TOKEN
    if apostrophes:
        marks = re.escape("".join(sorted(apostrophes)))
        pattern = re.compile(_TOKEN.pattern.replace(r"(?P<word>[^\W\d_]+)",
                                                    rf"(?P<word>[^\W\d_]+(?:[{marks}][^\W\d_]+)*)"))
    matches = list(pattern.finditer(text))
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
        unsigned = match.group().lstrip("-−")
        if is_digits and unsigned[0] in ".," and not (
                unsigned[0] in lone_decimal_marks and _LONE_MARK.fullmatch(unsigned)):
            start += len(match.group()) - len(unsigned) + 1
        gap = text[previous_end:start]
        if is_digits and gap == "" and tokens and not tokens[-1].is_digits:
            previous_end = match.end()
            continue
        end, suffix = match.end(), ""
        if is_digits and index + 1 < len(matches):
            following = matches[index + 1]
            between = text[match.end():following.start()]
            if (following.lastgroup == "word" and (between in ("", ".") or between in suffix_marks)
                    and following.group().casefold() in ordinal_suffixes):
                end, suffix = following.end(), following.group()
                skip_until = following.end()
        token = Token(text[start:end], start, end, is_digits, gap, suffix)
        whole_word = number_words is not None and token.norm in number_words
        tokens += _split_compound(token, compound_parts) if compound_parts and not (is_digits or whole_word) else [token]
        previous_end = end
    return tokens if number_words is None else _drop_compound_nouns(text, tokens, number_words)


def _split_compound(token: Token, parts: frozenset[str]) -> list[Token]:
    """The parts of a compound number word, or the word alone when it is a
    number word itself or no sequence of number words spells it. The split
    with the fewest parts wins, and among those the longest first part."""
    word = token.norm
    if word in parts or len(word) != len(token.text):
        return [token]
    # best[i]: the fewest parts that spell word[:i], as their end positions
    best: dict[int, tuple[int, ...]] = {0: ()}
    for i in range(len(word)):
        if i not in best:
            continue
        for j in range(len(word), i, -1):
            if word[i:j] in parts and (j not in best or len(best[i]) + 1 < len(best[j])):
                best[j] = best[i] + (j,)
    ends = best.get(len(word), ())
    if len(ends) < 2:
        return [token]
    pieces, start = [], 0
    for n, end in enumerate(ends):
        pieces.append(Token(token.text[start:end], token.start + start, token.start + end, False,
                            token.gap if n == 0 else "", joined=n > 0))
        start = end
    return pieces


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
