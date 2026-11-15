"""Split a text into words and digit strings, each with its character offsets."""
import re
import unicodedata
from dataclasses import dataclass, field, replace
from functools import cache

_ASCII_DIGITS = re.compile(r"(?:[-−][.,]?|[.,])?[0-9]+(?:[.,][0-9]+)*")
_LONE_MARK = re.compile(r"[.,][0-9]+")
_TRAILING_MARK = re.compile(r"\D+$")
_WORD = re.compile(r"[^\W\d_]+")
# A soft hyphen (U+00AD) inside a word marks where a line may break; it
# is no break in the word ("huszon\u00adöt").
SOFT_HYPHEN = "\u00ad"
_NEXT_WORD = re.compile(r"\.\s([^\W\d_]+)")
_PREVIOUS_WORD = re.compile(r"([^\W\d_]+)\s+$")


@dataclass(frozen=True)
class PeriodCues:
    """What makes a period after digits an ordinal mark rather than a
    sentence end: a word before the digits ("zum 1000. Mal"), with
    ``lowercase`` any lower-case word after the period ("17. mai"), and a
    number of at most ``free_digits`` digits with no cue ("3. Platz", where
    every noun takes a capital)."""
    before: frozenset[str] = frozenset()
    lowercase: bool = False
    free_digits: int = 0


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
    minus sign or a lone mark belongs to it only at the start of a word ("-5",
    ".5" and "-.5", not "5-7" or "...5"). The pattern takes digits of every script,
    so that a run with a digit the language does not read ("٣", "１２") is
    found whole and then dropped. A soft hyphen between letters stays in
    the word."""
    marks = ".," + "".join(re.escape(n) for n, a in script.native_digits if not a.isdigit())
    word = r"[^\W\d_]"
    if script.fold_marks or script.word_chars:
        inner = (_combining_marks() if script.fold_marks else "") + re.escape(script.word_chars)
        word = rf"{word}(?:[^\W\d_]|[{inner}]|{SOFT_HYPHEN}[^\W\d_])*"
    else:
        word = rf"{word}+(?:{SOFT_HYPHEN}[^\W\d_]+)*"
    return re.compile(rf"(?P<digits>(?:(?<![^\s(\[])(?:[-−][{marks}]?|[{marks}]))?\d+(?:[{marks}]\d+)*)|(?P<word>{word})")


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
    # A part of a compound word after its first part, with no space before
    # it ("kymmentä" in "kaksikymmentä", "zwanzig" in "einundzwanzig").
    glued: bool = False
    # The lower-case form where the language folds case in its own way.
    folded: str = ""
    # A digit string that a period makes an ordinal ("3" in "am 3. Mai").
    period_ordinal: bool = False

    @property
    def norm(self) -> str:
        if self.key is not None:
            return self.key
        return self.folded or self.text.casefold()

    @property
    def latin(self) -> str:
        """A digit string in ASCII digits and the locale's marks."""
        return self.text if self.key is None else self.key

    @property
    def digits(self) -> str:
        """A digit string without its ordinal suffix and the mark before it."""
        latin = self.latin
        if not self.suffix or not latin.endswith(self.suffix):
            return latin
        return _TRAILING_MARK.sub("", latin[:len(latin) - len(self.suffix)])

    def links_to_previous(self) -> bool:
        """True when this token can continue a number that the previous
        token is part of: only a space or a hyphen lies between them, or the
        token is glued to a joiner prefix or to the part of a compound word
        before it. A word with a clitic prefix and no joiner prefix links to
        nothing before it."""
        if self.attached or self.glued:
            return True
        return not self.clitic and (self.gap == "-" or (self.gap != "" and self.gap.isspace()))


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
             number_words: frozenset[str] | None = None,
             script: Script = DEFAULT_SCRIPT, *,
             compound_words: frozenset[str] = frozenset(),
             compound_inner: frozenset[str] = frozenset(),
             shared_letter: bool = False,
             dotted_i: bool = False,
             suffix_marks: frozenset[str] = frozenset({"", "."}),
             digit_suffix_marks: frozenset[str] = frozenset(),
             period_ordinals: PeriodCues | None = None,
             dot_ordinal: bool = False, date_months: frozenset[str] = frozenset()) -> list[Token]:
    """Words and digit strings of ``text``; punctuation only shows in gaps.

    A word glued to a digit string is its ordinal suffix when the language
    lists it, after an optional dot ("1.º"). A digit string glued to the end
    of a word ("mp3") is part of a name and is dropped, and so is a digit
    string with a digit that the script does not read. A digit string keeps a
    mark before its first digit, also after a sign, only when the language
    lists the mark as a lone decimal mark and only digits follow it (".5",
    "-.5"). An abbreviation is a listed word with a period that no sentence
    end follows ("dez. 2025"); it is dropped, so it breaks the link between
    the words around it. Given ``number_words``, a hyphenated compound with a
    word outside them is one noun ("segunda-feira"): its words are dropped in
    the same way; and a word outside them loses a prefix of the script when
    the rest is a number word.

    Given ``compound_words``, a word that is no compound word itself but
    splits whole into them ("einundzwanzig", "kaksikymmentä") becomes one
    token per part, each glued to the one before. A word in
    ``compound_inner`` ("und") is never the first or last part. With
    ``shared_letter``, two parts may share a doubled letter ("ettusen").
    ``suffix_marks`` are the marks that may stand between a digit string and
    its ordinal suffix ("" in "21st", ":" in "3:e"). A word after one of
    ``digit_suffix_marks`` right after a digit string is its ordinal suffix
    or else its case ending, which is dropped ("5'inci", "5-öt").

    With ``period_ordinals``, a period between a digit string and the next
    word makes it an ordinal when one of the cues shows it ("am 3. Mai", not
    "in 1905. Dann"). With ``dot_ordinal``, a period after a digit string
    makes it an ordinal when a lower-case word or a digit follows ("2.
    emelet"); before one of ``date_months`` the period follows the year of a
    date, which is no ordinal ("2008. február"). In both cases the period is
    not part of the token.
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
        unsigned = latin.lstrip("-−")
        if is_digits and unsigned[0] in ".," and not (
                unsigned[0] in lone_decimal_marks and _LONE_MARK.fullmatch(unsigned)):
            cut = len(latin) - len(unsigned) + 1
            start += cut
            latin = latin[cut:]
        gap = scan[previous_end:start]
        if is_digits and gap == "" and tokens and not tokens[-1].is_digits:
            previous_end = match.end()
            continue
        if not is_digits and tokens and tokens[-1].is_digits and not tokens[-1].suffix \
                and gap in digit_suffix_marks and tokens[-1].end == previous_end:
            continue  # a case ending glued to digits: "5-öt", "5'te"
        end, suffix = match.end(), ""
        if is_digits and index + 1 < len(matches):
            following = matches[index + 1]
            between = scan[match.end():following.start()]
            if (following.lastgroup == "word" and (between in suffix_marks or between in digit_suffix_marks)
                    and following.group().casefold() in ordinal_suffixes):
                end, suffix = following.end(), following.group()
                latin += text[match.end():end]
                skip_until = following.end()
        if is_digits and dot_ordinal and not suffix and _dot_ordinal(text, end, date_months):
            suffix = "."  # the period stays outside the span, as punctuation
        word = text[start:end]
        letters = word.replace(SOFT_HYPHEN, "")
        folded = "" if is_digits else fold_dotted_i(letters) if dotted_i else \
            letters.casefold() if letters != word else ""
        lookup = folded or word.casefold()
        # the offset in the text of each letter of the word
        offsets = [start + k for k, char in enumerate(word) if char != SOFT_HYPHEN]
        parts = []
        if compound_words and not is_digits and lookup not in compound_words:
            source = fold_dotted_i(letters) if dotted_i else letters
            if len(source) == len(offsets):
                parts = _split_compound(source, compound_words, compound_inner, shared_letter)
        if parts:
            for n, (a, b) in enumerate(parts):
                first, last = offsets[a], offsets[b - 1] + 1
                piece = text[first:last]
                tokens.append(Token(piece, first, last, False, gap if n == 0 else "",
                                    key=None if script == DEFAULT_SCRIPT else script.fold(piece),
                                    glued=n > 0, folded=source[a:b].casefold()))
        else:
            key = None
            if script != DEFAULT_SCRIPT:
                key = latin if is_digits else script.fold(letters)
            period = (period_ordinals is not None and is_digits and not suffix
                      and match.group().isdigit() and _period_ordinal(text, start, end, period_ordinals))
            tokens.append(Token(word, start, end, is_digits, gap, suffix, key=key, folded=folded,
                                period_ordinal=period))
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


def _period_ordinal(text: str, start: int, end: int, cues: PeriodCues) -> bool:
    """True when a period, one space and a word follow the digits from
    ``start`` to ``end``, and a cue shows the period marks an ordinal: "am
    3. Mai", "17. mai", not "i 1905. Dette" or "3." at a text end."""
    after = _NEXT_WORD.match(text, end)
    if after is None:
        return False
    word = after.group(1)
    if end - start <= cues.free_digits or (cues.lowercase and word[0].islower()):
        return True
    before = _PREVIOUS_WORD.search(text, max(0, start - 64), start)
    return before is not None and before.group(1).casefold() in cues.before


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
