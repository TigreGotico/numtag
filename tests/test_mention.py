import unittest
from decimal import Decimal
from fractions import Fraction

from numtag import Form, Kind, NumberMention, Scale, is_canonical_value
from numtag import lexicon


class TestCanonicalValue(unittest.TestCase):
    def test_canonical_forms_are_accepted(self):
        for value in ("0", "7", "24", "-21", "1" + "0" * 600,
                      "2.5", "-0.25", "0.5", "1/3", "-2/3"):
            with self.subTest(value=value):
                self.assertTrue(is_canonical_value(value))

    def test_other_forms_are_refused(self):
        for value in ("", "007", "-0", "-0.0", "2.50", "2.", ".5", "+3",
                      "0/3", "3/0", "1e6", "1 000", "1,5", "um"):
            with self.subTest(value=value):
                self.assertFalse(is_canonical_value(value))

    def test_standard_types_read_every_form(self):
        self.assertEqual(int("1" + "0" * 600), 10 ** 600)
        self.assertEqual(Decimal("-0.25"), Decimal(-1) / 4)
        self.assertEqual(Fraction("1/3"), Fraction(1, 3))
        self.assertEqual(Fraction("2.5"), Fraction(5, 2))


class TestNumberMention(unittest.TestCase):
    def test_a_mention_holds_its_slice(self):
        text = "comprou duas dúzias de ovos"
        mention = NumberMention((8, 19), text[8:19], "24", Kind.CARDINAL,
                                Form.WORDS, gender="feminine")
        self.assertEqual(text[slice(*mention.char_span)], mention.text)

    def test_a_span_that_does_not_fit_the_text_is_refused(self):
        with self.assertRaises(ValueError):
            NumberMention((0, 3), "duas", "2", Kind.CARDINAL, Form.WORDS)

    def test_a_value_that_is_not_canonical_is_refused(self):
        with self.assertRaises(ValueError):
            NumberMention((0, 3), "2,5", "2,5", Kind.DECIMAL, Form.DIGITS)

    def test_number_scale_is_a_scale_or_none(self):
        mention = NumberMention((0, 9), "um bilião", "1" + "0" * 12, Kind.CARDINAL, Form.WORDS,
                                number_scale=Scale.LONG)
        self.assertIs(mention.number_scale, Scale.LONG)
        self.assertIsNone(NumberMention((0, 4), "dois", "2", Kind.CARDINAL, Form.WORDS).number_scale)
        with self.assertRaises(ValueError):
            NumberMention((0, 9), "um bilião", "1" + "0" * 12, Kind.CARDINAL, Form.WORDS,
                          number_scale="long")

    def test_number_scale_is_keyword_only_and_confidence_keeps_its_place(self):
        # the seventh positional argument is confidence, as in the contract on dev
        mention = NumberMention((0, 3), "uma", "1", Kind.CARDINAL, Form.WORDS, "feminine", 0.3)
        self.assertEqual((mention.gender, mention.number_scale, mention.confidence), ("feminine", None, 0.3))
        with self.assertRaises(TypeError):
            NumberMention((0, 3), "one", "1", Kind.CARDINAL, Form.WORDS, None, Scale.LONG, 1.0)

    def test_number_scale_is_part_of_equality(self):
        long = NumberMention((0, 3), "one", "1", Kind.CARDINAL, Form.WORDS, number_scale=Scale.LONG)
        self.assertNotEqual(long, NumberMention((0, 3), "one", "1", Kind.CARDINAL, Form.WORDS))

    def test_the_contract_module_owns_the_scale(self):
        self.assertIs(lexicon.Scale, Scale)

    def test_confidence_is_not_part_of_equality(self):
        a = NumberMention((0, 3), "uma", "1", Kind.CARDINAL, Form.WORDS, confidence=0.3)
        b = NumberMention((0, 3), "uma", "1", Kind.CARDINAL, Form.WORDS)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
