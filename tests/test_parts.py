"""The parts of a mention: docs/api.md, "Part" and "Role"."""
import json
import unittest
from fractions import Fraction
from pathlib import Path

from numtag import Form, Kind, NumberMention, Part, Role, tag_numbers
from numtag.lexicon import fold, load
from numtag.tagger import lexicon_name

GOLD = Path(__file__).parent / "gold"
COUNT, SCALE, COLLECTIVE, OF, JOINER, HALF = Role.COUNT, Role.SCALE, Role.COLLECTIVE, Role.OF, Role.JOINER, Role.HALF
DENOMINATOR, MINUS, DECIMAL_MARK, DECIMALS = Role.DENOMINATOR, Role.MINUS, Role.DECIMAL_MARK, Role.DECIMALS

# (text, lang, [(mention text, value, [(role, part text, part value)])]), with
# each value worked out by hand from the words of the part alone.
WORKED = [
    ("às três e meia", "pt-PT", [("três e meia", "3.5", [(COUNT, "três", "3"), (JOINER, "e", None), (HALF, "meia", "0.5")])]),
    ("há mil e duzentos anos", "pt-PT", [("mil e duzentos", "1200", [(SCALE, "mil", "1000"), (JOINER, "e", None),
                                                                        (COUNT, "duzentos", "200")])]),
    ("dois milhões e meio de anos", "pt-PT", [("dois milhões e meio", "2500000", [
        (COUNT, "dois", "2"), (SCALE, "milhões", "1000000"), (JOINER, "e", None), (HALF, "meio", "0.5")])]),
    ("mil e quinhentos milhões", "pt-PT", [("mil e quinhentos milhões", "1500000000", [
        (SCALE, "mil", "1000"), (JOINER, "e", None), (COUNT, "quinhentos", "500"), (SCALE, "milhões", "1000000")])]),
    ("duas dúzias de milhar", "pt-PT", [("duas dúzias de milhar", "24000", [
        (COUNT, "duas", "2"), (COLLECTIVE, "dúzias", "12"), (OF, "de", None), (SCALE, "milhar", "1000")])]),
    ("uma dúzia e meia", "pt-PT", [("uma dúzia e meia", "18", [
        (COUNT, "uma", "1"), (COLLECTIVE, "dúzia", "12"), (JOINER, "e", None), (HALF, "meia", "0.5")])]),
    ("menos cinco graus", "pt-PT", [("menos cinco", "-5", [(MINUS, "menos", None), (COUNT, "cinco", "5")])]),
    ("-5 graus", "pt-PT", [("-5", "-5", [(COUNT, "-5", "-5")])]),
    ("dois vírgula zero cinco", "pt-PT", [("dois vírgula zero cinco", "2.05", [
        (COUNT, "dois", "2"), (DECIMAL_MARK, "vírgula", None), (DECIMALS, "zero cinco", "0.05")])]),
    ("2,5 milhões", "pt-PT", [("2,5 milhões", "2500000", [(COUNT, "2,5", "2.5"), (SCALE, "milhões", "1000000")])]),
    ("dois terços", "pt-PT", [("dois terços", "2/3", [(COUNT, "dois", "2"), (DENOMINATOR, "terços", "3")])]),
    ("três doze avos", "pt-PT", [("três doze avos", "0.25", [(COUNT, "três", "3"), (DENOMINATOR, "doze avos", "12")])]),
    ("1.234,5", "pt-PT", [("1.234,5", "1234.5", [(COUNT, "1.234,5", "1234.5")])]),
    ("1 234,5", "pt-PT", [("1 234,5", "1234.5", [(COUNT, "1 234,5", "1234.5")])]),
    ("um bilião", "pt-PT", [("um bilião", "1000000000000", [(COUNT, "um", "1"), (SCALE, "bilião", "1000000000000")])]),
    ("vigésimo primeiro", "pt-PT", [("vigésimo primeiro", "21", [(COUNT, "vigésimo primeiro", "21")])]),
    ("a quarter past four", "en", [("a quarter", "0.25", [(COUNT, "a", "1"), (DENOMINATOR, "quarter", "4")]),
                                   ("four", "4", [(COUNT, "four", "4")])]),
    ("sixty six million years ago", "en", [("sixty six million", "66000000", [
        (COUNT, "sixty six", "66"), (SCALE, "million", "1000000")])]),
    ("one million two hundred thousand years ago", "en", [("one million two hundred thousand", "1200000", [
        (COUNT, "one", "1"), (SCALE, "million", "1000000"), (COUNT, "two hundred", "200"), (SCALE, "thousand", "1000")])]),
    ("half a dozen", "en", [("half a dozen", "6", [(HALF, "half", "0.5"), (COLLECTIVE, "a dozen", "12")])]),
    ("minus five", "en", [("minus five", "-5", [(MINUS, "minus", None), (COUNT, "five", "5")])]),
    ("one point two million", "en", [("one point two million", "1200000", [
        (COUNT, "one", "1"), (DECIMAL_MARK, "point", None), (DECIMALS, "two", "0.2"), (SCALE, "million", "1000000")])]),
    ("two and a third", "en", [("two and a third", "7/3", [
        (COUNT, "two", "2"), (JOINER, "and", None), (COUNT, "a", "1"), (DENOMINATOR, "third", "3")])]),
    ("six thousand two hundredth", "en", [("six thousand two hundredth", "6200", [
        (COUNT, "six", "6"), (SCALE, "thousand", "1000"), (COUNT, "two hundredth", "200")])]),
    ("one and a half", "en", [("one and a half", "1.5", [(COUNT, "one", "1"), (JOINER, "and", None),
                                                          (HALF, "a half", "0.5")])]),
    ("a half", "en", [("a half", "0.5", [(COUNT, "a", "1"), (DENOMINATOR, "half", "2")])]),
    ("a third of a dozen", "en", [("a third of a dozen", "4", [
        (COUNT, "a", "1"), (DENOMINATOR, "third", "3"), (OF, "of", None), (COLLECTIVE, "a dozen", "12")])]),
    ("zweieinhalb Millionen", "de", [("zweieinhalb Millionen", "2500000", [
        (COUNT, "zwei", "2"), (HALF, "einhalb", "0.5"), (SCALE, "Millionen", "1000000")])]),
    # a case form that names the parts, then the count of parts
    ("üçte bir", "tr", [("üçte bir", "1/3", [(DENOMINATOR, "üçte", "3"), (COUNT, "bir", "1")])]),
    # the count of one after the noun
    ("heren bat", "eu", [("heren bat", "1/3", [(DENOMINATOR, "heren", "3"), (COUNT, "bat", "1")])]),
    ("три целых и двадцать пять сотых", "ru", [("три целых и двадцать пять сотых", "3.25", [
        (COUNT, "три", "3"), (DECIMAL_MARK, "целых", None), (JOINER, "и", None),
        (DECIMALS, "двадцать пять сотых", "0.25")])]),
    # a compound word follows its sub-words; Swedish "ett" and "tusen" share the t
    ("dreihunderttausend", "de", [("dreihunderttausend", "300000", [
        (COUNT, "dreihundert", "300"), (SCALE, "tausend", "1000")])]),
    ("ettusen", "sv", [("ettusen", "1000", [(COUNT, "ett", "1"), (SCALE, "tusen", "1000")])]),
    # a word that holds two parts is one part: the dual, the numerator in the denominator
    ("ألفين", "ar", [("ألفين", "2000", [(SCALE, "ألفين", "1000")])]),
    ("ثلثان", "ar", [("ثلثان", "2/3", [(DENOMINATOR, "ثلثان", "3")])]),
]


