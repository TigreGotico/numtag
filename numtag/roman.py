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
from numtag.tokenize import Token, fold

# The standard subtractive form from 1 to 3999 ("IIII", "IC" and "VX" are
# no numeral). It is positional: each group writes one decimal digit.
_STANDARD = re.compile(r"(M{0,3})(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})")
# The digit each group writes, thousands first.
_PLACES = tuple(dict(zip(groups, "0123456789")) for groups in (
    ("", "M", "MM", "MMM"),
    ("", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"),
    ("", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"),
    ("", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX")))
# The Unicode Roman numeral characters (The Unicode Standard, chapter 22,
# "Number Forms"): U+2160 to U+217F stand for the letters, U+2180 to U+2188
# (except U+2183 and U+2184) are numerals with no letter form.
_NUMBER_FORMS = range(0x2160, 0x2189)
_NO_LETTER_FORM = {"\u2180": "1000", "\u2181": "5000", "\u2182": "10000", "\u2185": "6",
                   "\u2186": "50", "\u2187": "50000", "\u2188": "100000"}
# A single letter is a numeral only as I, V or X: L, C, D and M alone are
# labels ("Part D", "Vitamin C").
_SINGLE_LETTERS = frozenset("IVX")


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


def _suffixed(lexicon: Lexicon, word: str) -> tuple[str, str | None] | None:
    """The value and the gender of an upper-case numeral glued to an ordinal
    suffix of the language in lower case ("XIXe", "Ier", "IIde"), where the
    language sets ``roman_ordinal_suffix``. The suffix keeps its lower case
    in upper-case text ("XXe SIÈCLE"), so the change of case ends the
    numeral. A single letter is I, V or X, as alone, and a numeral that is
    also a word takes no suffix ("MMe")."""
    numeral = word[:len(word) - len(word.lstrip("IVXLCDM"))]
    suffix = word[len(numeral):]
    if not (lexicon.roman_ordinal_suffix and numeral and suffix) or any(c.isupper() for c in suffix):
        return None
    if len(numeral) == 1 and numeral not in _SINGLE_LETTERS or fold(numeral) in lexicon.roman_words:
        return None
    value = roman_value(numeral)
    if value is None or not lexicon.ordinal_suffix_fits(suffix, value):
        return None
    return value, lexicon.ordinal_suffixes[fold(suffix)]


def _title_case(token: Token) -> bool:
    return token.text[:1].isupper() and any(c.islower() for c in token.text[1:])


def _spaced(tokens: list[Token], k: int) -> bool:
    """Only white space stands between token k and the one before it."""
    return k > 0 and tokens[k].gap.isspace()


def _list_item(tokens: list[Token], k: int, text: str) -> bool:
    """The numeral opens a line and a ")" or a "." closes it: "ii) …", "(iv) …", "iii. …"."""
    gap = tokens[k].gap
    opens_line = (k == 0 or "\n" in gap) and gap.rpartition("\n")[2].strip(" \t(") == ""
    after = text[tokens[k].end:tokens[k].end + 1]
    return opens_line and after in (")", ".")


def _cue(lexicon: Lexicon, tokens: list[Token], k: int, word: bool, upper: bool) -> bool:
    """True when the words around the numeral mark a place in a series.

    A series noun before it ("século XIX", "World War I") or, for a numeral
    that is no word, after it ("the XXI century"). Where a single letter
    may be a pronoun, the series noun before a word must be in title case:
    "Part I" reads, "the part I like" does not. A numeral that is no word
    also takes any title-case word before it ("Luís XIV", "Edition XIV"),
    in a language that does not write every noun in title case. Any
    numeral takes a regnal title before the name ("King Henry I", "D. João
    I", "Papst Benedikt XVI"); a single letter or a numeral that is also a
    word takes nothing else: "tell John I am late" and "I told Mary Jane I
    would come" give no cue. A title-case word is no cue for a lower-case
    numeral: "Pokaż mi" holds no 1001."""
    before = tokens[k - 1] if _spaced(tokens, k) else None
    if before is not None and before.norm in lexicon.roman_series_nouns:
        return not (word and lexicon.roman_pronoun_letters) or _title_case(before)
    if not word:
        # a German ordinal period may stand between: "im XIX. Jahrhundert"
        gaps = {"", "."} if lexicon.period_ordinals else {""}
        after = tokens[k + 1] if k + 1 < len(tokens) and tokens[k + 1].gap.strip() in gaps \
            and tokens[k + 1].gap[-1:].isspace() else None
        if after is not None and after.norm in lexicon.roman_series_nouns:
            return True
        if upper and lexicon.roman_title_case_cue and before is not None and _title_case(before):
            return True
    return before is not None and "\n" not in tokens[k].gap and _regnal(lexicon, tokens, k) \
        and not (word and _initial(tokens, k))


def _regnal(lexicon: Lexicon, tokens: list[Token], k: int) -> bool:
    """A regnal title, then a name of one or two title-case words, before
    token k on one line: "King Henry I", "Pope John Paul I", "D. João I".
    Only a one-letter title ends in a period ("D."); "the King. Then I"
    is two sentences."""
    for words in (1, 2):
        first = k - words
        name = tokens[first:k]
        if first < 1 or not all(_title_case(t) for t in name):
            return False
        title, title_gap = tokens[first - 1], name[0].gap
        joined = title_gap.isspace() or title_gap.strip() == "." and len(title.text) == 1
        if title.norm in lexicon.roman_titles and joined and "\n" not in title_gap \
                and all(t.gap.isspace() and "\n" not in t.gap for t in name[1:]):
            return True
    return False


def _initial(tokens: list[Token], k: int) -> bool:
    """A capital letter before a name or another capital is an initial:
    "General D K Arya", "D. K. Arya". A period before a title-case word
    ends the sentence: "Queen Elizabeth I. Then"."""
    if k + 1 == len(tokens):
        return False
    after, gap = tokens[k + 1], tokens[k + 1].gap
    if len(after.text) == 1 and after.text.isupper():
        return gap.strip(". ") == ""
    return gap.isspace() and _title_case(after)


def _in_word(text: str, token: Token) -> bool:
    """A digit beside the numeral, or an apostrophe and a letter after it,
    make it part of a code or a word ("CX5", "2XL", "Xi'an"), unless they
    are the possessive "'s" ("Henry VIII's")."""
    if text[token.start - 1:token.start].isdigit() or text[token.end:token.end + 1].isdigit():
        return True
    after = text[token.end:token.end + 3]
    return after[:1] in "'’" and after[1:2].isalpha() and not (after[1:2] == "s" and not after[2:3].isalpha())


def _listed_after(lexicon: Lexicon, tokens: list[Token], k: int, cued: set[int]) -> bool:
    """The numeral follows a cued numeral in a list: "séculos XI, XII e XIII"."""
    if k > 0 and k - 1 in cued and tokens[k].gap.strip() == ",":
        return True
    return k > 1 and k - 2 in cued and tokens[k - 1].norm in lexicon.joiners \
        and tokens[k - 1].gap.strip() in ("", ",")


def roman_numerals(text: str, lexicon: Lexicon, tokens: list[Token],
                   taken: list[tuple[int, int]]) -> list[tuple[Token, str, Kind, Reason | None, str | None]]:
    """The Roman numerals among ``tokens`` outside the spans in ``taken``,
    which are in reading order and do not overlap: each token with its
    value, its kind, why it is not sure and the gender of its suffix."""
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
        if suffixed := _suffixed(lexicon, token.text):
            # the suffix makes the place in a series: "au XXe siècle", "François Ier"
            cued.add(k)
            numerals.append((token, suffixed[0], Kind.ORDINAL, None, suffixed[1]))
            continue
        value = roman_value(token.text)
        if not value:
            continue
        sure_form = all(ord(c) in _NUMBER_FORMS for c in token.text)
        if not sure_form and len(token.text) == 1 and token.text.upper() not in _SINGLE_LETTERS:
            continue
        word = not sure_form and (len(token.text) == 1 or token.norm in lexicon.roman_words
                                  or token.text.islower() and token.norm in lexicon.roman_lower_words)
        if word and not token.text.isupper():
            continue
        # a word in a list is no numeral by its place: "World War I, I moved"
        cue = _cue(lexicon, tokens, k, word, upper=token.text.isupper() or sure_form) \
            or not word and _listed_after(lexicon, tokens, k, cued)
        if cue:
            cued.add(k)
        if word and not cue:
            continue
        if not (sure_form or cue or token.text.isupper() or _list_item(tokens, k, text)):
            continue
        numerals.append((token, value, Kind.ORDINAL if cue else Kind.CARDINAL,
                         None if sure_form or cue else Reason.HOMOGRAPH, None))
    return numerals
