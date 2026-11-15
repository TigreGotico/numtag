"""English grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/en.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def en(text: str, **options) -> list[tuple[str, str, str]]:
    return read(text, "en", **options)


class TestCardinals(unittest.TestCase):
    def test_a_ten_cannot_follow_a_unit(self):
        self.assertEqual(en("twenty one twenty"), [("twenty one", "21", C), ("twenty", "20", C)])

    def test_tens_and_units_take_a_hyphen_or_a_space(self):
        self.assertEqual(en("twenty-one"), [("twenty-one", "21", C)])
        self.assertEqual(en("twenty and one"), [("twenty", "20", C), ("one", "1", C)])

    def test_and_after_hundred_is_optional(self):
        # 100 + 5 = 105
        self.assertEqual(en("one hundred and five"), [("one hundred and five", "105", C)])
        self.assertEqual(en("one hundred five"), [("one hundred five", "105", C)])
        self.assertEqual(en("a hundred and one dalmatians"), [("a hundred and one", "101", C)])

    def test_hundreds_counted_by_a_teen(self):
        # 12 x 100 = 1200
        self.assertEqual(en("twelve hundred"), [("twelve hundred", "1200", C)])

    def test_groups_descend(self):
        # 2 x 10^6 + 300 x 10^3 = 2300000; 2000 + 5 = 2005
        self.assertEqual(en("two million three hundred thousand"),
                         [("two million three hundred thousand", "2300000", C)])
        self.assertEqual(en("two thousand and five"), [("two thousand and five", "2005", C)])

    def test_a_count_belongs_to_the_multiplier_after_it(self):
        self.assertEqual(en("one hundred and two hundred"),
                         [("one hundred", "100", C), ("two hundred", "200", C)])

    def test_a_scale_noun_needs_a_count(self):
        self.assertEqual(en("a million"), [("a million", "1000000", C)])
        self.assertEqual(en("the million"), [])
        self.assertEqual(en("hundred"), [])

    def test_a_plural_with_no_count_is_no_number(self):
        for text in ("millions of people", "thousands of years", "hundreds of birds", "dozens of eggs"):
            with self.subTest(text=text):
                self.assertEqual(en(text), [])

    def test_the_short_scale_and_the_long_scale(self):
        self.assertEqual(en("a billion")[0][1], "1" + "0" * 9)
        self.assertEqual(en("a billion", scale="long")[0][1], "1" + "0" * 12)
        # short scale: 10^(3 x 10 + 3)
        self.assertEqual(en("a decillion")[0][1], "1" + "0" * 33)

    def test_a_centillion(self):
        # short scale 10^(3 x 100 + 3)
        self.assertEqual(en("a centillion")[0][1], "1" + "0" * 303)

    def test_an_en_region_tag_reads_en(self):
        self.assertEqual(read("twenty-one", "en-US"), [("twenty-one", "21", C)])


class TestCollectivesAndHalves(unittest.TestCase):
    def test_dozen(self):
        # 12; 2 x 12 = 24
        self.assertEqual(en("a dozen eggs"), [("a dozen", "12", C)])
        self.assertEqual(en("two dozen"), [("two dozen", "24", C)])

    def test_half_a_dozen_and_a_dozen_and_a_half(self):
        # 12 / 2 = 6; 12 + 6 = 18
        self.assertEqual(en("half a dozen"), [("half a dozen", "6", C)])
        self.assertEqual(en("a dozen and a half"), [("a dozen and a half", "18", C)])

    def test_score_takes_an_addend(self):
        # 4 x 20 + 7 = 87
        self.assertEqual(en("four score and seven years ago"), [("four score and seven", "87", C)])

    def test_a_half_after_a_scale_noun_is_half_the_noun(self):
        # 10^6 + 10^6 / 2 = 1500000
        self.assertEqual(en("a million and a half"), [("a million and a half", "1500000", C)])

    def test_a_whole_and_a_half_counts_a_scale(self):
        # 2.5 x 10^6 = 2500000
        self.assertEqual(en("two and a half million"), [("two and a half million", "2500000", C)])

    def test_a_whole_and_a_half(self):
        self.assertEqual(en("two and a half"), [("two and a half", "2.5", F)])

    def test_half_a_million(self):
        self.assertEqual(en("half a million"), [("half a million", "500000", C)])


class TestFractions(unittest.TestCase):
    def test_numerator_and_denominator(self):
        self.assertEqual(en("a third"), [("a third", "1/3", F)])
        self.assertEqual(en("two thirds"), [("two thirds", "2/3", F)])
        self.assertEqual(en("three quarters"), [("three quarters", "0.75", F)])
        self.assertEqual(en("one hundredth"), [("one hundredth", "0.01", F)])

    def test_a_count_before_a_singular_ordinal_is_an_ordinal(self):
        # 20 + 3 = 23
        self.assertEqual(en("twenty third"), [("twenty third", "23", O)])


class TestOrdinals(unittest.TestCase):
    def test_only_the_last_word_is_ordinal(self):
        # 20 + 1 = 21; 100 + 1 = 101
        self.assertEqual(en("twenty-first"), [("twenty-first", "21", O)])
        self.assertEqual(en("one hundred and first"), [("one hundred and first", "101", O)])
        self.assertEqual(en("one hundred twenty-third"), [("one hundred twenty-third", "123", O)])

    def test_an_ordinal_scale_word(self):
        # 2 x 100 = 200
        self.assertEqual(en("hundredth"), [("hundredth", "100", O)])
        self.assertEqual(en("two hundredth"), [("two hundredth", "200", O)])

    def test_an_ordinal_cannot_fill_a_place_already_taken(self):
        self.assertEqual(en("twenty-one first"), [("twenty-one", "21", C), ("first", "1", O)])

    def test_digit_ordinals(self):
        self.assertEqual(en("the 21st and the 3rd"), [("21st", "21", O), ("3rd", "3", O)])

    def test_second_is_marked_ambiguous(self):
        # "second" is also a unit of time, so it gets a weak score
        mentions = tag_numbers("read the second chapter", "en")
        self.assertEqual([m.value for m in mentions], ["2"])
        self.assertLess(mentions[0].confidence, 0.5)


class TestDecimalsAndDigits(unittest.TestCase):
    def test_point(self):
        self.assertEqual(en("two point five"), [("two point five", "2.5", D)])
        self.assertEqual(en("zero point zero five"), [("zero point zero five", "0.05", D)])

    def test_digit_marks(self):
        self.assertEqual(en("1,000,000.5"), [("1,000,000.5", "1000000.5", D)])
        self.assertEqual(en("1.5"), [("1.5", "1.5", D)])
        self.assertEqual(en("1,5"), [])

    def test_a_whole_value_is_cardinal_even_with_a_decimal_point(self):
        self.assertEqual(en("two point zero"), [("two point zero", "2", C)])

    def test_digits_and_a_scale_word(self):
        self.assertEqual(en("3 million"), [("3 million", "3000000", C)])


class TestMinusAndArticles(unittest.TestCase):
    def test_minus_words(self):
        self.assertEqual(en("minus five"), [("minus five", "-5", C)])
        self.assertEqual(en("negative two point five"), [("negative two point five", "-2.5", D)])

    def test_an_article_alone_is_no_number(self):
        self.assertEqual(en("I have a dog"), [])

    def test_one_is_a_numeral(self):
        mentions = tag_numbers("one dog", "en")
        self.assertEqual([(m.value, m.confidence) for m in mentions], [("1", 1.0)])


if __name__ == "__main__":
    unittest.main()
