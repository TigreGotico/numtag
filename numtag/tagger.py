"""Find the numbers of a text: the leftmost longest reading at each position."""
from numtag.grammar import Grammar, Parse
from numtag.lexicon import CARDINAL_ROLES, Lexicon, Scale, load
from numtag.mention import Form, Kind, NumberMention
from numtag.tokenize import Token, tokenize

# A weak number: an article alone before a noun, or a word with a common
# meaning that is no number. Scores are deterministic, not probabilities.
ARTICLE_CONFIDENCE = 0.3
AMBIGUOUS_CONFIDENCE = 0.4


def lexicon_name(lang: str) -> str:
    """The lexicon file for a language tag: "pt-br" reads pt-BR, every other
    "pt" tag pt-PT, and every "en" tag en."""
    parts = lang.replace("_", "-").split("-")
    primary, region = parts[0].lower(), (parts[1].upper() if len(parts) > 1 else "")
    if primary == "pt":
        return "pt-BR" if region == "BR" else "pt-PT"
    return primary


def tag_numbers(text: str, lang: str, *, scale: Scale | None = None) -> list[NumberMention]:
    """Every non-overlapping number in ``text``, in reading order."""
    lexicon = load(lexicon_name(lang), Scale(scale) if scale else None)
    tokens = tokenize(text, frozenset(lexicon.ordinal_suffixes), lexicon.lone_decimal_marks,
                      lexicon.abbreviations, frozenset(lexicon.readings) | lexicon.joiners,
                      compound_words=frozenset(lexicon.readings) if lexicon.compound_words else frozenset(),
                      dotted_i=lexicon.dotted_i, digit_suffix_marks=lexicon.digit_suffix_marks,
                      dot_ordinal=lexicon.dot_ordinal, date_months=lexicon.date_months)
    mentions: list[NumberMention] = []
    for run in _runs(tokens):
        mentions += _tag_run(text, lexicon, run)
    return mentions


def _runs(tokens: list[Token]) -> list[list[Token]]:
    """Stretches of tokens with only spaces or hyphens between them: a
    number never crosses punctuation."""
    runs: list[list[Token]] = []
    for token in tokens:
        if runs and token.links_to_previous():
            runs[-1].append(token)
        else:
            runs.append([token])
    return runs


def _tag_run(text: str, lexicon: Lexicon, run: list[Token]) -> list[NumberMention]:
    grammar = Grammar(lexicon, run)
    mentions = []
    i = 0
    while i < len(run):
        negative = _is_minus(grammar, lexicon, run, i)
        start = i + 1 if negative else i
        parses = [p for p in grammar.numbers(start) if _whole_words(grammar, run, start, p)]
        # a number starts and ends at the edges of a word, never inside one
        if not parses or run[i].glued:
            i += 1
            continue
        best = max(parses, key=lambda p: p.end)
        value = -best.value if negative else best.value
        span = (run[i].start, run[best.end - 1].end)
        mentions.append(NumberMention(
            span, text[span[0]:span[1]], value.canonical(), _kind(lexicon, run[start:best.end], best),
            _form(run[start:best.end]), _gender(lexicon, run[start:best.end]),
            _confidence(grammar, lexicon, run, start, best),
            number_scale=_number_scale(lexicon, run[start:best.end])))
        i = best.end
    return mentions


def _is_minus(grammar: Grammar, lexicon: Lexicon, run: list[Token], i: int) -> bool:
    """A minus word that starts a number: not after a number ("cinco menos
    dois"), not inside an idiom ("pelo menos dois") and not at the end of a
    run ("Quero menos.")."""
    if i + 1 == len(run) or run[i].is_digits or run[i].norm not in lexicon.minus_words:
        return False
    if i > 0 and grammar.starts_number(i - 1):
        return False
    words = [t.norm for t in run[:i + 1]]
    return not any(tuple(words[-len(idiom):]) == idiom for idiom in lexicon.minus_idioms)


