"""Split a text into words and digit strings, each with its character offsets."""
import re
import unicodedata
from dataclasses import dataclass, field, replace
from functools import cache

_ASCII_DIGITS = re.compile(r"[-−.,]?[0-9]+(?:[.,][0-9]+)*")
_LONE_MARK = re.compile(r"[.,][0-9]+")
# Directional marks and embedding controls: no letter, so a script that sets
# them aside reads each as a space ("‏٣" is "٣").
BIDI_CONTROLS = "؜‎‏‪‫‬‭‮⁦⁧⁨⁩"


def _combining_marks() -> str:
    """A character class body with every combining mark of the Basic Multilingual Plane."""
    ranges: list[list[int]] = []
    for code in range(0x300, 0x10000):
        if unicodedata.category(chr(code)).startswith("M"):
            if ranges and ranges[-1][1] == code - 1:
                ranges[-1][1] = code
            else:
                ranges.append([code, code])
    return "".join(f"{chr(a)}-{chr(b)}" if a != b else chr(a) for a, b in ranges)


@dataclass(frozen=True)
class Script:
    """How a language's script is read. The defaults read text as pt and en do."""
    # Combining marks (harakat, niqqud, tonos, dots below) belong to the word
    # they follow and are ignored when a word is looked up. With "unmarked",
    # only a word written with no mark at all is read without its marks: in
    # el "εκτός" (except) stays apart from "έκτος" (sixth), while "εικοσι"
    # typed without accents still reads as "είκοσι".
    fold_marks: bool | str = False
    # Marks that are part of a letter and stay when the other marks go: the
    # hamza of ar "أ", which sets "وأحد" (and eleven) apart from "واحد" (one).
    kept_marks: str = ""
    # Letters that read as another letter for lookup ("ي" as "ی" in fa).
    letter_folds: tuple[tuple[str, str], ...] = ()
    # Characters that stand inside a word: the zero-width non-joiner of fa.
    word_chars: str = ""
    # Bidi controls read as spaces.
    bidi_controls: bool = False
    # Native digits and digit marks, each with the ASCII digit or the
    # locale's own mark it reads as ("٣" as "3", "٫" as ".").
    native_digits: tuple[tuple[str, str], ...] = ()
    # A prefix glued to a number word that is the joiner ("و" in "وعشرون").
    joiner_prefixes: tuple[str, ...] = ()
    # A prefix glued to a number word that is no part of the number: an
    # article or a preposition ("ال" in "الثالث", "ב" in "בשלושה").
    clitic_prefixes: tuple[str, ...] = ()
    # The fewest letters a word keeps after a clitic prefix comes off.
    clitic_min_rest: int = 1

    def fold(self, word: str) -> str:
        """The lookup form of a word in a text."""
        return self._fold(word, strip=self.fold_marks is True)

    def lexicon_forms(self, word: str) -> set[str]:
        """The lookup forms of a lexicon word: with "unmarked", the word as
        written and the word without its marks."""
        return {self.fold(word), self._fold(word, strip=bool(self.fold_marks))}

    def _fold(self, word: str, strip: bool) -> str:
        word = word.casefold()
        if strip:
            word = "".join(c for c in unicodedata.normalize("NFD", word)
                           if c in self.kept_marks or not unicodedata.category(c).startswith("M"))
        if self.fold_marks:
            word = unicodedata.normalize("NFC", word)
        for old, new in self.letter_folds:
            word = word.replace(old, new)
        for char in self.word_chars:
            word = word.replace(char, "")
        return word

    @property
    def digit_table(self) -> dict[int, str]:
        return {ord(native): ascii_ for native, ascii_ in self.native_digits}


DEFAULT_SCRIPT = Script()


@cache
def _token_pattern(script: Script) -> re.Pattern:
    """A digit string keeps its group and decimal marks ("1.000.000,5"). A
    minus sign or a lone mark belongs to it only at the start of a word ("-5"
    and ".5", not "5-7" or "...5"). The pattern takes digits of every script,
    so that a run with a digit the language does not read ("٣", "１２") is
    found whole and then dropped."""
    marks = ".," + "".join(re.escape(n) for n, a in script.native_digits if not a.isdigit())
    word = r"[^\W\d_]"
    if script.fold_marks or script.word_chars:
        inner = (_combining_marks() if script.fold_marks else "") + re.escape(script.word_chars)
        word = rf"{word}(?:[^\W\d_]|[{inner}])*"
    else:
        word += "+"
    return re.compile(rf"(?P<digits>(?:(?<![^\s(\[])[-−{marks}])?\d+(?:[{marks}]\d+)*)|(?P<word>{word})")


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
    # The lookup form when it is not the case-folded text: the folded word
    # without its clitic prefix, or a digit string in ASCII digits.
    key: str | None = field(default=None, compare=False)
    # Glued to the previous token: the word after a joiner prefix.
    attached: bool = False
    # Read without a clitic prefix: a preposition or an article opens a
    # number and never stands inside one ("خمسة بالمائة" is two numbers).
    clitic: bool = False

    @property
    def norm(self) -> str:
        return self.text.casefold() if self.key is None else self.key

    @property
    def latin(self) -> str:
        """A digit string in ASCII digits and the locale's marks."""
        return self.text if self.key is None else self.key

    @property
    def digits(self) -> str:
        """A digit string without its ordinal suffix."""
        latin = self.latin
        return latin[:len(latin) - len(self.suffix)].rstrip(".") if self.suffix else latin

    def links_to_previous(self) -> bool:
        """True when this token can continue a number that the previous
        token is part of: only a space or a hyphen lies between them, or the
        token is glued to a joiner prefix. A word with a clitic prefix and
        no joiner prefix links to nothing before it."""
        if self.attached:
            return True
        return not self.clitic and (self.gap == "-" or (self.gap != "" and self.gap.isspace()))


