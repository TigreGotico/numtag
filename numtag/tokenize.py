"""Split a text into words and digit strings, each with its character offsets."""
import re
from dataclasses import dataclass, replace
from functools import cache

# A digit string keeps its group and decimal marks ("1.000.000,5"). A minus
# sign or a lone mark belongs to it only at the start of a word ("-5" and
# ".5", not "5-7" or "...5"). The pattern takes digits of every script, so
# that a run with any digit outside 0-9 ("٣", "１２") is found whole and then
# dropped.
_LONE_MARK = re.compile(r"[.,][0-9]+")


@cache
def _patterns(group_mark: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    """The token pattern and the pattern of a digit string in 0-9. A group
    mark other than "." and "," ("1'234'567" in Switzerland) also stands
    between digits."""
    inner = "[.," + (re.escape(group_mark) if group_mark not in ".," else "") + "]"
    return (re.compile(rf"(?P<digits>(?:(?<![^\s(\[])(?:[-−][.,]?|[.,]))?\d+(?:{inner}\d+)*)|(?P<word>[^\W\d_]+)"),
            re.compile(rf"(?:[-−][.,]?|[.,])?[0-9]+(?:{inner}[0-9]+)*"))


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
    # The form the lexicon knows the word by, when it is not the case-folded
    # text: a folded letter ("şase"), or a number word of several words
    # ("quatre-vingts" for "quatre vingts").
    key: str = ""
    # A piece of a word that the tokenizer split ("venti" and "tré" in
    # "ventitré"); ``joined`` when the piece goes on the word of the token
    # before it.
    part: bool = False
    joined: bool = False

    @property
    def norm(self) -> str:
        return self.key or self.text.casefold()

    @property
    def digits(self) -> str:
        """A digit string without its ordinal suffix."""
        return self.text[:len(self.text) - len(self.suffix)].rstrip(".") if self.suffix else self.text

    def links_to_previous(self) -> bool:
        """True when this token can continue a number that the previous
        token is part of: only a space or a hyphen lies between them, or the
        two are pieces of one word."""
        return self.joined or self.gap == "-" or (self.gap != "" and self.gap.isspace())


def tokenize(text: str, ordinal_suffixes: frozenset[str] = frozenset(),
             lone_decimal_marks: frozenset[str] = frozenset(),
             abbreviations: frozenset[str] = frozenset(),
             number_words: frozenset[str] | None = None, *,
             fold: dict[str, str] | None = None,
             phrases: frozenset[tuple[str, ...]] = frozenset(),
             split: frozenset[str] = frozenset(), group_mark: str = ".") -> list[Token]:
    """Words and digit strings of ``text``; punctuation only shows in gaps.

    A word glued to a digit string is its ordinal suffix when the language
    lists it, after an optional dot ("1.º"), or after a hyphen when the
    language lists it with one ("2-lea"). A digit string glued to the end
    of a word ("mp3") is part of a name and is dropped, and so is a digit
    string with a digit outside 0-9. A digit string keeps a mark before its
    first digit, also after a sign, only when the language lists the mark as
    a lone decimal mark and only digits follow it (".5", "-.5"). An abbreviation is a listed word with a
    period that no sentence end follows ("dez. 2025"); it is dropped, so it
    breaks the link between the words around it. Given ``number_words``, a
    hyphenated compound with a word outside them is one noun
    ("segunda-feira"): its words are dropped in the same way.

    ``fold`` maps letters to the letters the lexicon uses ("ş" to "ș").
    A word outside ``number_words`` that is a run of the words in ``split``
    is split into them ("ventitré" is "venti" and "tré"). The words of
    each phrase in ``phrases`` become one token ("quatre-vingts").
    ``group_mark`` joins digits as "." and "," do ("1'234").
    """
    token_pattern, ascii_digits = _patterns(group_mark)
    tokens: list[Token] = []
    previous_end = 0
    matches = list(token_pattern.finditer(text))
    skip_until = -1
    for index, match in enumerate(matches):
        if match.start() < skip_until:
            continue
        is_digits = match.lastgroup == "digits"
        if is_digits and not ascii_digits.fullmatch(match.group()):
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
            # a suffix listed with a hyphen ("-lea") takes one ("2-lea")
            word = following.group() if between in ("", ".") else between + following.group()
            if following.lastgroup == "word" and between in ("", ".", "-") and word.casefold() in ordinal_suffixes:
                end, suffix = following.end(), word
                skip_until = following.end()
        token = Token(text[start:end], start, end, is_digits, gap, suffix)
        if fold and not is_digits:
            token = replace(token, key=token.text.casefold().translate(str.maketrans(fold)))
        tokens.append(token)
        previous_end = end
    if number_words is None:
        return tokens
    if split:
        tokens = [piece for token in tokens for piece in _split(token, number_words, split)]
    if phrases:
        tokens = _merge_phrases(text, tokens, phrases)
    return _drop_compound_nouns(text, tokens, number_words)


def _split(token: Token, number_words: frozenset[str], parts: frozenset[str]) -> list[Token]:
    """The pieces of a word that is a run of ``parts``, with the fewest
    pieces; the word itself when it is a number word or no such run."""
    word = token.norm
    if token.is_digits or word in number_words or len(word) != len(token.text):
        return [token]
    # best[k]: the fewest pieces that spell word[:k], as the piece ends
    best: dict[int, tuple[int, ...]] = {0: ()}
    for start in range(len(word)):
        if start not in best:
            continue
        for end in range(start + 1, len(word) + 1):
            if word[start:end] in parts and (
                    end not in best or len(best[start]) + 1 < len(best[end])):
                best[end] = best[start] + (end,)
    ends = best.get(len(word), ())
    if len(ends) < 2:
        return [token]
    pieces, start = [], 0
    for n, end in enumerate(ends):
        pieces.append(Token(token.text[start:end], token.start + start, token.start + end, False,
                            token.gap if n == 0 else "", key=word[start:end], part=True, joined=n > 0))
        start = end
    return pieces


def _merge_phrases(text: str, tokens: list[Token], phrases: frozenset[tuple[str, ...]]) -> list[Token]:
    """The tokens with the words of each phrase made one token, longest
    phrase first, when only spaces or hyphens lie between the words."""
    longest = max(len(p) for p in phrases)
    merged: list[Token] = []
    i = 0
    while i < len(tokens):
        for size in range(min(longest, len(tokens) - i), 1, -1):
            words = tokens[i:i + size]
            if (tuple(t.norm for t in words) in phrases and not any(t.is_digits or t.part for t in words)
                    and all(t.links_to_previous() for t in words[1:])):
                first, last = words[0], words[-1]
                merged.append(replace(first, text=text[first.start:last.end], end=last.end,
                                      key="-".join(t.norm for t in words)))
                i += size
                break
        else:
            merged.append(tokens[i])
            i += 1
    return merged


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
