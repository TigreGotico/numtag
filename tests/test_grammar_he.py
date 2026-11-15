"""Hebrew grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/he.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def he(text: str) -> list[tuple[str, str, str]]:
    return read(text, "he")


class TestHebrew(unittest.TestCase):
    def test_the_joiner_is_glued_to_the_last_part(self):
        # 20 + 3 = 23; 1000 + 900 + 80 + 4 = 1984
        self.assertEqual(he("עשרים ושלוש"), [("עשרים ושלוש", "23", C)])
        self.assertEqual(he("אלף תשע מאות שמונים וארבע"), [("אלף תשע מאות שמונים וארבע", "1984", C)])

    def test_a_teen_is_a_unit_and_a_teen_word(self):
        # 3 + 10 = 13, masculine and feminine; שנים and שתים stand only in teens
        self.assertEqual(he("שלושה עשר ילדים"), [("שלושה עשר", "13", C)])
        self.assertEqual(he("שלוש עשרה בנות"), [("שלוש עשרה", "13", C)])
        self.assertEqual(he("שנים עשר"), [("שנים עשר", "12", C)])
        self.assertEqual(he("לפני שנים"), [])

    def test_plural_hundreds_take_a_count(self):
        # 3 x 100 = 300
        self.assertEqual(he("שלוש מאות"), [("שלוש מאות", "300", C)])

    def test_the_dual_holds_its_count(self):
        # אלפיים = 2 x 1000; + 20 + 5 = 2025
        self.assertEqual(he("אלפיים ועשרים וחמש"), [("אלפיים ועשרים וחמש", "2025", C)])
        self.assertEqual(he("שלושת אלפים"), [("שלושת אלפים", "3000", C)])

    def test_a_half_after_a_scale_word_is_half_of_it(self):
        # 10^6 + 10^6 / 2 = 1500000; 3 + 1/2 = 3.5
        self.assertEqual(he("מיליון וחצי"), [("מיליון וחצי", "1500000", C)])
        self.assertEqual(he("שלוש וחצי"), [("שלוש וחצי", "3.5", F)])

    def test_a_lone_fraction_noun_is_one_part(self):
        # רבע = 1/4; שני שלישים = 2/3
        self.assertEqual(he("רבע שעה"), [("רבע", "0.25", F)])
        self.assertEqual(he("שני שלישים"), [("שני שלישים", "2/3", F)])

    def test_prefixes_stay_in_the_span(self):
        # ב + שש = at six; ה + שלישית = the third (feminine)
        self.assertEqual(he("בשש בבוקר"), [("בשש", "6", C)])
        self.assertEqual(he("הפעם השלישית"), [("השלישית", "3", O)])

    def test_a_number_after_an_unused_joiner_keeps_the_whole_word(self):
        # "ושלושה" opens the number: the span starts at the word, not inside it
        self.assertEqual(he("ושלושה ילדים"), [("ושלושה", "3", C)])

    def test_niqqud_and_bidi_marks(self):
        # the points do not change the word; a mark before a digit is no gap
        self.assertEqual(he("שְׁלוֹשָׁה"), [("שְׁלוֹשָׁה", "3", C)])
        self.assertEqual(he("‏-5"), [("-5", "-5", C)])

    def test_the_long_scale(self):
        # ביליון = 10^12 in the long scale
        mention, = tag_numbers("ביליון", "he")
        self.assertEqual((mention.value, mention.number_scale.value), ("1000000000000", "long"))


if __name__ == "__main__":
    unittest.main()
