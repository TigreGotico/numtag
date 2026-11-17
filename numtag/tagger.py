"""Find the numbers of a text: the leftmost longest reading at each position."""
from numtag import digits
from numtag.digits import Rational
from numtag.grammar import Grammar, Parse, Pieces
from numtag.lexicon import CARDINAL_ROLES, Lexicon, Scale, exists, load
from numtag.mention import Form, Kind, NumberMention, Part, Reason, Role
from numtag.roman import roman_numerals
from numtag.tokenize import PeriodCues, Token, fold, tokenize

# The hyphen-minus and the minus sign that start a signed digit string.
SIGNS = "-\u2212"

# A weak number: an article alone before a noun, or a word with a common
# meaning that is no number. Scores are deterministic, not probabilities.
ARTICLE_CONFIDENCE = 0.3
AMBIGUOUS_CONFIDENCE = 0.4
# The score of a mention, by the reason it is not sure.
CONFIDENCE = {None: 1.0, Reason.ARTICLE: ARTICLE_CONFIDENCE, Reason.HOMOGRAPH: AMBIGUOUS_CONFIDENCE}


# The lexicon of a language tag with no region, or with a region that has no
# lexicon of its own.
BASE_LEXICON = {"pt": "pt-PT", "fr": "fr-FR", "no": "nb"}


def lexicon_name(lang: str) -> str:
    """The lexicon file for a language tag: the region's file when there is
    one ("pt-br" reads pt-BR, "fr-be" fr-BE), else the language's base file:
    every other "pt" tag reads pt-PT, "no" (Norwegian) reads Bokmål, nb, and
    every other tag its primary language ("de-AT" reads de)."""
    parts = lang.replace("_", "-").split("-")
    primary, region = parts[0].lower(), (parts[1].upper() if len(parts) > 1 else "")
    if region and exists(f"{primary}-{region}"):
        return f"{primary}-{region}"
    return BASE_LEXICON.get(primary, primary)


def tag_numbers(text: str, lang: str, *, scale: Scale | None = None) -> list[NumberMention]:
    """Every non-overlapping number in ``text``, in reading order."""
    lexicon = load(lexicon_name(lang), Scale(scale) if scale else None)
    words = lexicon.number_words
    tokens = tokenize(text, frozenset(lexicon.ordinal_suffixes), lexicon.lone_decimal_marks,
                      lexicon.abbreviations, words, lexicon.script,
                      compound_words=lexicon.compound_parts,
                      compound_inner=lexicon.joiners, shared_letter=lexicon.compound_shared_letter,
                      dotted_i=lexicon.dotted_i, apostrophes=lexicon.word_apostrophes,
                      suffix_marks=lexicon.ordinal_suffix_marks, digit_suffix_marks=lexicon.digit_suffix_marks,
                      period_ordinals=PeriodCues(lexicon.period_ordinal_before, lexicon.period_ordinal_lowercase,
                                                 lexicon.period_ordinal_free_digits)
                      if lexicon.period_ordinals else None,
                      dot_ordinal=lexicon.dot_ordinal, date_months=lexicon.date_months,
                      phrases=lexicon.phrases, group_mark=lexicon.group_mark,
                      compounds=lexicon.compounds, day_month=lexicon.decimal_mark != ".")
    mentions: list[NumberMention] = []
    for run in _runs(tokens, lexicon):
        mentions += _tag_run(text, lexicon, run)
    # "1/0" is a fraction with a zero denominator: it has no value, so its
    # digits give no mention. A chain of slashes ("3/5/2025") is no fraction.
    after_slash = [k > 0 and t.gap == "/" for k, t in enumerate(tokens)] + [False]
    no_value = [(tokens[k - 1].start, t.end) for k, t in enumerate(tokens)
                if after_slash[k] and tokens[k - 1].is_digits and t.is_digits and not t.norm.strip("0")
                and not after_slash[k - 1] and not after_slash[k + 1]]
    mentions = [m for m in mentions
                if not any(start < m.char_span[1] and m.char_span[0] < end for start, end in no_value)]
    mentions = _slash_fractions(text, tokens, mentions, after_slash)
    for token, value, kind, reason in roman_numerals(text, lexicon, tokens, [m.char_span for m in mentions]):
        span = (token.start, token.end)
        mentions.append(NumberMention(
            span, token.text, value, kind, Form.ROMAN, None, CONFIDENCE[reason],
            reasons=frozenset() if reason is None else frozenset({reason}),
            parts=(Part(Role.COUNT, span, token.text, value),)))
    return sorted(mentions, key=lambda m: m.char_span)


