"""Split a text into words and digit strings, each with its character offsets."""
import re
from dataclasses import dataclass, replace

# A digit string keeps its group and decimal marks ("1.000.000,5"). A minus
# sign or a lone mark belongs to it only at the start of a word ("-5" and
# ".5", not "5-7" or "...5"). The pattern takes digits of every script, so
# that a run with any digit outside 0-9 ("٣", "１２") is found whole and then
# dropped.
# A soft hyphen (U+00AD) inside a word marks where a line may break; it
# is no break in the word ("huszon\u00adöt").
SOFT_HYPHEN = "\u00ad"
_TOKEN = re.compile(r"(?P<digits>(?:(?<![^\s(\[])[-−.,])?\d+(?:[.,]\d+)*)|(?P<word>[^\W\d_]+(?:\u00ad[^\W\d_]+)*)")
_ASCII_DIGITS = re.compile(r"[-−.,]?[0-9]+(?:[.,][0-9]+)*")
_LONE_MARK = re.compile(r"[.,][0-9]+")
_TRAILING_MARK = re.compile(r"\D+$")
_WORD = re.compile(r"[^\W\d_]+")


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
    # A part of a compound word that goes on from the previous token with
    # no space ("kymmentä" in "kaksikymmentä").
    glued: bool = False
    # The lower-case form where the language folds case in its own way.
    folded: str = ""

    @property
    def norm(self) -> str:
        return self.folded or self.text.casefold()

    @property
    def digits(self) -> str:
        """A digit string without its ordinal suffix and the mark before it."""
        if not self.suffix or not self.text.endswith(self.suffix):
            return self.text
        return _TRAILING_MARK.sub("", self.text[:len(self.text) - len(self.suffix)])

    def links_to_previous(self) -> bool:
        """True when this token can continue a number that the previous
        token is part of: only a space or a hyphen lies between them."""
        return self.glued or self.gap == "-" or (self.gap != "" and self.gap.isspace())


def fold_dotted_i(text: str) -> str:
    """Lower-case text with the Turkic letters: "I" is "ı" and "İ" is "i"."""
    return text.replace("I", "ı").replace("İ", "i").casefold()


def split_compound(word: str, known: frozenset[str]) -> list[str] | None:
    """The fewest known words that make up ``word`` with nothing between
    them, or None when no such chain exists."""
    best: list[list[str] | None] = [[]] + [None] * len(word)
    for start in range(len(word)):
        if best[start] is None:
            continue
        for end in range(start + 1, len(word) + 1):
            if word[start:end] in known and (best[end] is None or len(best[start]) + 1 < len(best[end])):
                best[end] = best[start] + [word[start:end]]
    return best[-1]


def tokenize(text: str, ordinal_suffixes: frozenset[str] = frozenset(),
             lone_decimal_marks: frozenset[str] = frozenset(),
             abbreviations: frozenset[str] = frozenset(),
             number_words: frozenset[str] | None = None, *,
             compound_words: frozenset[str] = frozenset(), dotted_i: bool = False,
             digit_suffix_marks: frozenset[str] = frozenset(),
             dot_ordinal: bool = False, date_months: frozenset[str] = frozenset()) -> list[Token]:
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
    ("segunda-feira"): its words are dropped in the same way.

    A word that is not in ``compound_words`` but splits into a chain of
    them is one token per part, each glued to the one before. A word after
    one of ``digit_suffix_marks`` right after a digit string is its ordinal
    suffix or else its case ending, which is dropped ("5'inci", "5-öt").
    With ``dot_ordinal``, a period after a digit string makes it an
    ordinal when a lower-case word or a digit follows ("2. emelet"); the
    period stays outside the token. Before one of ``date_months`` the
    period follows the year of a date, which is no ordinal ("2008. február").
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
        if not is_digits and tokens and tokens[-1].is_digits and not tokens[-1].suffix \
                and gap in digit_suffix_marks and tokens[-1].end == previous_end:
            continue  # a case ending glued to digits: "5-öt", "5'te"
        end, suffix = match.end(), ""
        if is_digits and index + 1 < len(matches):
            following = matches[index + 1]
            between = text[match.end():following.start()]
            if (following.lastgroup == "word" and (between in ("", ".") or between in digit_suffix_marks)
                    and following.group().casefold() in ordinal_suffixes):
                end, suffix = following.end(), following.group()
                skip_until = following.end()
        if is_digits and dot_ordinal and not suffix and _dot_ordinal(text, end, date_months):
            suffix = "."  # the period stays outside the span, as punctuation
        word = text[start:end]
        letters = word.replace(SOFT_HYPHEN, "")
        folded = "" if is_digits else fold_dotted_i(letters) if dotted_i else \
            letters.casefold() if letters != word else ""
        key = folded or word.casefold()
        # the offset in the text of each letter of the word
        offsets = [start + k for k, char in enumerate(word) if char != SOFT_HYPHEN]
        parts = None
        if compound_words and not is_digits and key not in compound_words and len(key) == len(offsets):
            parts = split_compound(key, compound_words)
        if parts and len(parts) > 1:
            at = 0
            for k, part in enumerate(parts):
                first, last = offsets[at], offsets[at + len(part) - 1] + 1
                tokens.append(Token(text[first:last], first, last, False, gap if k == 0 else "",
                                    glued=k > 0, folded=part))
                at += len(part)
        else:
            tokens.append(Token(word, start, end, is_digits, gap, suffix, folded=folded))
        previous_end = end
    return tokens if number_words is None else _drop_compound_nouns(text, tokens, number_words)


def _drop_compound_nouns(text: str, tokens: list[Token], number_words: frozenset[str]) -> list[Token]:
    """The tokens without the words of each hyphenated compound that holds
    a word outside ``number_words``. The token after a dropped word gets the
    text since the last kept token as its gap, so it links to nothing."""
    dropped = set()
    start = 0
    for i in range(1, len(tokens) + 1):
        if i < len(tokens) and (tokens[i].gap == "-" or tokens[i].glued):
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


def _dot_ordinal(text: str, end: int, date_months: frozenset[str]) -> bool:
    """True when a period, a space and a lower-case word or a digit follow
    the digit string that ends at ``end``, and the word is no month of
    ``date_months``: a full name, with or without a case ending
    ("januárban"), or an abbreviation listed with its period ("jan.")."""
    if not text.startswith(".", end):
        return False
    rest = text[end + 1:]
    stripped = rest.lstrip()
    if not stripped or len(stripped) == len(rest) or not (stripped[0].islower() or stripped[0].isdigit()):
        return False
    word = _WORD.match(stripped)
    if not word:
        return True
    name = word.group().casefold()
    if stripped.startswith(".", word.end()) and name + "." in date_months:
        return False  # an abbreviated month ("2008. febr. 3.")
    return not any(name.startswith(month) for month in date_months if not month.endswith("."))


def _abbreviated(text: str, end: int) -> bool:
    """True when a period follows the word that ends at ``end`` and no
    sentence end does: after the period comes a digit, a lower-case word or
    more punctuation, not a capital or the end of the text."""
    if not text.startswith(".", end):
        return False
    rest = text[end + 1:].lstrip()
    return bool(rest) and not rest[0].isupper()
