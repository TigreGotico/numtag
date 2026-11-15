"""Split a text into words and digit strings, each with its character offsets."""
import re
from dataclasses import dataclass, replace

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
    # A digit string that a period makes an ordinal ("3" in "am 3. Mai").
    period_ordinal: bool = False
    # A part of a compound word after its first part ("zwanzig" in "einundzwanzig").
    glued: bool = False

    @property
    def norm(self) -> str:
        return self.text.casefold()

    @property
    def digits(self) -> str:
        """A digit string without its ordinal suffix."""
        return self.text[:len(self.text) - len(self.suffix)].rstrip(".:") if self.suffix else self.text

    def links_to_previous(self) -> bool:
        """True when this token can continue a number that the previous
        token is part of: only a space or a hyphen lies between them."""
        return self.glued or self.gap == "-" or (self.gap != "" and self.gap.isspace())


def tokenize(text: str, ordinal_suffixes: frozenset[str] = frozenset(),
             lone_decimal_marks: frozenset[str] = frozenset(),
             abbreviations: frozenset[str] = frozenset(),
             number_words: frozenset[str] | None = None,
             compound_words: frozenset[str] = frozenset(),
             compound_inner: frozenset[str] = frozenset(),
             shared_letter: bool = False,
             suffix_marks: frozenset[str] = frozenset({"", "."}),
             period_ordinals: bool = False) -> list[Token]:
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

    Given ``compound_words``, a word that is no compound word itself but
    splits whole into them ("einundzwanzig") becomes one token per part. A
    word in ``compound_inner`` ("und") is never the first or last part.
    With ``shared_letter``, two parts may share a doubled letter ("ettusen").
    ``suffix_marks`` are the marks that may stand between a digit string and
    its ordinal suffix ("" in "21st", ":" in "3:e"). With ``period_ordinals``,
    a period between a digit string and the next word makes it an ordinal
    ("am 3. Mai"); the period is not part of the token.
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
            if (following.lastgroup == "word" and between in suffix_marks
                    and following.group().casefold() in ordinal_suffixes):
                end, suffix = following.end(), following.group()
                skip_until = following.end()
        if not is_digits and compound_words and match.group().casefold() not in compound_words:
            parts = _split_compound(match.group(), compound_words, compound_inner, shared_letter)
            if parts:
                for n, (a, b) in enumerate(parts):
                    tokens.append(Token(text[start + a:start + b], start + a, start + b, False,
                                        gap if n == 0 else "", glued=n > 0))
                previous_end = end
                continue
        period = (period_ordinals and is_digits and not suffix
                  and match.group().isdigit() and _period_ordinal(text, end))
        tokens.append(Token(text[start:end], start, end, is_digits, gap, suffix, period))
        previous_end = end
    return tokens if number_words is None else _drop_compound_nouns(text, tokens, number_words)


def _split_compound(word: str, parts: frozenset[str], inner: frozenset[str],
                    shared_letter: bool = False) -> list[tuple[int, int]]:
    """The offsets of the fewest parts that ``word`` splits into, each one in
    ``parts`` after case folding and no ``inner`` part at either end; [] when
    it splits in no way. Among splits with as many parts, the one with the
    longest last part wins. With ``shared_letter``, a part that ends in a
    double letter shares its last letter with the next part ("ettusen" is
    "ett" and "tusen"), so the two parts overlap by one letter."""
    longest = max(map(len, parts), default=0)
    # best[k]: the fewest parts that cover word[:k], as a list of offsets
    best: dict[int, list[tuple[int, int]]] = {0: []}
    for covered in range(len(word)):
        if covered not in best:
            continue
        starts = [covered]
        if shared_letter and covered >= 2 and word[covered - 1] == word[covered - 2]:
            starts.append(covered - 1)
        for start in starts:
            for end in range(min(len(word), start + longest), covered, -1):
                part = word[start:end].casefold()
                if part not in parts or (part in inner and (start == 0 or end == len(word))):
                    continue
                split = best[covered] + [(start, end)]
                if end not in best or len(split) < len(best[end]):
                    best[end] = split
    found = best.get(len(word), [])
    return found if len(found) > 1 else []


def _period_ordinal(text: str, end: int) -> bool:
    """True when a period follows the digits that end at ``end``, then one
    space, then a letter or a digit: "3. Mai", not "3." at a text end."""
    return text[end:end + 1] == "." and text[end + 1:end + 2].isspace() and \
        text[end + 2:end + 3].isalnum()


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