def _slash_fractions(text: str, tokens: list[Token], mentions: list[NumberMention],
                     after_slash: list[bool]) -> list[NumberMention]:
    """A digit fraction with a slash, "3/4", is one FRACTION mention. A sure
    cardinal right before it, with only a space between, makes a mixed
    number: "5 1/2" is 5.5, and a sign of the whole covers the fraction. Four
    digits with no group mark are no whole part, because they are mostly a
    year: "In 2023 1/3 of adults" is 2023 and 1/3. Only
    a fraction below one reads, so "24/7" and "50/50" keep their two numbers.
    So do a chain of slashes ("12/05/2024"), a term with a leading zero
    ("03/04") and a numerator right after a sign ("5-1/2")."""
    by_span = {m.char_span: m for m in mentions}
    by_end = {m.char_span[1]: m for m in mentions}
    consumed: set[tuple[int, int]] = set()
    fractions = []
    for k in range(1, len(tokens)):
        if not after_slash[k] or after_slash[k - 1] or after_slash[k + 1]:
            continue
        top, bottom = tokens[k - 1], tokens[k]
        signed = top.latin[0] in SIGNS
        terms = top.latin.lstrip(SIGNS), bottom.latin
        terms_read = [by_span.get((t.start, t.end)) for t in (top, bottom)]
        if (not all(t.isdigit() and t[0] != "0" for t in terms) or digits.compare(*terms) >= 0
                or text.endswith(tuple(SIGNS), 0, top.start)
                or any(m is None or m.kind != Kind.CARDINAL for m in terms_read)):
            continue
        spaced = top.gap != "" and not top.gap.strip(" \u00a0\u202f")
        whole = by_end.get(tokens[k - 2].end) if k > 1 and spaced and not (signed or after_slash[k - 2]) else None
        # Four digits with no group mark are mostly a year: "In 2023 1/3 of
        # adults", "minus 2023 1/2".
        year = tokens[k - 2].latin.lstrip(SIGNS)
        if whole and (whole.kind != Kind.CARDINAL or whole.reasons or (len(year) == 4 and year.isdigit())):
            whole = None
        value = Rational(*terms, signed)
        parts = (Part(Role.COUNT, (top.start, top.end), top.text, Rational(terms[0], negative=signed).canonical()),
                 Part(Role.DENOMINATOR, (bottom.start, bottom.end), bottom.text, terms[1]))
        first, form, gender, scale = top.start, Form.DIGITS, None, None
        if whole:
            value = Rational(whole.value.lstrip(SIGNS)) + value
            if whole.text[0] in SIGNS or any(p.role == Role.MINUS for p in whole.parts):
                value = -value
            first, gender, scale = whole.char_span[0], whole.gender, whole.number_scale
            form = Form.DIGITS if whole.form == Form.DIGITS else Form.MIXED
            parts = whole.parts + parts
            consumed.add(whole.char_span)
        consumed.update(m.char_span for m in terms_read)
        span = (first, bottom.end)
        fractions.append(NumberMention(span, text[first:bottom.end], value.canonical(), Kind.FRACTION, form, gender,
                                       number_scale=scale, parts=parts))
    return [m for m in mentions if m.char_span not in consumed] + fractions


def _runs(tokens: list[Token], lexicon: Lexicon) -> list[list[Token]]:
    """Stretches of tokens with only spaces or hyphens between them: a
    number never crosses punctuation. Where the lexicon allows it, a comma
    after a scale word links a number word: "dois milhões, duzentos e
    trinta e seis mil" is one number."""
    runs: list[list[Token]] = []
    for token in tokens:
        if runs and (token.links_to_previous() or _comma_between_classes(lexicon, runs[-1][-1], token)):
            runs[-1].append(token)
        else:
            runs.append([token])
    return runs


def _comma_between_classes(lexicon: Lexicon, previous: Token, token: Token) -> bool:
    """The classes go from the largest down, so the class after the comma
    is smaller: "dois milhões, mil e quinhentos" is one number, and "dois
    mil, milhões de pessoas" is two thousand and then a noun phrase."""
    if not (lexicon.comma_between_classes and token.gap.startswith(",") and token.gap[1:].isspace()
            and not previous.is_digits and not token.is_digits):
        return False
    classes = ("scale_numeral", "scale_noun")
    scales = [e.exponent for e in lexicon.readings.get(previous.norm, ()) if e.role in classes]
    after = lexicon.readings.get(token.norm, ())
    return bool(scales) and any(e.role != "half" for e in after) \
        and all(e.exponent < max(scales) for e in after if e.role in classes)


