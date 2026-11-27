"""Bengali grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/bn.json."""
import unittest

import pytest

from helpers import read

C, O, F = "cardinal", "ordinal", "fraction"


def bn(text: str) -> list[tuple[str, str, str]]:
    return read(text, "bn")


class TestCardinals(unittest.TestCase):
    def test_each_number_below_a_hundred_is_one_word(self):
        # 27 has two forms, and 99 has no tens-and-units rule
        self.assertEqual(bn("সাতাশ"), [("সাতাশ", "27", C)])
        self.assertEqual(bn("নিরানব্বই"), [("নিরানব্বই", "99", C)])

    def test_two_words_below_a_hundred_stay_two_numbers(self):
        # "বিশ" 20 and "পাঁচ" 5 never join, because 25 is "পঁচিশ"
        self.assertEqual(bn("বিশ পাঁচ"), [("বিশ", "20", C), ("পাঁচ", "5", C)])

    def test_the_hundred_takes_a_count(self):
        # 2 * 100 = 200; 5 * 100 + 50 = 550
        self.assertEqual(bn("দুই শ"), [("দুই শ", "200", C)])
        self.assertEqual(bn("পাঁচ শ পঞ্চাশ"), [("পাঁচ শ পঞ্চাশ", "550", C)])

    def test_the_one_word_hundreds_take_a_rest(self):
        # 6000 + 700 + 99 = 6799; 13000 + 900 + 1 = 13901; 100 + 1 = 101
        self.assertEqual(bn("ছয় হাজার সাতশো নিরানব্বই"), [("ছয় হাজার সাতশো নিরানব্বই", "6799", C)])
        self.assertEqual(bn("তেরো হাজার নয়শো এক"), [("তেরো হাজার নয়শো এক", "13901", C)])
        self.assertEqual(bn("একশ এক"), [("একশ এক", "101", C)])
        self.assertEqual(bn("দুশো"), [("দুশো", "200", C)])
        self.assertEqual(bn("দুইশো পাঁচ"), [("দুইশো পাঁচ", "205", C)])

    def test_a_hundred_counts_the_koti(self):
        # (100 + 47) * 10^7 = 1470000000
        self.assertEqual(bn("একশো সাতচল্লিশ কোটি"), [("একশো সাতচল্লিশ কোটি", "1470000000", C)])

    def test_a_glued_classifier_ends_the_number(self):
        # the classifier adds nothing: 21, 47, 3, 2, 482
        self.assertEqual(bn("একুশটি"), [("একুশটি", "21", C)])
        self.assertEqual(bn("সাতচল্লিশটা"), [("সাতচল্লিশটা", "47", C)])
        self.assertEqual(bn("তিনটে"), [("তিনটে", "3", C)])
        self.assertEqual(bn("দুটো"), [("দুটো", "2", C)])
        self.assertEqual(bn("চারশো বিরাশিটি"), [("চারশো বিরাশিটি", "482", C)])
        self.assertEqual(bn("পাঁচখানা"), [("পাঁচখানা", "5", C)])
        self.assertEqual(bn("দুজন"), [("দুজন", "2", C)])

    def test_the_indian_scale(self):
        # 3 * 10^7 + 50 * 10^5 = 35000000; 10 * 10^5 = 1000000
        self.assertEqual(bn("তিন কোটি পঞ্চাশ লাখ"), [("তিন কোটি পঞ্চাশ লাখ", "35000000", C)])
        self.assertEqual(bn("দশ লক্ষ"), [("দশ লক্ষ", "1000000", C)])


class TestOrdinalsAndHalf(unittest.TestCase):
    def test_the_first_ten_ordinals(self):
        self.assertEqual(bn("প্রথম"), [("প্রথম", "1", O)])
        self.assertEqual(bn("দশম"), [("দশম", "10", O)])

    def test_half(self):
        self.assertEqual(bn("আধ"), [("আধ", "0.5", F)])


class TestOpenIssues(unittest.TestCase):
    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/363")
    def test_indian_digit_grouping(self):
        # 1,00,000 is one lakh: 100000
        self.assertEqual(bn("১,০০,০০০"), [("১,০০,০০০", "100000", C)])