def _whole_words(grammar: Grammar, run: list[Token], start: int, parse: Parse) -> bool:
    """True when the tokens of ``parse`` from ``start`` end at the edge of a
    word, and no form before the last one closes the number with a case
    ending ("yüzde" ends its number, so "yüzde elli" is no 150), except the
    form that names the parts of a fraction ("üçte bir")."""
    end = parse.end
    if end < len(run) and run[end].glued:
        return False
    return not any(grammar.closes(k) for k in range(start, end - 1) if k != parse.parts_at)


def _ordinal_word(lexicon: Lexicon, tokens: list[Token]) -> bool:
    """True when the last word of a number has an ordinal form among its
    readings. A form that is both an ordinal and a case of a cardinal reads
    as the ordinal (Estonian "viies" is "fifth" and "in five"). A teen
    with no ordinal form ("toista" in "yhdestoista") leaves the choice to
    the unit before it."""
    last = tokens[-1]
    if last.is_digits:
        return False
    entries = [e for e in lexicon.readings.get(last.norm, ()) if e.role in CARDINAL_ROLES]
    teens = [e for e in entries if e.role == "teen"]
    if len(tokens) > 1 and teens:
        return any(e.ordinal for e in teens) or _ordinal_word(lexicon, tokens[:-1])
    entries = [e for e in entries if e.role != "teen"] or entries
    return any(e.ordinal for e in entries)


def _kind(lexicon: Lexicon, tokens: list[Token], parse: Parse) -> Kind:
    """A whole value is cardinal, also when the words hold a decimal mark or
    a half ("2,5 milhões", "dois vírgula zero"). A value that is not whole is
    decimal when the words use a decimal mark, else a fraction. A whole
    value whose last word is an ordinal form is ordinal ("kahdeskymmenes")."""
    if parse.kind == Kind.ORDINAL:
        return parse.kind
    if parse.value.is_whole() and _ordinal_word(lexicon, tokens):
        return Kind.ORDINAL
    if parse.value.is_whole():
        return Kind.CARDINAL
    return Kind.DECIMAL if parse.decimal else Kind.FRACTION


def _form(tokens: list[Token]) -> Form:
    if all(t.is_digits for t in tokens):
        return Form.DIGITS
    return Form.MIXED if any(t.is_digits for t in tokens) else Form.WORDS


def _gender(lexicon: Lexicon, tokens: list[Token]) -> str | None:
    """The gender of the last word that shows one."""
    for token in reversed(tokens):
        if token.is_digits:
            gender = lexicon.ordinal_suffixes.get(token.suffix.casefold())
            if gender:
                return gender
            continue
        genders = {e.gender for e in lexicon.readings.get(token.norm, ())}
        if len(genders) == 1 and None not in genders:
            return genders.pop()
    return None


def _number_scale(lexicon: Lexicon, tokens: list[Token]) -> Scale | None:
    """The lexicon's scale when a word of the number has a power of ten that
    differs between the long and the short scale."""
    dependent = any(e.scale_dependent for t in tokens if not t.is_digits
                    for e in lexicon.readings.get(t.norm, ()))
    return lexicon.scale if dependent else None


def _confidence(grammar: Grammar, lexicon: Lexicon, run: list[Token], start: int, parse: Parse) -> float:
    lone_article = (parse.end == start + 1 and run[start].norm in lexicon.articles
                    and parse.end < len(run) and not run[parse.end].is_digits
                    and not grammar.starts_number(parse.end))
    if lone_article:
        return ARTICLE_CONFIDENCE
    # one word whose every reading has a common meaning that is no number
    entries = () if run[start].is_digits else lexicon.readings.get(run[start].norm, ())
    lone_ambiguous = parse.end == start + 1 and bool(entries) and all(e.ambiguous for e in entries)
    # a number written as one word that the lexicon lists with another
    # meaning ("üksteist" is eleven and "each other")
    word = run[start:parse.end]
    listed = len(word) > 1 and all(t.glued for t in word[1:]) \
        and "".join(t.norm for t in word) in lexicon.ambiguous_words
    return AMBIGUOUS_CONFIDENCE if parse.ambiguous or lone_ambiguous or listed else 1.0