def _value_from_counts_and_scales(lang: str, parts: tuple[Part, ...]) -> Fraction | None:
    """The value of a mention whose parts are counts, scales, joiners and a
    minus, worked out from the part values alone: a scale multiplies the
    counts and smaller scales before it. None for any other mention, and for
    a part that holds more than its word value: a dual ("ألفين") or the
    count of one after a noun ("milioi bat")."""
    if not {p.role for p in parts} <= {COUNT, SCALE, JOINER, MINUS}:
        return None
    lexicon = load(lexicon_name(lang))
    stack: list[tuple[Fraction, Fraction]] = []  # (amount, scale)
    for k, part in enumerate(parts):
        word = fold(part.text)
        # also behind a clitic prefix of one or two letters ("وألفين", "באלפיים")
        if any(e.count for w in (word, word[1:], word[2:]) for e in lexicon.readings.get(w, ())):
            return None
        if part.role == COUNT and k and parts[k - 1].role == SCALE and word in lexicon.one_after_noun:
            return None
        if part.role == COUNT:
            stack.append((Fraction(part.value), Fraction(1)))
        elif part.role == SCALE:
            scale, amount = Fraction(part.value), Fraction(0)
            while stack and stack[-1][1] < scale:
                amount += stack.pop()[0]
            stack.append(((amount or 1) * scale, scale))
    total = sum(amount for amount, _ in stack)
    return -total if parts[0].role == MINUS else total