def tokenize(text: str, ordinal_suffixes: frozenset[str] = frozenset(),
             lone_decimal_marks: frozenset[str] = frozenset(),
             abbreviations: frozenset[str] = frozenset(),
             number_words: frozenset[str] | None = None,
             script: Script = DEFAULT_SCRIPT) -> list[Token]:
    """Words and digit strings of ``text``; punctuation only shows in gaps.

    A word glued to a digit string is its ordinal suffix when the language
    lists it, after an optional dot ("1.º"). A digit string glued to the end
    of a word ("mp3") is part of a name and is dropped, and so is a digit
    string with a digit that the script does not read. A digit string keeps a
    mark before its first digit only when the language lists the mark as a
    lone decimal mark and only digits follow it (".5"). An abbreviation is a
    listed word with a period that no sentence end follows ("dez. 2025"); it
    is dropped, so it breaks the link between the words around it. Given
    ``number_words``, a hyphenated compound with a word outside them is one
    noun ("segunda-feira"): its words are dropped in the same way; and a word
    outside them loses a prefix of the script when the rest is a number word.
    """
    scan = text
    if script.bidi_controls:
        scan = text.translate({ord(c): " " for c in BIDI_CONTROLS})
    table = script.digit_table
    tokens: list[Token] = []
    previous_end = 0
    matches = list(_token_pattern(script).finditer(scan))
    skip_until = -1
    for index, match in enumerate(matches):
        if match.start() < skip_until:
            continue
        is_digits = match.lastgroup == "digits"
        latin = match.group().translate(table) if is_digits else ""
        if is_digits and not (_ASCII_DIGITS.fullmatch(latin) and _one_digit_script(match.group(), table)):
            continue
        if not is_digits and match.group().casefold() in abbreviations and _abbreviated(scan, match.end()):
            continue
        start = match.start()
        if is_digits and latin[0] in ".," and not (
                latin[0] in lone_decimal_marks and _LONE_MARK.fullmatch(latin)):
            start += 1
            latin = latin[1:]
        gap = scan[previous_end:start]
        if is_digits and gap == "" and tokens and not tokens[-1].is_digits:
            previous_end = match.end()
            continue
        end, suffix = match.end(), ""
        if is_digits and index + 1 < len(matches):
            following = matches[index + 1]
            between = scan[match.end():following.start()]
            if (following.lastgroup == "word" and between in ("", ".")
                    and following.group().casefold() in ordinal_suffixes):
                end, suffix = following.end(), following.group()
                latin += text[match.end():end]
                skip_until = following.end()
        key = None
        if script != DEFAULT_SCRIPT:
            key = latin if is_digits else script.fold(text[start:end])
        tokens.append(Token(text[start:end], start, end, is_digits, gap, suffix, key))
        previous_end = end
    if number_words is None:
        return tokens
    if script.joiner_prefixes or script.clitic_prefixes:
        tokens = _split_prefixes(tokens, number_words, script)
    return _drop_compound_nouns(text, tokens, number_words)


def _one_digit_script(run: str, table: dict[int, str]) -> bool:
    """True when the digits of ``run`` are all ASCII or all native."""
    digits = [c for c in run if c.isdigit()]
    return all(c in "0123456789" for c in digits) or all(ord(c) in table for c in digits)


def _strip_clitic(key: str, number_words: frozenset[str], script: Script) -> str | None:
    """The number word left when a clitic prefix comes off ``key``."""
    for prefix in sorted(script.clitic_prefixes, key=len, reverse=True):
        rest = key[len(prefix):]
        if key.startswith(prefix) and len(rest) >= script.clitic_min_rest and rest in number_words:
            return rest
    return None


def _split_prefixes(tokens: list[Token], number_words: frozenset[str], script: Script) -> list[Token]:
    """Each word that is no number word but holds one after a prefix: a
    joiner prefix becomes a joiner token of its own, with the rest of the
    word glued to it ("وعشرون" is "و" and "عشرون"); a clitic prefix stays in
    the text of the word and leaves its lookup ("الثالث" reads "ثالث")."""
    found: list[Token] = []
    for token in tokens:
        if token.is_digits or token.norm in number_words:
            found.append(token)
            continue
        split = _joiner_split(token, number_words, script)
        if split:
            joiner, rest = split
            stripped = rest.norm if rest.norm in number_words else _strip_clitic(rest.norm, number_words, script)
            found += [joiner, replace(rest, key=stripped)]
            continue
        stripped = _strip_clitic(token.norm, number_words, script)
        found.append(token if stripped is None else replace(token, key=stripped, clitic=True))
    return found


def _joiner_split(token: Token, number_words: frozenset[str], script: Script) -> tuple[Token, Token] | None:
    """The joiner prefix and the rest of ``token`` when the rest is a number
    word, with or without a clitic prefix. The marks on the prefix letter go
    with the prefix ("وَ")."""
    for cut in range(len(token.text) - 1, 0, -1):
        head, rest = token.text[:cut], token.text[cut:]
        if script.fold(head) not in script.joiner_prefixes or unicodedata.category(rest[0]).startswith("M"):
            continue
        key = script.fold(rest)
        if key in number_words or _strip_clitic(key, number_words, script):
            middle = token.start + cut
            return (replace(token, text=head, end=middle, key=script.fold(head)),
                    Token(rest, middle, token.end, False, "", key=key, attached=True))
    return None


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
