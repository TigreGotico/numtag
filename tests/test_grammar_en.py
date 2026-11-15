"""English grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/en.json."""
import time
import unittest

from helpers import read
from numtag import Scale, tag_numbers

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
        # a second group of the same scale starts a new number
        self.assertEqual(en("ten thousand two thousand"), [("ten thousand", "10000", C), ("two thousand", "2000", C)])
        self.assertEqual(en("two hundred million ten million"),
                         [("two hundred million", "200000000", C), ("ten million", "10000000", C)])

    def test_a_count_belongs_to_the_multiplier_after_it(self):
        self.assertEqual(en("one hundred and two hundred"),
                         [("one hundred", "100", C), ("two hundred", "200", C)])

    def test_a_cardinal_counts_a_larger_scale_noun(self):
        # (2000 + 500) x 10^6; 1000 x 10^6; 10000 x 10^6
        self.assertEqual(en("two thousand five hundred million"),
                         [("two thousand five hundred million", "2500000000", C)])
        self.assertEqual(en("a thousand million"), [("a thousand million", "1000000000", C)])
        self.assertEqual(en("ten thousand million"), [("ten thousand million", "10000000000", C)])

    def test_only_a_cardinal_with_thousand_counts_a_larger_scale_noun(self):
        self.assertEqual(en("between two million and three billion dollars"),
                         [("two million", "2000000", C), ("three billion", "3000000000", C)])
        self.assertEqual(en("one million two billion"),
                         [("one million", "1000000", C), ("two billion", "2000000000", C)])

    def test_a_group_fits_below_the_digits_of_the_count_before_it(self):
        # 2500 x 10^6 leaves eight zeros; 600 x 10^6 has nine digits
        self.assertEqual(en("two thousand five hundred million and six hundred million"),
                         [("two thousand five hundred million", "2500000000", C),
                          ("six hundred million", "600000000", C)])
        # 2 x 10^6 leaves six zeros; 1500 x 10^3 has seven digits
        self.assertEqual(en("two million fifteen hundred thousand"),
                         [("two million", "2000000", C), ("fifteen hundred thousand", "1500000", C)])
        self.assertEqual(en("one million and fifteen hundred thousand"),
                         [("one million", "1000000", C), ("fifteen hundred thousand", "1500000", C)])

    def test_a_count_of_several_words_after_a_group_starts_a_new_number(self):
        # 10^9; 2500 x 10^6
        self.assertEqual(en("between one billion and two thousand five hundred million"),
                         [("one billion", "1000000000", C), ("two thousand five hundred million", "2500000000", C)])

    def test_a_count_below_a_thousand_belongs_to_the_scale_word_after_it(self):
        # 10^6; 25 x 10^6
        self.assertEqual(en("between one million and twenty-five million dollars"),
                         [("one million", "1000000", C), ("twenty-five million", "25000000", C)])
        # 2 x 10^6; 150 x 10^6
        self.assertEqual(en("between two million and one hundred and fifty million"),
                         [("two million", "2000000", C), ("one hundred and fifty million", "150000000", C)])
        # with no range cue too
        self.assertEqual(en("two million and one hundred and fifty million"),
                         [("two million", "2000000", C), ("one hundred and fifty million", "150000000", C)])

    def test_a_well_formed_count_with_thousand_and_counts_a_larger_noun(self):
        # (500000 + 2) x 10^6 = 500002000000
        self.assertEqual(en("five hundred thousand and two million"),
                         [("five hundred thousand and two million", "500002000000", C)])

    def test_and_after_thousand_takes_only_a_last_group_below_a_hundred(self):
        # "two thousand and five hundred" is no count of "million": 2000 and
        # 500 x 10^6
        self.assertEqual(en("two thousand and five hundred million"),
                         [("two thousand", "2000", C), ("five hundred million", "500000000", C)])
        # 2000 + 1 = 2001: a group below a hundred
        self.assertEqual(en("two thousand and one million"),
                         [("two thousand and one million", "2001000000", C)])

    def test_two_numbers_split_where_the_fewest_digits_are(self):
        # 2000 and 150 x 1000 tie with 2100 and 50 x 1000 on significant
        # digits (1 + 2 = 2 + 1); a split inside "one hundred and fifty"
        # wins only with fewer digits
        self.assertEqual(en("two thousand and one hundred and fifty thousand"),
                         [("two thousand", "2000", C), ("one hundred and fifty thousand", "150000", C)])
        # 10^9 and 1500 x 10^6: 1 + 2 = 3, against 1000001000 and 500 x 10^6: 7 + 1 = 8
        self.assertEqual(en("one thousand million and one thousand five hundred million"),
                         [("one thousand million", "1" + "0" * 9, C),
                          ("one thousand five hundred million", "15" + "0" * 8, C)])
        # A split keeps the words of the second number: "one thousand and
        # five hundred" is no count of "million", so 10^9 + 1000 and 500 x 10^6
        self.assertEqual(en("a thousand million and one thousand and five hundred million"),
                         [("a thousand million and one thousand", "1000001000", C),
                          ("five hundred million", "500000000", C)])

    def test_a_joiner_at_the_end_of_the_words_splits_nothing(self):
        self.assertEqual(en("between two and"), [("two", "2", C)])
        self.assertEqual(en("between -1 and"), [("-1", "-1", C)])
        # digits glued to a word are dropped, so "and20" leaves a final joiner
        self.assertEqual(en("between 15 and20"), [("15", "15", C)])

    def test_a_scale_word_keeps_the_singular_after_a_count(self):
        self.assertEqual(en("two million"), [("two million", "2000000", C)])
        # (1000 + 1) x 10^6
        self.assertEqual(en("one thousand and one million"),
                         [("one thousand and one million", "1001000000", C)])

    def test_the_first_number_takes_a_plain_group_before_a_compound_count(self):
        # 10^6 + 500 x 1000 = 1500000; 2 x 10^6
        self.assertEqual(en("one million five hundred thousand and two million"),
                         [("one million five hundred thousand", "1500000", C), ("two million", "2000000", C)])

    def test_a_range_cue_ends_the_first_number_at_the_range_joiner(self):
        # 500 x 1000; 2 x 10^6
        self.assertEqual(en("between five hundred thousand and two million"),
                         [("five hundred thousand", "500000", C), ("two million", "2000000", C)])
        # 10^6 + 200 x 1000 = 1200000; 2 x 10^6
        self.assertEqual(en("between one million two hundred thousand and two million"),
                         [("one million two hundred thousand", "1200000", C), ("two million", "2000000", C)])
        # 2000 and 150000 tie with 2100 and 50000 on significant digits; a
        # split inside "one hundred and fifty" wins only with fewer digits
        self.assertEqual(en("between two thousand and one hundred and fifty thousand"),
                         [("two thousand", "2000", C), ("one hundred and fifty thousand", "150000", C)])

    def test_a_group_that_counts_the_scale_word_after_it_starts_a_new_number(self):
        # "two million" counts "billion", so it does not join "one trillion";
        # the reading of "two million billion" is plan open question 6
        self.assertEqual(en("one trillion two million billion")[0], ("one trillion", "1000000000000", C))

    def test_a_scale_noun_after_a_group_starts_a_new_number(self):
        # 2000 x 10^6; 3000 x 10^6
        self.assertEqual(en("two thousand million and three thousand million"),
                         [("two thousand million", "2000000000", C), ("three thousand million", "3000000000", C)])

    def test_an_ordinal_scale_word_names_the_scale(self):
        mentions = tag_numbers("the billionth visitor", "en")
        self.assertEqual([(m.value, m.kind.value, m.number_scale) for m in mentions],
                         [("1" + "0" * 9, O, Scale.SHORT)])

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

    def test_a_billion_class_word_names_the_scale_of_its_value(self):
        mentions = tag_numbers("one billion", "en")
        self.assertEqual([(m.value, m.number_scale) for m in mentions], [("1" + "0" * 9, Scale.SHORT)])
        mentions = tag_numbers("one billion", "en", scale=Scale.LONG)
        self.assertEqual([(m.value, m.number_scale) for m in mentions], [("1" + "0" * 12, Scale.LONG)])

    def test_a_value_that_is_the_same_in_both_scales_has_no_scale(self):
        for text in ("a million", "two thousand", "1,000,000,000", "a thousand million"):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.number_scale) for m in tag_numbers(text, "en")],
                                 [(text, None)])

    def test_a_centillion(self):
        # short scale 10^(3 x 100 + 3)
        self.assertEqual(en("a centillion")[0][1], "1" + "0" * 303)

    def test_an_en_region_tag_reads_en(self):
        self.assertEqual(read("twenty-one", "en-US"), [("twenty-one", "21", C)])


    def test_a_last_round_group_joins_with_or_without_and(self):
        # English "and" before the last group is optional (Cambridge
        # Dictionary, "Numbers"): 1000 + 200, 1000 + 2, 2000000 + 500000
        self.assertEqual(en("one thousand two hundred"), [("one thousand two hundred", "1200", C)])
        self.assertEqual(en("one thousand two"), [("one thousand two", "1002", C)])
        self.assertEqual(en("one thousand and two"), [("one thousand and two", "1002", C)])
        self.assertEqual(en("two million five hundred thousand"),
                         [("two million five hundred thousand", "2500000", C)])

    def test_a_comma_links_a_class_of_a_hundred_or_more(self):
        # 2 x 10^6 + 300 x 10^3 = 2300000; before a group below a hundred the
        # comma ends the number
        self.assertEqual(en("two million, three hundred thousand"), [("two million, three hundred thousand", "2300000", C)])
        self.assertEqual(en("one thousand, nine hundred"), [("one thousand, nine hundred", "1900", C)])
        self.assertEqual(en("two thousand, five"), [("two thousand", "2000", C), ("five", "5", C)])
        self.assertEqual(en("five million, three million"), [("five million", "5000000", C), ("three million", "3000000", C)])

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

    def test_an_article_before_a_half(self):
        # 10^6 / 2 = 500000; 12 / 2 = 6
        self.assertEqual(en("a half million"), [("a half million", "500000", C)])
        self.assertEqual(en("a half dozen eggs"), [("a half dozen", "6", C)])
        self.assertEqual(en("a half"), [("a half", "0.5", F)])