def _tag_run(text: str, lexicon: Lexicon, run: list[Token]) -> list[NumberMention]:
    grammar = Grammar(lexicon, run)
    mentions = []
    number_end = -1  # the run index after the last number
    count_end = -1  # the run index after the last sure cardinal
    i = 0
    while i < len(run):
        name = next((n for n in lexicon.number_names if tuple(t.norm for t in run[i:i + len(n)]) == n), None)
        if name:
            # "سه شنبه" is Tuesday: a name holds no number
            i += len(name)
            continue
        negative = _is_minus(grammar, lexicon, run, i)
        start = i + 1 if negative else i
        # "-2 milhões e meio" is minus two and a half million: the sign of a
        # digit string that starts a number applies to the whole number
        signed = _signed(run[start])
        number_grammar = Grammar(lexicon, run, unsigned=start) if signed else grammar
        parses = [p for p in number_grammar.numbers(start) if _whole_words(number_grammar, run, start, p)]
        # a number starts and ends at the edges of a word, never inside one
        if not parses or run[i].glued:
            i += 1
            continue
        best = max(parses, key=lambda p: p.end)
        if not negative and (_percent_word(lexicon, run, start, best, number_end)
                             or _not_a_single(lexicon, run, start, best)
                             # "öt hét" is five weeks: right after a sure cardinal, a word
                             # that is also a noun is the noun that the cardinal counts
                             or i == count_end and best.end == start + 1
                             and run[start].norm in lexicon.nouns_after_count):
            i += 1
            continue
        value = -best.value if negative != signed else best.value
        span = (run[i].start, run[best.end - 1].end)
        reason = _reason(number_grammar, lexicon, run, start, best, alone=text.strip() == run[start].text,
                         signed=negative)
        kind = _kind(lexicon, run[start:best.end], best)
        pieces = best.parts
        if signed:
            # the digit string is one part with its sign: "-2" is -2
            role, first_index, end, part_value = pieces[0]
            pieces = ((role, first_index, end, -part_value),) + pieces[1:]
        if negative:
            pieces = ((Role.MINUS, i, start, None),) + pieces
        mentions.append(NumberMention(
            span, text[span[0]:span[1]], value.canonical(), kind,
            _form(run[start:best.end]), _gender(lexicon, run[start:best.end]), CONFIDENCE[reason],
            number_scale=_number_scale(lexicon, run[start:best.end]),
            reasons=frozenset() if reason is None else frozenset({reason}),
            parts=_parts(text, run, pieces)))
        count_end = best.end if kind == Kind.CARDINAL and reason is None else -1
        i = number_end = best.end
    return mentions


def _parts(text: str, run: list[Token], pieces: Pieces) -> tuple[Part, ...]:
    """The parts of a parse, with their character spans in ``text``."""
    parts = []
    for role, start, end, value in pieces:
        span = (run[start].start, run[end - 1].end)
        parts.append(Part(role, span, text[span[0]:span[1]], None if value is None else value.canonical()))
    return tuple(parts)


def _signed(token: Token) -> bool:
    return token.is_digits and not token.suffix and not token.period_ordinal and token.latin[:1] in "-\u2212"


def _not_a_single(lexicon: Lexicon, run: list[Token], start: int, parse: Parse) -> bool:
    """True when the word for one follows a negative particle: ru "ни
    одного", pl "ani jednego" mean "not a single", no count."""
    return (parse.end == start + 1 and start > 0 and not run[start].is_digits
            and run[start - 1].norm in lexicon.negative_particles and parse.value.canonical() == "1")


def _percent_word(lexicon: Lexicon, run: list[Token], start: int, parse: Parse, number_end: int) -> bool:
    """True when the one word at ``start`` ends a percent phrase after a
    number ("vint per cent", "20 per cent"), after a slot that holds a
    number ("{brightness} per cent de brillantor"), or alone ("per cent", a
    line of a vocabulary file). "Ho he venut per cent." (for a hundred) and
    "per cent vint" (for 120) keep their number."""
    if parse.end != start + 1 or run[start].is_digits:
        return False
    for phrase in lexicon.percent_phrases:
        head = start - len(phrase) + 1
        if head >= 0 and tuple(t.norm for t in run[head:start + 1]) == phrase \
                and (number_end == head
                     or head == 0 and (run[0].gap.rstrip().endswith("}") or parse.end == len(run))):
            return True
    return False


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
            gender = lexicon.ordinal_suffixes.get(fold(token.suffix))
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


