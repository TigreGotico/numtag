"""Vague quantities: words that state an amount but no exact number.

"millions" and "dezenas" are a MAGNITUDE: a plural scale word with no count,
whose lower bound is two of the scale. "several" and "muitos" are an AMOUNT:
no value, no scale and no bound. The words are the ``vague_quantifier``
entries of each lexicon, each with its source; the same list stops a scale
word right after one of them from reading a number (grammar ``_after_vague``).
A plural scale word and the scale word it counts, joined by a ``vague_of`` word
("milhares de milhões"), make one magnitude.
"""
from bisect import bisect_left

from numtag import digits
from numtag.lexicon import SCALE_ROLES, Entry, Lexicon, load
from numtag.mention import Reason, VagueKind, VagueQuantity
from numtag.tagger import CONFIDENCE, _runs, _tokenize, lexicon_name, tag_numbers
from numtag.tokenize import Token


def tag_vague_quantities(text: str, lang: str) -> list[VagueQuantity]:
    """Every non-overlapping vague quantity in text, in reading order."""
    lexicon = load(lexicon_name(lang))
    if not lexicon.vague_quantifiers:
        return []
    # "três milhões": a count before the plural makes an ordinary number
    numbers = [m.char_span for m in tag_numbers(text, lang)]
    starts = [start for start, _ in numbers]

    def free(token: Token) -> bool:
        # the mentions are sorted and do not overlap: test the last one that starts before the token ends
        k = bisect_left(starts, token.end) - 1
        return k < 0 or numbers[k][1] <= token.start

    found = []
    for run in _runs(_tokenize(text, lexicon), lexicon):
        i = 0
        while i < len(run):
            phrase = _phrase(lexicon, run, i)
            end = i + len(phrase)
            if not phrase or not all(free(t) for t in run[i:end]):
                i += 1
                continue
            if i and not run[i - 1].is_digits and run[i - 1].norm in lexicon.vague_not_after.get(phrase, ()):
                i += 1
                continue
            ambiguous = lexicon.vague_quantifiers[phrase]
            head = _scale(lexicon, run[i]) if len(phrase) == 1 else None
            if head is not None and head.plural:
                scales = [head]
                ambiguous = ambiguous or head.ambiguous
            else:
                # "several million", "muitos mil milhões": the vague word stands where
                # the count would, and the scale words make the quantity reading clear
                scales = []
                while end < len(run) and free(run[end]) and (entry := _scale(lexicon, run[end])):
                    scales.append(entry)
                    end += 1
                ambiguous = any(e.ambiguous for e in scales) if scales else ambiguous
            # "milhares de milhões": a plural scale word and the scale word it counts
            # make one magnitude, the product of both
            direct = len(scales)
            counted = bool(scales) and scales[-1].plural
            while counted and end + 1 < len(run) and not run[end].is_digits and run[end].norm in lexicon.vague_of \
                    and free(run[end]) and free(run[end + 1]) and (entry := _scale(lexicon, run[end + 1])):
                scales.append(entry)
                ambiguous = ambiguous or entry.ambiguous
                end += 2
                counted = entry.plural
            reason = Reason.HOMOGRAPH if ambiguous else None
            span = (run[i].start, run[end - 1].end)
            if scales:
                kind, value = VagueKind.MAGNITUDE, "1"
                for entry in scales:
                    value = digits.multiply(value, entry.value if entry.role == "collective"
                                            else digits.shift("1", entry.exponent))
                # the plural means more than one: "millions" is at least two million, and
                # "milhares de milhões" at least two thousand millions
                bound = digits.multiply("2", value) if direct == 1 and scales[0].plural else None
            else:
                kind, value, bound = VagueKind.AMOUNT, None, None
            found.append(VagueQuantity(span, text[span[0]:span[1]], kind, value, bound, CONFIDENCE[reason],
                                       reasons=frozenset() if reason is None else frozenset({reason})))
            i = end
    return found


def _phrase(lexicon: Lexicon, run: list[Token], i: int) -> tuple[str, ...]:
    """The longest vague phrase that starts at ``i``, or an empty tuple."""
    longest = max(map(len, lexicon.vague_quantifiers))
    words = tuple(t.norm if not t.is_digits else None for t in run[i:i + longest])
    phrases = [p for p in lexicon.vague_quantifiers if words[:len(p)] == p]
    return max(phrases, key=len, default=())


def _scale(lexicon: Lexicon, token: Token) -> Entry | None:
    """The scale-word or collective reading of ``token``, if it has one."""
    if token.is_digits:
        return None
    return next((e for e in lexicon.readings.get(token.norm, ())
                 if e.role in SCALE_ROLES or e.role == "collective"), None)
