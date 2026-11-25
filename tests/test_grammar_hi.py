"""Hindi grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/hi.json."""
import unittest

from helpers import read

C, O, D = "cardinal", "ordinal", "decimal"


def hi(text: str) -> list[tuple[str, str, str]]:
    return read(text, "hi")


class TestCardinals(unittest.TestCase):
    def test_each_number_below_a_hundred_is_one_word(self):
        # 42 and 99 have no tens-and-units rule
        self.assertEqual(hi("बयालीस"), [("बयालीस", "42", C)])
        self.assertEqual(hi("निन्यानबे"), [("निन्यानबे", "99", C)])

    def test_two_words_below_a_hundred_stay_two_numbers(self):
        # "बीस" 20 and "पाँच" 5 never join, because 25 is "पच्चीस"
        self.assertEqual(hi("बीस पाँच"), [("बीस", "20", C), ("पाँच", "5", C)])

    def test_a_count_before_sau_multiplies_it(self):
        # 2 x 100 + 50
        self.assertEqual(hi("दो सौ पचास"), [("दो सौ पचास", "250", C)])
        # 25 x 100
        self.assertEqual(hi("पच्चीस सौ"), [("पच्चीस सौ", "2500", C)])

    def test_sau_alone_is_no_number(self):
        self.assertEqual(hi("सौ"), [])

    def test_so_is_not_sau(self):
        # "सो" (sleep) has another vowel sign
        self.assertEqual(hi("वह सो गया।"), [])


class TestIndianScale(unittest.TestCase):
    def test_lakh_is_ten_to_the_fifth(self):
        # 1 x 10^5 + 25 x 1000
        self.assertEqual(hi("एक लाख पच्चीस हज़ार"), [("एक लाख पच्चीस हज़ार", "125000", C)])

    def test_crore_is_ten_to_the_seventh(self):
        # 2 x 10^7 + 1 x 10^5
        self.assertEqual(hi("दो करोड़ एक लाख"), [("दो करोड़ एक लाख", "20100000", C)])

    def test_arab_and_kharab(self):
        # 3 x 10^9, 12 x 10^9, 10^11
        self.assertEqual(hi("तीन अरब"), [("तीन अरब", "3000000000", C)])
        self.assertEqual(hi("एक खरब"), [("एक खरब", "100000000000", C)])


class TestOrdinals(unittest.TestCase):
    def test_one_to_six_are_irregular(self):
        self.assertEqual(hi("पहला"), [("पहला", "1", O)])
        self.assertEqual(hi("छठा"), [("छठा", "6", O)])

    def test_from_seven_the_ending_goes_on_the_cardinal(self):
        # सात 7, इक्कीस 21
        self.assertEqual(hi("सातवाँ"), [("सातवाँ", "7", O)])
        self.assertEqual(hi("इक्कीसवें"), [("इक्कीसवें", "21", O)])
        self.assertEqual(hi("पचासवी"), [("पचासवी", "50", O)])

    def test_the_oblique_and_feminine_forms(self):
        self.assertEqual(hi("दूसरे"), [("दूसरे", "2", O)])
        self.assertEqual(hi("तीसरी"), [("तीसरी", "3", O)])


class TestDecimals(unittest.TestCase):
    def test_dashamlav_and_the_point(self):
        self.assertEqual(hi("तीन दशमलव पाँच"), [("तीन दशमलव पाँच", "3.5", D)])
        self.assertEqual(hi("2.75 रुपये"), [("2.75", "2.75", D)])

    def test_rin_makes_a_number_negative(self):
        self.assertEqual(hi("ऋण पाँच"), [("ऋण पाँच", "-5", C)])
