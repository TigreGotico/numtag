"""Basque grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/eu.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C, O, F = "cardinal", "ordinal", "fraction"


def eu(text: str) -> list[tuple[str, str, str]]:
    return read(text, "eu")


def confidence(text: str, lang: str) -> list[tuple[str, float]]:
    return [(m.text, m.confidence) for m in tag_numbers(text, lang)]


class TestVigesimalTens(unittest.TestCase):
    def test_a_ten_with_ta_takes_the_teens(self):
        # 20 + 10 = 30; 3 x 20 + 10 = 70; 4 x 20 + 19 = 99
        self.assertEqual(eu("hogeita hamar"), [("hogeita hamar", "30", C)])
        self.assertEqual(eu("hirurogeita hamar"), [("hirurogeita hamar", "70", C)])
        self.assertEqual(eu("laurogeita hemeretzi"), [("laurogeita hemeretzi", "99", C)])

    def test_a_ten_with_ta_is_no_number_alone(self):
        self.assertEqual(eu("hogeita"), [])


class TestOneAfterNoun(unittest.TestCase):
    def test_bat_after_the_noun_is_the_count_one(self):
        self.assertEqual(eu("milioi bat"), [("milioi bat", "1000000", C)])
        self.assertEqual(eu("dozena bat"), [("dozena bat", "12", C)])
        self.assertEqual(eu("heren bat"), [("heren bat", "1/3", F)])
        self.assertEqual(eu("erdi bat"), [("erdi bat", "0.5", F)])


class TestOrdinalEnding(unittest.TestCase):
    def test_garren_makes_the_cardinal_before_it_an_ordinal(self):
        # 20 + 1 = 21
        self.assertEqual(eu("bigarren"), [("bigarren", "2", O)])
        self.assertEqual(eu("hogeita batgarren"), [("hogeita batgarren", "21", O)])
        self.assertEqual(eu("ehungarren"), [("ehungarren", "100", O)])

    def test_the_article_a_after_an_ordinal(self):
        # the article joins the ordinal with no space: 1st to 10th
        expected = ["lehena", "bigarrena", "hirugarrena", "laugarrena", "bosgarrena", "seigarrena",
                    "zazpigarrena", "zortzigarrena", "bederatzigarrena", "hamargarrena"]
        for value, word in enumerate(expected, 1):
            with self.subTest(word=word):
                self.assertEqual(eu(word), [(word, str(value), O)])
        self.assertEqual(eu("hogeita batgarrena"), [("hogeita batgarrena", "21", O)])

    def test_bost_drops_its_last_letter_before_garren(self):
        self.assertEqual(eu("bosgarren"), [("bosgarren", "5", O)])
        self.assertEqual(eu("hamabosgarren"), [("hamabosgarren", "15", O)])


class TestGroups(unittest.TestCase):
    def test_eta_goes_before_the_last_part(self):
        # 1000 + 200 = 1200; 1000 + 200 + 1 = 1201
        self.assertEqual(eu("mila eta berrehun"), [("mila eta berrehun", "1200", C)])
        self.assertEqual(eu("mila berrehun eta bat"), [("mila berrehun eta bat", "1201", C)])

    def test_a_scale_noun_keeps_one_form_after_every_count(self):
        # 5 x 1000000 = 5000000
        self.assertEqual(eu("bost milioi"), [("bost milioi", "5000000", C)])

    def test_a_space_groups_digits(self):
        self.assertEqual(eu("1 000 000"), [("1 000 000", "1000000", C)])



class TestFractionAfterScale(unittest.TestCase):
    def test_a_fraction_after_a_scale_word_takes_a_part_of_it(self):
        # 1000000 / 2 = 500000; 1000000 / 3; 3 x 1000000 / 4 = 750000
        self.assertEqual(eu("milioi erdi bat"), [("milioi erdi bat", "500000", C)])
        self.assertEqual(eu("milioi-erdi bat"), [("milioi-erdi bat", "500000", C)])
        self.assertEqual(eu("milioi heren bat"), [("milioi heren bat", "1000000/3", F)])
        self.assertEqual(eu("hiru milioi laurden"), [("hiru milioi laurden", "750000", C)])


class TestHamazortzi(unittest.TestCase):
    def test_hamazortzi_is_the_second_form_of_eighteen(self):
        # 20 + 18 = 38
        self.assertEqual(eu("hamazortzi"), [("hamazortzi", "18", C)])
        self.assertEqual(eu("hogeita hamazortzi"), [("hogeita hamazortzi", "38", C)])
        self.assertEqual(eu("hamazortzigarren"), [("hamazortzigarren", "18", O)])


class TestArticleAfterNoun(unittest.TestCase):
    def test_bat_after_a_word_is_a_weak_number(self):
        self.assertEqual(confidence("Etxe bat.", "eu"), [("bat", 0.3)])
        self.assertEqual(confidence("Liburu bat erosi du.", "eu"), [("bat", 0.3)])

    def test_bat_with_no_word_before_it_is_a_number(self):
        self.assertEqual(confidence("Bat etorri da.", "eu"), [("Bat", 1.0)])


if __name__ == "__main__":
    unittest.main()
