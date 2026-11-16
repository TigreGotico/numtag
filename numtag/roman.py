"""Roman numerals: "Luís XIV", "século XIX", "World War II", "Ⅻ".

A numeral reads only where no number word or digit string does, so pt
"MIL" and fr "DIX" keep their word reading. The rules are in docs/api.md,
"Roman numerals"; the cue words and their sources are in each lexicon.
"""
import re
import unicodedata
from bisect import bisect_left

from numtag.lexicon import Lexicon
from numtag.mention import Kind, Reason
from numtag.tokenize import Token

# The standard subtractive form from 1 to 3999 ("IIII", "IC" and "VX" are
# no numeral). It is positional: each group writes one decimal digit.
_STANDARD = re.compile(r"(M{0,3})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})")
_UNITS = ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")
# The digit each group writes, thousands first: the letters for one, five
# and ten of each place stand where the units have I, V and X.
_PLACES = tuple(dict(zip((u.translate(str.maketrans("IVX", letters)) for u in _UNITS), "0123456789"))
                for letters in ("M\0\0", "CDM", "XLC", "IVX"))
# The Unicode Roman numeral characters (The Unicode Standard, chapter 22,
# "Number Forms"): U+2160 to U+217F stand for the letters, U+2180 to U+2188
# (except U+2183 and U+2184) are numerals with no letter form.
_NUMBER_FORMS = range(0x2160, 0x2189)
_NO_LETTER_FORM = {"\u2180": "1000", "\u2181": "5000", "\u2182": "10000", "\u2185": "6",
                   "\u2186": "50", "\u2187": "50000", "\u2188": "100000"}
_SENTENCE_END = re.compile(r"[.!?…]")
# A period after a word of one or two letters ends an abbreviation, not a
# sentence: "D. João", "Dr. Silva".
_ABBREVIATION_LENGTH = 2


def roman_value(word: str) -> str | None:
    """The value of a well-formed numeral in one case, as a digit string, or None."""
    if word in _NO_LETTER_FORM:
        return _NO_LETTER_FORM[word]
    if all(ord(c) in _NUMBER_FORMS for c in word):
        word = unicodedata.normalize("NFKC", word)
    if not word.isascii() or not (word.isupper() or word.islower()):
        return None
    match = _STANDARD.fullmatch(word.upper())
    if not match:
        return None
    return "".join(place[group] for place, group in zip(_PLACES, match.groups())).lstrip("0")


def _title_case(token: Token) -> bool:
    return token.text[:1].isupper() and any(c.islower() for c in token.text[1:])


def _first_in_sentence(tokens: list[Token], k: int) -> bool:
    if k == 0 or "\n" in tokens[k].gap:
        return True
    if not _SENTENCE_END.search(tokens[k].gap):
        return False
    before = tokens[k - 1].text
    return not ("." in tokens[k].gap and before[:1].isupper() and len(before) <= _ABBREVIATION_LENGTH)


def _spaced(tokens: list[Token], k: int) -> bool:
    """Only white space stands between token k and the one before it."""
    return k > 0 and tokens[k].gap.isspace()


def _list_item(tokens: list[Token], k: int, text: str) -> bool:
    """The numeral opens a line and a ")" or a "." closes it: "ii) …", "(iv) …", "iii. …"."""
    opens_line = (k == 0 or "\n" in tokens[k].gap) and tokens[k].gap.strip(" \t\n(") == ""
    after = text[tokens[k].end:tokens[k].end + 1]
    return opens_line and after in (")", ".")


def _cue(lexicon: Lexicon, tokens: list[Token], k: int, word: bool, upper: bool) -> bool:
    """True when the words around the numeral mark a place in a series.

    A series noun before it ("século XIX", "World War I") or, for a numeral
    that is no word, after it ("the XXI century"). A numeral that is no word
    also takes any title-case word before it ("Luís XIV", "Edition XIV").
    A single letter or a numeral that is also a word needs more: a regnal
    title before the name ("King Henry I", "D. João I"), or a name with a
    title-case word before it, neither of them first in the sentence
    ("Queen Elizabeth I"). "tell John I am late" gives no cue. A title-case
    word is no cue for a lower-case numeral: "Pokaż mi" holds no 1001."""
    before = tokens[k - 1] if _spaced(tokens, k) else None
    if before is not None and before.norm in lexicon.roman_series_nouns:
        return True
    if not word:
        after = tokens[k + 1] if k + 1 < len(tokens) and tokens[k + 1].gap.isspace() else None
        if after is not None and after.norm in lexicon.roman_series_nouns:
            return True
        return upper and before is not None and _title_case(before)
    if before is None or not _title_case(before) or k < 2 or _first_in_sentence(tokens, k - 1) \
            or _initial(tokens, k):
        return False
    title = tokens[k - 2]
    if title.norm in lexicon.roman_titles:
        return True
    return _title_case(title) and not _first_in_sentence(tokens, k - 2)


def _initial(tokens: list[Token], k: int) -> bool:
    """A capital letter before a name is an initial: "General D K Arya"."""
    after = tokens[k + 1] if k + 1 < len(tokens) and tokens[k + 1].gap.strip(". ") == "" else None
    return after is not None and (_title_case(after) or len(after.text) == 1 and after.text.isupper())


def _in_word(text: str, token: Token) -> bool:
    """An apostrophe and a letter after the numeral make it part of a word
    ("Xi'an"), unless they are the possessive "'s" ("Henry VIII's")."""
    after = text[token.end:token.end + 3]
    return after[:1] in "'’" and after[1:2].isalpha() and not (after[1:2] == "s" and not after[2:3].isalpha())


def _listed_after(lexicon: Lexicon, tokens: list[Token], k: int, cued: set[int]) -> bool:
    """The numeral follows a cued numeral in a list: "séculos XI, XII e XIII"."""
    if k > 0 and k - 1 in cued and tokens[k].gap.strip() == ",":
        return True
    return k > 1 and k - 2 in cued and tokens[k - 1].norm in lexicon.joiners \
        and tokens[k - 1].gap.strip() in ("", ",")


def roman_numerals(text: str, lexicon: Lexicon, tokens: list[Token],
                   taken: list[tuple[int, int]]) -> list[tuple[Token, str, Kind, Reason | None]]:
    """The Roman numerals among ``tokens`` outside the spans in ``taken``,
    which are in reading order and do not overlap: each token with its
    value, its kind and why it is not sure."""
    ends = [end for _, end in taken]
    numerals = []
    cued: set[int] = set()
    for k, token in enumerate(tokens):
        if token.is_digits or token.glued or k + 1 < len(tokens) and tokens[k + 1].glued or _in_word(text, token):
            continue
        # the first span that ends after the token starts is the only one that may cover it
        first = bisect_left(ends, token.start + 1)
        if first < len(taken) and taken[first][0] < token.end:
            continue
        value = roman_value(token.text)
        if not value:
            continue
        sure_form = all(ord(c) in _NUMBER_FORMS for c in token.text)
        word = not sure_form and (len(token.text) == 1 or token.norm in lexicon.roman_words)
        if word and not token.text.isupper():
            continue
        cue = _cue(lexicon, tokens, k, word, upper=token.text.isupper() or sure_form) \
            or _listed_after(lexicon, tokens, k, cued)
        if cue:
            cued.add(k)
        if word and not cue:
            continue
        if not (sure_form or cue or token.text.isupper() or _list_item(tokens, k, text)):
            continue
        numerals.append((token, value, Kind.ORDINAL if cue else Kind.CARDINAL,
                         None if sure_form or cue else Reason.HOMOGRAPH))
    return numerals
