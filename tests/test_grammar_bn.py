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

    def test_an_ordinal_past_ten_is_the_cardinal_and_tomo(self):
        # 58; 100 + 58 = 158; 1000; 1000 + 700 + 30 = 1730
        self.assertEqual(bn("দাদুর সংগ্রহের আটান্নতম ডাকটিকিটটাই ছিল সবচেয়ে দামি।"), [("আটান্নতম", "58", O)])
        self.assertEqual(bn("লাইব্রেরিটা এবার তার একশো আটান্নতম প্রতিষ্ঠাদিবস পালন করছে।"),
                         [("একশো আটান্নতম", "158", O)])
        self.assertEqual(bn("এটা আমাদের এক হাজারতম অনুষ্ঠান।"), [("এক হাজারতম", "1000", O)])
        self.assertEqual(bn("লাইনে আমি এক হাজার সাতশো ত্রিশতম।"), [("এক হাজার সাতশো ত্রিশতম", "1730", O)])

    def test_the_sanskrit_ordinals_from_eleven_to_twenty(self):
        # Wiktionary rows 11 and 20, Ordinal column
        self.assertEqual(bn("একাদশ শ্রেণির ছাত্র"), [("একাদশ", "11", O)])
        self.assertEqual(bn("বিংশ শতাব্দী"), [("বিংশ", "20", O)])

    def test_a_decimal_reads_each_digit_after_doshomik(self):
        # 337 + 0.97 = 337.97; 20 + 0.38 = 20.38
        self.assertEqual(bn("জমিটার মোট আয়তন তিনশো সাঁইত্রিশ দশমিক নয় সাত বর্গমিটার।"),
                         [("তিনশো সাঁইত্রিশ দশমিক নয় সাত", "337.97", "decimal")])
        self.assertEqual(bn("নদীর জলের তাপমাত্রা ছিল বিশ দশমিক তিন আট ডিগ্রি।"),
                         [("বিশ দশমিক তিন আট", "20.38", "decimal")])

    @pytest.mark.xfail(strict=True, raises=AssertionError,
                       reason="ঋণ is also 'loan, debt', so the reader does not take it as minus")
    def test_a_negative_takes_rin(self):
        # -(5) = -5
        self.assertEqual(bn("তাপমাত্রা ঋণ পাঁচ ডিগ্রি"), [("ঋণ পাঁচ", "-5", C)])

    def test_rin_the_loan_keeps_a_positive_number(self):
        # ঋণ "loan": 10 × 1000 = 10000 owed; 5 per cent
        self.assertEqual(bn("ব্যাংকের ঋণ দশ হাজার টাকা বাকি।"), [("দশ হাজার", "10000", C)])
        self.assertEqual(bn("কৃষি ঋণ পাঁচ শতাংশ সুদে দেওয়া হয়।"), [("পাঁচ", "5", C)])

    def test_adha_is_a_half(self):
        self.assertEqual(bn("মা আধা কেজি মিষ্টি কিনে আনলেন।"), [("আধা", "0.5", F)])

    def test_half(self):
        self.assertEqual(bn("আধ"), [("আধ", "0.5", F)])


class TestOpenIssues(unittest.TestCase):
    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/363")
    def test_indian_digit_grouping(self):
        # 1,00,000 is one lakh: 100000
        self.assertEqual(bn("১,০০,০০০"), [("১,০০,০০০", "100000", C)])