def _gold():
    for path in sorted(GOLD.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            yield path.stem, json.loads(line)["text"]


class TestWorkedExamples(unittest.TestCase):
    def test_each_example_gives_its_parts(self):
        for text, lang, expected in WORKED:
            with self.subTest(text=text, lang=lang):
                got = [(m.text, m.value, [(p.role, p.text, p.value) for p in m.parts])
                       for m in tag_numbers(text, lang)]
                self.assertEqual(got, expected)

    def test_a_part_span_indexes_the_input(self):
        text = "Saímos às três e meia."
        for part in tag_numbers(text, "pt-PT")[0].parts:
            self.assertEqual(text[part.char_span[0]:part.char_span[1]], part.text)
        self.assertEqual([p.char_span for p in tag_numbers(text, "pt-PT")[0].parts], [(10, 14), (15, 16), (17, 21)])

    def test_a_joiner_prefix_is_in_no_part(self):
        # "ושבעה" is "and seven": the span and the count start after the prefix
        mention = tag_numbers("שלושה ושבעה", "he")[-1]
        self.assertEqual([(p.role, p.char_span, p.text, p.value) for p in mention.parts], [(COUNT, (7, 11), "שבעה", "7")])


class TestEveryGoldMention(unittest.TestCase):
    def test_every_word_is_in_exactly_one_part(self):
        checked = 0
        for lang, text in _gold():
            for mention in tag_numbers(text, lang):
                start = mention.char_span[0]
                cover = [0] * len(mention.text)
                for part in mention.parts:
                    for k in range(part.char_span[0] - start, part.char_span[1] - start):
                        cover[k] += 1
                uncovered = {mention.text[k] for k, n in enumerate(cover) if n == 0}
                twice = [mention.text[k] for k, n in enumerate(cover) if n > 1]
                with self.subTest(lang=lang, text=mention.text):
                    self.assertTrue(mention.parts)
                    self.assertTrue(all(c.isspace() or c in "-­," for c in uncovered), uncovered)
                    # two parts share at most the one letter of a compound ("ettusen")
                    self.assertTrue(all(c.isalpha() for c in twice) and len(twice) <= 1, twice)
                checked += 1
        self.assertGreater(checked, 8000)

    def test_counts_and_scales_give_the_mention_value(self):
        checked = 0
        for lang, text in _gold():
            for mention in tag_numbers(text, lang):
                value = _value_from_counts_and_scales(lang, mention.parts)
                if value is None:
                    continue
                with self.subTest(lang=lang, text=mention.text):
                    self.assertEqual(value, Fraction(mention.value))
                checked += 1
        self.assertGreater(checked, 7000)

    def test_the_last_scale_gives_the_deep_time_count(self):
        # deep time divides the value by the last scale: "há mil e duzentos anos" is 1.2 thousands
        for text, lang, count in [("há mil e duzentos anos", "pt-PT", Fraction("1.2")),
                                  ("one million two hundred thousand years ago", "en", Fraction(1200)),
                                  ("dois milhões e meio de anos", "pt-PT", Fraction("2.5"))]:
            mention = tag_numbers(text, lang)[0]
            last = [p for p in mention.parts if p.role == SCALE][-1]
            with self.subTest(text=text):
                self.assertEqual(Fraction(mention.value) / Fraction(last.value), count)


class TestPartChecks(unittest.TestCase):
    def test_a_role_with_no_number_takes_no_value(self):
        with self.assertRaisesRegex(ValueError, "takes no value"):
            Part(JOINER, (0, 1), "e", "1")
        with self.assertRaisesRegex(ValueError, "takes a value"):
            Part(COUNT, (0, 4), "dois")

    def test_a_part_value_is_canonical(self):
        with self.assertRaisesRegex(ValueError, "not a canonical"):
            Part(COUNT, (0, 4), "dois", "2.0")

    def test_a_part_lies_inside_its_mention_in_reading_order(self):
        two = Part(COUNT, (0, 3), "two", "2")
        with self.assertRaisesRegex(ValueError, "is not inside"):
            NumberMention((0, 3), "two", "2", Kind.CARDINAL, Form.WORDS, parts=(Part(COUNT, (4, 7), "two", "2"),))
        hundred = Part(SCALE, (4, 11), "hundred", "100")
        mention = NumberMention((0, 11), "two hundred", "200", Kind.CARDINAL, Form.WORDS, parts=(two, hundred))
        self.assertEqual(mention.parts, (two, hundred))
        with self.assertRaisesRegex(ValueError, "reading order"):
            NumberMention((0, 11), "two hundred", "200", Kind.CARDINAL, Form.WORDS, parts=(hundred, two))

    def test_parts_share_at_most_one_letter_and_never_nest(self):
        dois = Part(COUNT, (0, 4), "dois", "2")
        for parts in [(dois, Part(COUNT, (3, 4), "s", "7")),
                      (Part(COUNT, (0, 3), "two", "2"), Part(JOINER, (2, 3), "o"), Part(COUNT, (2, 7), "o ten", "10"))]:
            text = "dois" if parts[0] is dois else "two ten"
            with self.subTest(parts=parts), self.assertRaisesRegex(ValueError, "reading order"):
                NumberMention((0, len(text)), text, "2", Kind.CARDINAL, Form.WORDS, parts=parts)
        ett, tusen = Part(COUNT, (0, 3), "ett", "1"), Part(SCALE, (2, 7), "tusen", "1000")
        self.assertEqual(NumberMention((0, 7), "ettusen", "1000", Kind.CARDINAL, Form.WORDS,
                                       parts=(ett, tusen)).parts, (ett, tusen))

    def test_parts_stay_out_of_equality(self):
        two = Part(COUNT, (0, 3), "two", "2")
        self.assertEqual(NumberMention((0, 3), "two", "2", Kind.CARDINAL, Form.WORDS, parts=(two,)),
                         NumberMention((0, 3), "two", "2", Kind.CARDINAL, Form.WORDS))
