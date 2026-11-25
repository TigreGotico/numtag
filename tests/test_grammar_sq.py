"""Albanian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/sq.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C = "cardinal"


def sq(text: str) -> list[tuple[str, str, str]]:
    return read(text, "sq")


class TestCardinals(unittest.TestCase):
    def test_e_joins_a_ten_and_a_unit(self):
        # 20 + 5
        self.assertEqual(sq("njëzet e pesë"), [("njëzet e pesë", "25", C)])
        # 50 is pesë + dhjetë in one word, then 50 + 7
        self.assertEqual(sq("pesëdhjetë e shtatë"), [("pesëdhjetë e shtatë", "57", C)])

    def test_a_teen_is_a_unit_and_mbëdhjetë_in_one_word(self):
        # 3 + 10, 9 + 10
        self.assertEqual(sq("trembëdhjetë"), [("trembëdhjetë", "13", C)])
        self.assertEqual(sq("nëntëmbëdhjetë"), [("nëntëmbëdhjetë", "19", C)])

    def test_a_hundred_is_a_count_and_qind_in_one_word(self):
        # 2 x 100 + 30 + 8
        self.assertEqual(sq("dyqind e tridhjetë e tetë"), [("dyqind e tridhjetë e tetë", "238", C)])

    def test_the_thousands_stand_apart_and_e_joins_the_rest(self):
        # 2 x 1000 + 3 x 100
        self.assertEqual(sq("dy mijë e treqind"), [("dy mijë e treqind", "2300", C)])
        # 12 x 1000
        self.assertEqual(sq("dymbëdhjetë mijë"), [("dymbëdhjetë mijë", "12000", C)])

    def test_without_e_two_numbers_stay_two(self):
        # "dy" and "tre" with no joiner
        self.assertEqual(sq("dy tre"), [("dy", "2", C), ("tre", "3", C)])


class TestLargeNumbers(unittest.TestCase):
    def test_the_scale_is_long(self):
        # a milliard is 10^9 and a bilion 10^12
        self.assertEqual(sq("tre miliarë"), [("tre miliarë", "3000000000", C)])
        self.assertEqual(sq("dy bilionë"), [("dy bilionë", "2000000000000", C)])

    def test_the_count_of_a_plural_scale_noun_takes_the_feminine_three(self):
        # 20 + 3 million, "tri" is the feminine of "tre"
        self.assertEqual(sq("njëzet e tre milionë"), [("njëzet e tre milionë", "23000000", C)])

    def test_the_singular_scale_noun_takes_only_one(self):
        # "dy milion" is the count 2 and a scale noun that counts nothing
        self.assertEqual(sq("dy milion"), [("dy", "2", C)])
        self.assertEqual(sq("një milion e dyqind mijë"), [("një milion e dyqind mijë", "1200000", C)])


class TestArticle(unittest.TestCase):
    def test_një_before_a_noun_is_the_indefinite_article(self):
        mentions = read("Dua një gotë ujë.", "sq")
        self.assertEqual(mentions, [("një", "1", C)])
        self.assertLess(tag_numbers("Dua një gotë ujë.", "sq")[0].confidence, 0.5)


class TestDecimals(unittest.TestCase):
    def test_presje_and_the_comma(self):
        self.assertEqual(sq("tre presje pesë"), [("tre presje pesë", "3.5", "decimal")])
        self.assertEqual(sq("2,75 kg"), [("2,75", "2.75", "decimal")])

    def test_a_no_break_space_groups_digits(self):
        self.assertEqual(sq("10 000 lekë"), [("10 000", "10000", C)])
