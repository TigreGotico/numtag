import unittest
from decimal import Decimal
from fractions import Fraction

import numtag
from numtag import (ARTICLE_CONFIDENCE, Form, Kind, NumberMention, Reason, Scale, VagueKind, VagueQuantity,
                    is_canonical_value, tag_numbers)
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
                                 ("le nombre un est-il pair ?", "fr-FR", "un"),
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

    def test_number_words_beside_a_homograph_make_it_sure(self):
        # a whole number before the joiner, or a minus word, leaves no reading but the number
        for text, lang, words, value in (("Faltam três e um quarto.", "pt-PT", "três e um quarto", "3.25"),
                                         ("Faltam três e um quarto.", "pt-BR", "três e um quarto", "3.25"),
                                         ("Temperatuur oli miinus viis kraadi.", "et", "miinus viis", "-5"),
                                         ("دما به منفی ده رسید.", "fa", "منفی ده", "-10")):
            with self.subTest(text=text, lang=lang):
                self.assertEqual([(m.text, m.value, m.reasons) for m in tag_numbers(text, lang)],
                                 [(words, value, frozenset())])
        # the homograph alone, or a fraction on it alone, stays weak
        for text, lang in (("Bebeu um quarto da garrafa.", "pt-PT"), ("Õige arv on viis.", "et")):
            with self.subTest(text=text, lang=lang):
                self.assertEqual([m.reasons for m in tag_numbers(text, lang)], [frozenset({Reason.HOMOGRAPH})])

    def test_an_ordinal_one_with_a_second_meaning_is_weak(self):
        # fr "premier" is also "prime" and "original", it "primo" "prime", it "prima" "before"
        for text, lang, word in (("Le nombre sept est-il premier ?", "fr-FR", "premier"),
                                 ("Ces nombres sont premiers.", "fr-FR", "premiers"),
                                 ("Le premier jour.", "fr-FR", "premier"),
                                 ("Il sette è un numero primo.", "it", "primo"),
                                 ("Chiamami prima di cena.", "it", "prima")):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.value, m.reasons) for m in tag_numbers(text, lang) if m.text == word],
                                 [(word, "1", frozenset({Reason.HOMOGRAPH}))])
        # a compound ordinal is clear
        self.assertEqual([m.reasons for m in tag_numbers("le vingt et unième jour", "fr-FR")], [frozenset()])

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


class TestVagueQuantityValues(unittest.TestCase):
    """A scale is a positive whole number, a lower bound is not below its scale, and a
    confidence is a number from 0 to 1."""

    def magnitude(self, scale, lower_bound=None, **kwargs):
        return VagueQuantity((0, 8), "millions", VagueKind.MAGNITUDE, scale, lower_bound, **kwargs)

    def test_a_scale_that_is_not_a_positive_whole_number_is_refused(self):
        for scale in ("-5", "0", "1/3", "2.5", "007", "", "1e6", "1 000", "\u0661\u0660"):
            with self.subTest(scale=scale), self.assertRaises(ValueError):
                self.magnitude(scale)

    def test_a_lower_bound_below_the_scale_is_refused(self):
        for scale, bound in (("1000000", "5"), ("1000", "999"), ("20", "19"), ("1" + "0" * 600, "9" * 600)):
            with self.subTest(scale=scale[:8], bound=bound[:8]), self.assertRaises(ValueError):
                self.magnitude(scale, bound)

    def test_a_lower_bound_that_is_not_a_positive_whole_number_is_refused(self):
        for bound in ("-2000", "0", "2000.5", "4000/3"):
            with self.subTest(bound=bound), self.assertRaises(ValueError):
                self.magnitude("1000", bound)

    def test_a_confidence_outside_zero_to_one_is_refused(self):
        for confidence in (7.0, -0.1, 1.0001, float("nan"), float("inf"), "0.4", None, True):
            with self.subTest(confidence=confidence), self.assertRaises(ValueError):
                self.magnitude("1000", confidence=confidence)

    def test_valid_values_are_accepted(self):
        # 2 x 1000 = 2000; the lower bound may equal the scale or go above it; a dozen is 12
        for scale, bound, confidence in (("1000", "2000", 1.0), ("1000", "1000", 0.4), ("12", None, 0),
                                         ("1", None, 1), ("1" + "0" * 600, "2" + "0" * 600, 0.5)):
            with self.subTest(scale=scale[:8], bound=bound):
                self.assertEqual(self.magnitude(scale, bound, confidence=confidence).scale, scale)

    def test_an_amount_takes_a_confidence_in_range(self):
        with self.assertRaises(ValueError):
            VagueQuantity((0, 4), "many", VagueKind.AMOUNT, confidence=2.0)
        self.assertEqual(VagueQuantity((0, 4), "many", VagueKind.AMOUNT, confidence=0.4).confidence, 0.4)


