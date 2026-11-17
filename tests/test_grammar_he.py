"""Hebrew grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/he.json."""
import unittest

from helpers import read, sure
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

    def test_the_span_starts_after_an_unused_joiner(self):
        # ו (and) is written joined to the word and starts a new number: the
        # span is the number word, so it starts one character after the ו
        for text, word, value in [
            ("יש לי מכונית ושלוש אופניים", "שלוש", "3"),
            ("קניתי ספר ועשרה עטים", "עשרה", "10"),
            ("ושלושה ילדים", "שלושה", "3"),
            ("שלושה וארבעה", "ארבעה", "4"),
            ("ושליש", "שליש", "1/3"),
            ("ורבע", "רבע", "0.25"),
        ]:
            start = text.index(word)
            mention = tag_numbers(text, "he")[-1]
            self.assertEqual((mention.char_span, mention.text, mention.value), ((start, start + len(word)), word, value), text)
        # the ו is no part of the second number, and the first keeps its own span
        self.assertEqual([(m.char_span, m.text, m.value) for m in tag_numbers("ספר אחד ושני עטים", "he")],
                         [((4, 7), "אחד", "1"), ((9, 12), "שני", "2")])

    def test_a_clitic_after_the_joiner_stays_in_the_span(self):
        # ו comes off; ה and ב stay: "והשלושה" is ו + השלושה, "ובשלושה" is ו + בשלושה
        self.assertEqual([(m.char_span, m.text) for m in tag_numbers("והשלושה הלכו", "he")], [((1, 7), "השלושה")])
        self.assertEqual([(m.char_span, m.text) for m in tag_numbers("ובשלושה", "he")], [((1, 7), "בשלושה")])

    def test_the_joiner_inside_a_number_stays_in_the_span(self):
        # 20 + 3 = 23: the ו joins the unit to the ten
        self.assertEqual([(m.char_span, m.text, m.value) for m in tag_numbers("יש עשרים ושלוש", "he")],
                         [((3, 14), "עשרים ושלוש", "23")])

    def test_niqqud_and_bidi_marks(self):
        # the points do not change the word; a mark before a digit is no gap
        self.assertEqual(he("שְׁלוֹשָׁה"), [("שְׁלוֹשָׁה", "3", C)])
        self.assertEqual(he("‏-5"), [("-5", "-5", C)])

    def test_billion_has_one_value(self):
        # CLDR "1000000000000: ביליון": 10^12 on either scale, so no scale is reported
        mention, = tag_numbers("ביליון", "he")
        self.assertEqual((mention.value, mention.number_scale), ("1000000000000", None))

    def test_the_trillion_is_a_thousand_milliards(self):
        # he.wikipedia: 10^12; 3 x 10^12
        self.assertEqual(he("שלושה טריליון שקלים"), [("שלושה טריליון", "3000000000000", C)])
        self.assertEqual(he("טריליון"), [("טריליון", "1000000000000", C)])
        self.assertEqual(he("מיליארד"), [("מיליארד", "1000000000", C)])

    def test_the_century_and_monday_are_low_confidence(self):
        self.assertEqual(sure("המאה העשרים", "he"), [("המאה", "100", 0.4), ("העשרים", "20", 1.0)])
        self.assertEqual(sure("יום שני", "he"), [("שני", "2", 0.4)])
        self.assertEqual(sure("מאה שקלים", "he"), [("מאה", "100", 1.0)])
        self.assertEqual(sure("שני מיליון", "he"), [("שני מיליון", "2000000", 1.0)])


if __name__ == "__main__":
    unittest.main()
