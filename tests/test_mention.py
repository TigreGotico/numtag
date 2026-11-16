import unittest
from decimal import Decimal
from fractions import Fraction

import numtag
from numtag import ARTICLE_CONFIDENCE, Form, Kind, NumberMention, Reason, Scale, is_canonical_value, tag_numbers
from numtag import tagger
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


class TestArticleConfidence(unittest.TestCase):
    def test_the_package_exports_the_article_score(self):
        self.assertIs(ARTICLE_CONFIDENCE, tagger.ARTICLE_CONFIDENCE)
        self.assertEqual(ARTICLE_CONFIDENCE, 0.3)

    def test_an_article_gets_the_exported_score(self):
        found = tag_numbers("Comprei uma casa e dois carros.", "pt-PT")
        self.assertEqual([m.confidence == ARTICLE_CONFIDENCE for m in found], [True, False])


class TestReasons(unittest.TestCase):
    def test_one_after_a_number_noun_is_the_number(self):
        # "o número um": the word names the number, so it is no article
        for text, lang, word in (("o número um por favor", "pt-PT", "um"), ("O número um", "pt-BR", "um"),
                                 ("le numéro un s'il te plaît", "fr-FR", "un"),
                                 ("nummer een alsjeblieft", "nl", "een"), ("nummer ett tack", "sv", "ett")):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.value, m.reasons) for m in tag_numbers(text, lang)],
                                 [(word, "1", frozenset())])
        # the article before "número" stays an article
        self.assertEqual([m.reasons for m in tag_numbers("Comprei um número.", "pt-PT")],
                         [frozenset({Reason.ARTICLE})])

    def test_one_before_a_percent_phrase_is_the_number(self):
        # "un pour cent" is 1 %: the word counts the hundredths, so it is no article
        for text, lang, word in (("volume à un pour cent", "fr-FR", "un"), ("volum al un per cent", "ca", "un"),
                                 ("volum a un per cent", "oc", "un"), ("volume al uno per cento", "it", "uno"),
                                 ("άλλαξε στο ένα τοις εκατό την φωτεινότητα", "el", "ένα")):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.value, m.reasons) for m in tag_numbers(text, lang)],
                                 [(word, "1", frozenset())])
        # an article before "pour" with no "cent" after it stays an article
        self.assertEqual([(m.value, m.reasons) for m in tag_numbers("un livre pour cent euros", "fr-FR")],
                         [("1", frozenset({Reason.ARTICLE})), ("100", frozenset())])

    def test_an_article_that_is_the_whole_text_is_weak(self):
        # a line of a vocabulary file: the word has no noun to decide it
        for text, lang in (("um", "pt-PT"), ("uma", "pt-BR"), ("un", "gl"), ("unha", "gl"), ("egy", "hu"),
                           ("un", "ca"), ("una", "ca"), ("eine", "de"), ("einer", "de"), ("o", "ro")):
            with self.subTest(text=text, lang=lang):
                self.assertEqual([(m.text, m.reasons) for m in tag_numbers(text, lang)],
                                 [(text, frozenset({Reason.ARTICLE}))])
        # a number word that is no article, and an article inside a clause, stay sure
        self.assertEqual([m.reasons for m in tag_numbers("dois", "pt-PT")], [frozenset()])
        self.assertEqual([m.reasons for m in tag_numbers("Quero um.", "pt-PT")], [frozenset()])

    def test_the_package_exports_the_reason(self):
        self.assertIn("Reason", numtag.__all__)
        self.assertEqual({r.value for r in Reason}, {"article", "homograph"})

    def test_an_article_and_a_homograph_say_why_they_are_weak(self):
        found = tag_numbers("Dá-me um segundo facto e dois livros.", "pt-PT")
        self.assertEqual([(m.text, m.reasons) for m in found],
                         [("um", frozenset({Reason.ARTICLE})), ("segundo", frozenset({Reason.HOMOGRAPH})),
                          ("dois", frozenset())])

    def test_the_reason_matches_the_score(self):
        for text, lang in (("Comprei uma casa.", "pt-PT"), ("Wait a second.", "en"),
                           ("Er lud mich ein.", "de"), ("liburu bat", "eu")):
            for m in tag_numbers(text, lang):
                with self.subTest(text=text, mention=m.text):
                    expected = {0.3: {Reason.ARTICLE}, 0.4: {Reason.HOMOGRAPH}, 1.0: set()}[m.confidence]
                    self.assertEqual(m.reasons, expected)

    def test_reasons_must_be_a_frozenset_of_reasons(self):
        for bad in ({Reason.ARTICLE}, frozenset({"article"}), [Reason.ARTICLE]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                NumberMention((0, 3), "uma", "1", Kind.CARDINAL, Form.WORDS, confidence=0.3, reasons=bad)

    def test_reasons_are_keyword_only_and_not_part_of_equality(self):
        a = NumberMention((0, 3), "uma", "1", Kind.CARDINAL, Form.WORDS, confidence=0.3,
                          reasons=frozenset({Reason.ARTICLE}))
        self.assertEqual(a, NumberMention((0, 3), "uma", "1", Kind.CARDINAL, Form.WORDS))
        self.assertEqual(NumberMention((0, 3), "uma", "1", Kind.CARDINAL, Form.WORDS).reasons, frozenset())


class TestZeroDenominator(unittest.TestCase):
    def test_a_slash_fraction_over_zero_gives_no_mention(self):
        for text, lang in (("1/0", "en"), ("5/0 apples", "en"), ("0/00", "en"), ("1/0", "el"), ("1/0", "et"),
                           ("1/0", "sl"), ("١/٠", "ar")):
            with self.subTest(text=text, lang=lang):
                self.assertEqual(tag_numbers(text, lang), [])

    def test_other_slashes_keep_their_digits(self):
        self.assertEqual([m.value for m in tag_numbers("1/3", "en")], ["1", "3"])
        self.assertEqual([m.value for m in tag_numbers("3/0/2025", "en")], ["3", "0", "2025"])
        self.assertEqual([m.value for m in tag_numbers("twenty 1/0 five", "en")], ["20", "5"])