def read(text: str, lang: str = "en") -> list[tuple[str, str, str]]:
    return [(m.text, m.value, m.kind.value) for m in tag_numbers(text, lang)]


class TestSlashFraction(unittest.TestCase):
    LANGUAGES = "bg da de en fr fy hr id nb nl nn pl ru sk sv".split()

    def test_a_proper_fraction_is_one_fraction_in_lowest_terms(self):
        for text, value in (("3/4", "0.75"),  # 3 / 4 = 0.75
                            ("1/3", "1/3"),  # no finite decimal form
                            ("2/4", "0.5"),  # 2/4 = 1/2
                            ("6/8", "0.75"),  # 6/8 = 3/4
                            ("7/12", "7/12"),  # gcd(7, 12) = 1
                            ("5/8", "0.625"),  # 625 / 1000
                            ("1/1000000", "0.000001")):
            for lang in self.LANGUAGES:
                with self.subTest(text=text, lang=lang):
                    self.assertEqual(read(text, lang), [(text, value, "fraction")])

    def test_a_fraction_in_a_sentence_keeps_the_text_around_it(self):
        self.assertEqual(read("Add 3/4 cup of milk, then 1/3 of the flour.", "en"),
                         [("3/4", "0.75", "fraction"), ("1/3", "1/3", "fraction")])
        self.assertEqual(read("(3/4)", "en"), [("3/4", "0.75", "fraction")])
        self.assertEqual(read("Das sind 2/3.", "de"), [("2/3", "2/3", "fraction")])

    def test_a_whole_number_before_the_fraction_makes_a_mixed_number(self):
        for text, value in (("5 1/2", "5.5"),  # 5 + 1/2
                            ("5 1/3", "16/3"),  # 5 + 1/3 = 16/3
                            ("20 1/2", "20.5"),
                            ("300 1/2", "300.5"),
                            ("-5 1/2", "-5.5"),  # the sign covers 5 + 1/2
                            ("-0 1/2", "-0.5"),
                            ("2 3/4", "2.75"),  # 2 + 3/4
                            ("4503599627370495 1/2", "4503599627370495.5"),  # no float: 2^52 - 1 + 1/2
                            ("5  1/2", "5.5")):
            for lang in self.LANGUAGES:
                with self.subTest(text=text, lang=lang):
                    self.assertEqual(read(text, lang), [(text, value, "fraction")])

    def test_a_whole_number_in_words_or_with_a_minus_word_makes_a_mixed_number(self):
        self.assertEqual(read("twenty 1/2"), [("twenty 1/2", "20.5", "fraction")])  # 20 + 1/2
        self.assertEqual(read("minus 5 1/2"), [("minus 5 1/2", "-5.5", "fraction")])
        self.assertEqual(read("minus 0 1/2"), [("minus 0 1/2", "-0.5", "fraction")])
        self.assertEqual(read("dwadzieścia 1/2", "pl"), [("dwadzieścia 1/2", "20.5", "fraction")])
        mention, = tag_numbers("x 3 1/2 y", "en")
        self.assertEqual((mention.char_span, mention.form), ((2, 7), Form.DIGITS))
        self.assertEqual(tag_numbers("twenty 1/2", "en")[0].form, Form.MIXED)

    def test_space_groups_do_not_swallow_the_numerator(self):
        for lang in ("nb", "nn", "sv", "fi"):
            with self.subTest(lang=lang):
                self.assertEqual(read("12 345 1/2", lang), [("12 345 1/2", "12345.5", "fraction")])
                self.assertEqual(read("5 1/2 og 3/4", lang),
                                 [("5 1/2", "5.5", "fraction"), ("3/4", "0.75", "fraction")])

    def test_a_group_of_three_digits_before_a_slash_stays_a_group(self):
        # "5 123/456": the space groups 5 123, so the fraction is 5123/456, above one
        self.assertEqual(read("5 123/456", "sv"), [("5 123", "5123", "cardinal"), ("456", "456", "cardinal")])

    def test_the_parts_name_the_terms(self):
        mention, = tag_numbers("-5 1/2", "en")
        self.assertEqual([(p.role.value, p.text, p.value) for p in mention.parts],
                         [("count", "-5", "-5"), ("count", "1", "1"), ("denominator", "2", "2")])
        mention, = tag_numbers("-3/4", "en")
        self.assertEqual([(p.role.value, p.text, p.value) for p in mention.parts],
                         [("count", "-3", "-3"), ("denominator", "4", "4")])
        self.assertEqual(mention.value, "-0.75")

    def test_a_signed_fraction_is_never_added_to_a_whole_number(self):
        self.assertEqual(read("5 -1/2"), [("5", "5", "cardinal"), ("-1/2", "-0.5", "fraction")])

    def test_a_signed_fraction_is_negative(self):
        self.assertEqual(read("-1/2"), [("-1/2", "-0.5", "fraction")])
        self.assertEqual(read("-2/3"), [("-2/3", "-2/3", "fraction")])

    def test_arabic_indic_digits_give_the_same_fraction(self):
        self.assertEqual(read("٣/٤", "ar"), [("٣/٤", "0.75", "fraction")])

    def test_a_fraction_that_is_not_below_one_keeps_its_two_numbers(self):
        # a ratio, a score or an idiom: 24/7 is "always", 50/50 is even odds, 16/9 is a screen
        for text in ("24/7", "50/50", "16/9", "3/2", "1/1", "6/3", "0/5"):
            with self.subTest(text=text):
                self.assertEqual([m.kind.value for m in tag_numbers(text, "en")], ["cardinal", "cardinal"])
        self.assertEqual(read("24/7"), [("24", "24", "cardinal"), ("7", "7", "cardinal")])
        self.assertEqual(read("x 5 3/2 y"), [("5", "5", "cardinal"), ("3", "3", "cardinal"), ("2", "2", "cardinal")])

    def test_a_chain_of_slashes_is_no_fraction(self):
        self.assertEqual(read("1/2/3"), [("1", "1", "cardinal"), ("2", "2", "cardinal"), ("3", "3", "cardinal")])
        self.assertEqual(read("12/05/2024"), [("12", "12", "cardinal"), ("05", "5", "cardinal"),
                                              ("2024", "2024", "cardinal")])
        self.assertEqual(read("1/2/3 1/2")[-1], ("1/2", "0.5", "fraction"))

    def test_a_term_with_a_leading_zero_is_no_fraction(self):
        # a day and a month: 03/04 is the third of April or the fourth of March
        for text in ("03/04", "1/02", "01/05", "0/1"):
            with self.subTest(text=text):
                self.assertEqual([m.kind.value for m in tag_numbers(text, "en")], ["cardinal", "cardinal"])

    def test_a_numerator_after_a_sign_is_no_fraction(self):
        self.assertEqual(read("5-1/2"), [("5", "5", "cardinal"), ("1", "1", "cardinal"), ("2", "2", "cardinal")])
        self.assertEqual(read("--3/2"), [("3", "3", "cardinal"), ("2", "2", "cardinal")])
        self.assertEqual(read("--1/2")[0][2], "cardinal")

    def test_a_space_around_the_slash_is_no_fraction(self):
        for text in ("3 / 4", "3/ 4", "3 /4"):
            with self.subTest(text=text):
                self.assertEqual([m.value for m in tag_numbers(text, "en")], ["3", "4"])

    def test_a_term_with_a_suffix_or_a_mark_is_no_fraction(self):
        self.assertEqual(read("1/2nd"), [("1", "1", "cardinal"), ("2nd", "2", "ordinal")])
        self.assertEqual(read("am 1/3. Mai", "de"), [("1", "1", "cardinal"), ("3", "3", "ordinal")])
        self.assertEqual(read("1/2. emelet", "hu"), [("1", "1", "cardinal"), ("2", "2", "ordinal")])
        self.assertEqual([m.value for m in tag_numbers("1.5/4", "en")], ["1.5", "4"])
        self.assertEqual([m.value for m in tag_numbers("1/2.5", "en")], ["1", "2.5"])

    def test_four_digits_with_no_group_mark_are_no_whole_part(self):
        # four digits are mostly a year: "In 2023 1/3 of adults" is the year 2023 and a third
        self.assertEqual(read("In 2023 1/3 of adults smoked."),
                         [("2023", "2023", "cardinal"), ("1/3", "1/3", "fraction")])
        self.assertEqual(read("In 2022 1/4 of the budget", "en"),
                         [("2022", "2022", "cardinal"), ("1/4", "0.25", "fraction")])
        self.assertEqual(read("-2023 1/2"), [("-2023", "-2023", "cardinal"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("minus 2023 1/2"), [("minus 2023", "-2023", "cardinal"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("menos 2023 1/2", "pt-PT"),
                         [("menos 2023", "-2023", "cardinal"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("2023 million 1/2"), [("2023 million 1/2", "2023000000.5", "fraction")])
        self.assertEqual(read("1.500 1/2", "pt-PT"), [("1.500 1/2", "1500.5", "fraction")])
        self.assertEqual(read("В 2023 1/3 взрослых курили.", "ru"),
                         [("2023", "2023", "cardinal"), ("1/3", "1/3", "fraction")])
        # a group mark, or three or five digits, still make a mixed number
        self.assertEqual(read("1,500 1/2"), [("1,500 1/2", "1500.5", "fraction")])  # 1500 + 1/2
        self.assertEqual(read("999 1/2"), [("999 1/2", "999.5", "fraction")])
        self.assertEqual(read("12345 1/2"), [("12345 1/2", "12345.5", "fraction")])

    def test_only_a_cardinal_before_the_fraction_makes_it_mixed(self):
        self.assertEqual(read("x 3.5 1/2 y"), [("3.5", "3.5", "decimal"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("-3.5 1/2"), [("-3.5", "-3.5", "decimal"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("-1/2 1/2"), [("-1/2", "-0.5", "fraction"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("1/2 1/2"), [("1/2", "0.5", "fraction"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("2nd 1/2"), [("2nd", "2", "ordinal"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("5 and a half 1/2")[-1], ("1/2", "0.5", "fraction"))

    def test_a_whole_number_that_is_a_term_of_another_slash_is_not_a_whole_part(self):
        self.assertEqual(read("24/7 1/2"), [("24", "24", "cardinal"), ("7", "7", "cardinal"),
                                            ("1/2", "0.5", "fraction")])

    def test_a_line_break_or_other_text_between_ends_the_mixed_number(self):
        self.assertEqual(read("5\n1/2"), [("5", "5", "cardinal"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("5, 1/2"), [("5", "5", "cardinal"), ("1/2", "0.5", "fraction")])
        self.assertEqual(read("5 of 1/2"), [("5", "5", "cardinal"), ("1/2", "0.5", "fraction")])

    def test_two_mixed_numbers_in_a_row_stay_two(self):
        self.assertEqual(read("1 1/2 2 1/3"), [("1 1/2", "1.5", "fraction"), ("2 1/3", "7/3", "fraction")])
        self.assertEqual(read("7 1/2 1/2"), [("7 1/2", "7.5", "fraction"), ("1/2", "0.5", "fraction")])

    def test_a_weak_whole_number_is_not_a_whole_part(self):
        self.assertEqual(read("una 1/2", "es"), [("una", "1", "cardinal"), ("1/2", "0.5", "fraction")])

    def test_a_zero_denominator_still_gives_no_mention(self):
        self.assertEqual(read("5 1/0"), [("5", "5", "cardinal")])
        self.assertEqual(read("1/0 and 1/2"), [("1/2", "0.5", "fraction")])


class TestZeroDenominator(unittest.TestCase):
    def test_a_slash_fraction_over_zero_gives_no_mention(self):
        for text, lang in (("1/0", "en"), ("5/0 apples", "en"), ("0/00", "en"), ("1/0", "el"), ("1/0", "et"),
                           ("1/0", "sl"), ("١/٠", "ar")):
            with self.subTest(text=text, lang=lang):
                self.assertEqual(tag_numbers(text, lang), [])

    def test_other_slashes_keep_their_digits(self):
        self.assertEqual([m.value for m in tag_numbers("3/0/2025", "en")], ["3", "0", "2025"])
        self.assertEqual([m.value for m in tag_numbers("twenty 1/0 five", "en")], ["20", "5"])