def _reason(grammar: Grammar, lexicon: Lexicon, run: list[Token], start: int, parse: Parse,
            *, alone: bool = False, signed: bool = False) -> Reason | None:
    """Why the number is not sure, or None for a sure number. ``alone``: the
    word is the whole text. ``signed``: a minus word starts the number."""
    # The article stands next to its noun: before it ("um livro"), or after
    # it where the language puts it there ("liburu bat"). A number in digits
    # and an ordinal are part of the noun phrase: "un 20 por ciento", "una
    # segunda curiosidad". A hyphenated noun gives no token, and the word
    # beside it notes it: "um guarda-chuva", "liburu-denda bat". A homograph
    # alone is the adjective or noun of the phrase ("un nou enregistrament"),
    # unless it is a noun that a count takes ("egy hét" is one week).
    noun = start - 1 if lexicon.article_after_noun else parse.end
    # The word is the number after a noun that names a number ("o número
    # um"), and before a percent phrase, where it counts the hundredths ("un
    # pour cent")
    named = (start > 0 and run[start - 1].norm in lexicon.number_nouns
             or any(tuple(t.norm for t in run[parse.end:parse.end + len(p)]) == p for p in lexicon.percent_phrases))
    hyphenated_noun = run[start].noun_before if lexicon.article_after_noun else run[start].noun_after
    lone_article = (parse.end == start + 1 and run[start].norm in lexicon.articles and not named
                    and (hyphenated_noun
                         or 0 <= noun < len(run)
                         and (run[noun].is_digits or not grammar.starts_number(noun)
                              or all(_kind(lexicon, run[noun:p.end], p) == Kind.ORDINAL
                                     or p.end == noun + 1 and p.ambiguous
                                     and run[noun].norm not in lexicon.nouns_after_count
                                     for p in grammar.numbers(noun)))))
    if lone_article:
        return Reason.ARTICLE
    # "Er lud mich ein.": a lone article that ends the clause is no numeral
    if parse.end == start + 1 == len(run) and run[start].norm in lexicon.article_needs_noun and not named:
        return Reason.ARTICLE
    # an article that is the whole text, as a line of a vocabulary file
    # ("un", "eine"), has the same two readings and no noun to decide them
    if alone and parse.end == start + 1 and run[start].norm in lexicon.articles:
        return Reason.ARTICLE
    # one word whose every reading has a common meaning that is no number
    entries = () if run[start].is_digits else lexicon.readings.get(run[start].norm, ())
    lone_ambiguous = parse.end == start + 1 and bool(entries) and all(e.ambiguous for e in entries)
    # a number written as one word that the lexicon lists with another
    # meaning ("üksteist" is eleven and "each other")
    word = run[start:parse.end]
    listed = len(word) > 1 and all(t.glued for t in word[1:]) \
        and "".join(t.norm for t in word) in lexicon.ambiguous_words
    # "Um décimo sobreviveu.": after an article, a word that is also a
    # singular denominator reads as the ordinal because no partitive follows
    # it, and a verb there gives the same reading as a noun
    weak_ordinal = parse.end == start + 1 and start > 0 and bool(lexicon.partitives) \
        and run[start - 1].norm in lexicon.articles \
        and any(not e.plural for e in lexicon.of(run[start].norm, "denominator")) \
        and _kind(lexicon, word, parse) == Kind.ORDINAL
    # "a les nou": the word before it agrees only with the number reading
    agrees = parse.end == start + 1 and start > 0 and bool(entries) \
        and all(run[start - 1].norm in e.number_after for e in entries)
    # "al per cent": a percent phrase with no number before it, at the end or
    # before "of", is the price ("Ho he venut per cent.") or the percent sign
    # with its number missing ("el tant per cent de descompte"). Before a
    # noun it is the price: "per cent euros".
    bare_percent = parse.end == start + 1 and not run[start].is_digits \
        and (parse.end == len(run) or run[parse.end].norm in lexicon.of_words) and any(
            tuple(t.norm for t in run[max(start - len(p) + 1, 0):start + 1]) == p for p in lexicon.percent_phrases)
    # a word that is weak only at the end of a clause is the number when it
    # is the whole text with no punctuation: a spoken answer ("hat" answers "hány?")
    whole = alone and parse.end == start + 1 and bool(entries) \
        and all(e.weak_at_end and not e.ambiguous for e in entries)
    # "miinus viis": a minus word starts only a number, so it makes the reading clear
    homograph = (parse.ambiguous and not whole) or lone_ambiguous or listed or weak_ordinal or bare_percent
    return Reason.HOMOGRAPH if homograph and not signed and not agrees else None
