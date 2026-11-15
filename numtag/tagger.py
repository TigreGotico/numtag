"""Find the numbers of a text: the leftmost longest reading at each position."""
from numtag.grammar import Grammar, Parse
from numtag.lexicon import Lexicon, Scale, load
from numtag.mention import Form, Kind, NumberMention
from numtag.tokenize import PeriodCues, Token, tokenize

# A weak number: an article alone before a noun, or a word with a common
# meaning that is no number. Scores are deterministic, not probabilities.
ARTICLE_CONFIDENCE = 0.3
AMBIGUOUS_CONFIDENCE = 0.4


def lexicon_name(lang: str) -> str:
    """The lexicon file for a language tag: "pt-br" reads pt-BR, every other
    "pt" tag pt-PT, "no" (Norwegian) reads Bokmål, nb, and every other tag
    its primary language ("de-AT" reads de)."""
    parts = lang.replace("_", "-").split("-")
    primary, region = parts[0].lower(), (parts[1].upper() if len(parts) > 1 else "")
    if primary == "pt":
        return "pt-BR" if region == "BR" else "pt-PT"
    return "nb" if primary == "no" else primary


def tag_numbers(text: str, lang: str, *, scale: Scale | None = None) -> list[NumberMention]:
    """Every non-overlapping number in ``text``, in reading order."""
    lexicon = load(lexicon_name(lang), Scale(scale) if scale else None)
    words = lexicon.number_words
    tokens = tokenize(text, frozenset(lexicon.ordinal_suffixes), lexicon.lone_decimal_marks,
                      lexicon.abbreviations, words,
                      compound_words=words if lexicon.compound_words else frozenset(),
                      compound_inner=lexicon.joiners, shared_letter=lexicon.compound_shared_letter,
                      suffix_marks=lexicon.ordinal_suffix_marks,
                      period_ordinals=PeriodCues(lexicon.period_ordinal_before, lexicon.period_ordinal_lowercase,
                                                 lexicon.period_ordinal_free_digits)
                      if lexicon.period_ordinals else None)
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
        # A number starts and ends with a whole word, not inside a compound.
        parses = [] if run[i].glued else [
            p for p in grammar.numbers(start) if p.end == len(run) or not run[p.end].glued]
        if not parses:
            i += 1
            continue
        best = max(parses, key=lambda p: p.end)
        value = -best.value if negative else best.value
        span = (run[i].start, run[best.end - 1].end)
        mentions.append(NumberMention(
            span, text[span[0]:span[1]], value.canonical(), _kind(best),
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


def _kind(parse: Parse) -> Kind:
    """A whole value is cardinal, also when the words hold a decimal mark or
    a half ("2,5 milhões", "dois vírgula zero"). A value that is not whole is
    decimal when the words use a decimal mark, else a fraction."""
    if parse.kind == Kind.ORDINAL:
        return parse.kind
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
    # "Er lud mich ein.": a lone article that ends the clause is no numeral
    if parse.end == start + 1 == len(run) and run[start].norm in lexicon.article_needs_noun:
        return ARTICLE_CONFIDENCE
    return AMBIGUOUS_CONFIDENCE if parse.ambiguous else 1.0
