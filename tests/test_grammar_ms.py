"""Malay grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/ms.json."""
import unittest

from helpers import read
from numtag import tag_numbers, tag_vague_quantities

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def ms(text: str) -> list[tuple[str, str, str]]:
    return read(text, "ms")


def confidence(text: str) -> list[tuple[str, float]]:
    return [(m.text, m.confidence) for m in tag_numbers(text, "ms")]


class TestMalayWords(unittest.TestCase):
    def test_lapan_is_eight(self):
        # 8; 10 + 8 = 18; 8 x 10 + 5 = 85; 8 x 100 = 800
        self.assertEqual(ms("lapan"), [("lapan", "8", C)])
        self.assertEqual(ms("lapan belas"), [("lapan belas", "18", C)])
        self.assertEqual(ms("lapan puluh lima"), [("lapan puluh lima", "85", C)])
        self.assertEqual(ms("lapan ratus"), [("lapan ratus", "800", C)])

    def test_sifar_is_zero(self):
        self.assertEqual(ms("markah sifar"), [("sifar", "0", C)])

    def test_kosong_is_a_weak_zero_unless_it_follows_nombor(self):
        # "cawan itu kosong" is an empty cup; "nombor kosong" is the digit 0
        self.assertEqual(confidence("Cawan itu kosong."), [("kosong", 0.4)])
        self.assertEqual(confidence("pusinglah nombor kosong"), [("kosong", 1.0)])

    def test_kelapan_is_the_eighth(self):
        self.assertEqual(ms("gilirannya yang kelapan"), [("kelapan", "8", O)])


class TestScale(unittest.TestCase):
    def test_bilion_is_ten_to_the_ninth_by_default(self):
        # 2 x 10^9; 3 x 10^12
        self.assertEqual(ms("dua bilion"), [("dua bilion", "2000000000", C)])
        self.assertEqual(ms("tiga trilion"), [("tiga trilion", "3000000000000", C)])

    def test_bilion_is_ten_to_the_twelfth_in_the_long_scale(self):
        # 2 x 10^12
        self.assertEqual([(m.text, m.value) for m in tag_numbers("dua bilion", "ms", scale="long")],
                         [("dua bilion", "2000000000000")])


class TestMarks(unittest.TestCase):
    def test_the_decimal_mark_is_a_point_and_the_group_mark_a_comma(self):
        # 7 + 5/10 = 7.5; 450 x 1000 = 450000
        self.assertEqual(ms("7.5 meter"), [("7.5", "7.5", D)])
        self.assertEqual(ms("450,000 orang"), [("450,000", "450000", C)])

    def test_perpuluhan_starts_the_decimals(self):
        # 3 + 1/10 + 4/100 = 3.14
        self.assertEqual(ms("tiga perpuluhan satu empat"), [("tiga perpuluhan satu empat", "3.14", D)])


class TestVague(unittest.TestCase):
    def test_beberapa_before_a_scale_word_is_a_magnitude(self):
        # Kamus Dewan, "juta": "berjuta-juta beberapa juta"; juta is 1 000 000
        text = "Beberapa juta orang menonton perlawanan itu."
        self.assertEqual([(q.text, q.kind.value, q.scale) for q in tag_vague_quantities(text, "ms")],
                         [("Beberapa juta", "magnitude", "1000000")])
        self.assertEqual(ms(text), [])

    def test_beberapa_alone_is_an_amount(self):
        text = "Ada beberapa orang yang datang."
        self.assertEqual([(q.text, q.kind.value) for q in tag_vague_quantities(text, "ms")],
                         [("beberapa", "amount")])


if __name__ == "__main__":
    unittest.main()