class TestFractions(unittest.TestCase):
    def test_numerator_and_denominator(self):
        self.assertEqual(en("a third"), [("a third", "1/3", F)])
        self.assertEqual(en("two thirds"), [("two thirds", "2/3", F)])
        self.assertEqual(en("three quarters"), [("three quarters", "0.75", F)])
        self.assertEqual(en("one hundredth"), [("one hundredth", "0.01", F)])

    def test_a_fraction_of_a_collective_is_that_part_of_it(self):
        # 12 / 3 = 4; 3 x 12 / 4 = 9
        self.assertEqual(en("one third of a dozen"), [("one third of a dozen", "4", C)])
        self.assertEqual(en("three quarters of a dozen eggs"), [("three quarters of a dozen", "9", C)])

    def test_a_count_before_a_singular_ordinal_is_an_ordinal(self):
        # 20 + 3 = 23
        self.assertEqual(en("twenty third"), [("twenty third", "23", O)])


class TestOrdinals(unittest.TestCase):
    def test_only_the_last_word_is_ordinal(self):
        # 20 + 1 = 21; 100 + 1 = 101
        self.assertEqual(en("twenty-first"), [("twenty-first", "21", O)])
        self.assertEqual(en("one hundred and first"), [("one hundred and first", "101", O)])
        self.assertEqual(en("one hundred twenty-third"), [("one hundred twenty-third", "123", O)])

    def test_a_unit_ordinal_joins_a_ten_as_a_unit_does(self):
        # "ten" is below 21 and takes no unit; a ten and a unit take no "and"
        self.assertEqual(en("ten fifth"), [("ten", "10", C), ("fifth", "5", O)])
        self.assertEqual(en("forty and eighth"), [("forty", "40", C), ("eighth", "8", O)])
        self.assertEqual(en("forty eighth"), [("forty eighth", "48", O)])
        self.assertEqual(en("two thousand and fifth"), [("two thousand and fifth", "2005", O)])

    def test_an_ordinal_scale_word(self):
        # 2 x 100 = 200
        self.assertEqual(en("hundredth"), [("hundredth", "100", O)])
        self.assertEqual(en("two hundredth"), [("two hundredth", "200", O)])

    def test_an_ordinal_scale_word_multiplies_only_the_last_group(self):
        # 6000 + 2 x 100 = 6200; 1000 + 2 x 100 = 1200; 156000 + 2 x 100 = 156200
        self.assertEqual(en("six thousand two hundredth"), [("six thousand two hundredth", "6200", O)])
        self.assertEqual(en("one thousand two hundredth"), [("one thousand two hundredth", "1200", O)])
        self.assertEqual(en("one hundred fifty-six thousand two hundredth"),
                         [("one hundred fifty-six thousand two hundredth", "156200", O)])
        # 8 x 10^12 + 830 x 10^9 + 874 x 10^6 + 156 x 10^3 + 2 x 100
        text = "eight trillion eight hundred thirty billion eight hundred seventy-four million one hundred fifty-six thousand two hundredth"
        self.assertEqual(en(text), [(text, "8830874156200", O)])
        # 2000000 + 300 x 1000 = 2300000; 10^9 + 5 x 1000 = 1000005000
        self.assertEqual(en("two million three hundred thousandth"),
                         [("two million three hundred thousandth", "2300000", O)])
        self.assertEqual(en("one billion five thousandth"), [("one billion five thousandth", "1000005000", O)])
        # 10^9 + 200 x 10^6 = 1200000000; 3 x 10^12 + 4 x 10^6 = 3000004000000
        self.assertEqual(en("one billion two hundred millionth"),
                         [("one billion two hundred millionth", "1200000000", O)])
        self.assertEqual(en("three trillion four millionth"), [("three trillion four millionth", "3000004000000", O)])
        # one group: 200 x 1000 = 200000
        self.assertEqual(en("two hundred thousandth"), [("two hundred thousandth", "200000", O)])
        # 2 x 1000 does not fit below "one thousand": no reading of 3000
        self.assertEqual(en("one thousand two thousandth"),
                         [("one thousand two", "1002", C), ("thousandth", "1000", O)])

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
        self.assertEqual(en("three point one four one six"), [("three point one four one six", "3.1416", D)])

    def test_a_multiplier_after_the_decimals_multiplies_the_decimal(self):
        # 1.2 x 100, as "one point two million" is 1.2 x 10^6
        self.assertEqual(en("one point two hundred"), [("one point two hundred", "120", C)])
        # 1.25 x 100
        self.assertEqual(en("one point two five hundred"), [("one point two five hundred", "125", C)])
        self.assertEqual(en("one point two million"), [("one point two million", "1200000", C)])

    def test_a_ten_and_its_unit_after_point_are_one_part(self):
        # 3 + 25/100 = 3.25, not 3.205
        self.assertEqual(en("three point twenty five"), [("three point twenty five", "3.25", D)])
        self.assertEqual(en("three point twenty-five"), [("three point twenty-five", "3.25", D)])
        self.assertEqual(en("zero point one two three"), [("zero point one two three", "0.123", D)])

    def test_a_long_decimal_reads_in_linear_time(self):
        # 16 pairs "twenty one" took 22 s when every split was a reading
        text = "three point" + " twenty one" * 16
        started = time.perf_counter()
        mentions = en(text)
        elapsed = time.perf_counter() - started
        self.assertEqual(mentions, [(text, "3." + "21" * 16, D)])
        self.assertLess(elapsed, 0.5)

    def test_digit_marks(self):
        self.assertEqual(en("1,000,000.5"), [("1,000,000.5", "1000000.5", D)])
        self.assertEqual(en("1.5"), [("1.5", "1.5", D)])
        self.assertEqual(en("1,5"), [])

    def test_a_lone_decimal_point_before_digits(self):
        self.assertEqual(en("about .5 percent"), [(".5", "0.5", D)])
        # the comma only groups digits
        self.assertEqual(en(",5"), [("5", "5", C)])
        self.assertEqual(en("about -.5 percent"), [("-.5", "-0.5", D)])

    def test_a_decimal_point_after_a_leading_zero(self):
        self.assertEqual(en("weighs 0.500 kg"), [("0.500", "0.5", D)])
        # the comma groups digits, and a group never follows a leading zero
        self.assertEqual(en("weighs 0,500 kg"), [])

    def test_a_whole_value_is_cardinal_even_with_a_decimal_point(self):
        self.assertEqual(en("two point zero"), [("two point zero", "2", C)])

    def test_digits_and_a_scale_word(self):
        self.assertEqual(en("3 million"), [("3 million", "3000000", C)])


class TestNonAsciiDigits(unittest.TestCase):
    def test_digits_of_other_scripts_are_no_number(self):
        for text in ("٣", "３", "१२", "1٣", "١٢٣٤"):
            with self.subTest(text=text):
                self.assertEqual(en(f"I have {text} apples"), [])


class TestMinusAndArticles(unittest.TestCase):
    def test_minus_words(self):
        self.assertEqual(en("minus five"), [("minus five", "-5", C)])
        self.assertEqual(en("negative two point five"), [("negative two point five", "-2.5", D)])

    def test_a_minus_word_with_no_number_after_it_is_no_number(self):
        for text in ("the temperature is negative", "that is negative, sadly", "minus"):
            with self.subTest(text=text):
                self.assertEqual(en(text), [])

    def test_an_article_alone_is_no_number(self):
        self.assertEqual(en("I have a dog"), [])

    def test_one_is_a_numeral(self):
        mentions = tag_numbers("one dog", "en")
        self.assertEqual([(m.value, m.confidence) for m in mentions], [("1", 1.0)])


if __name__ == "__main__":
    unittest.main()
