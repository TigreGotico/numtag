"""Arabic grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/ar.json."""
import unittest

import pytest
from helpers import read, sure
from numtag import tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def ar(text: str) -> list[tuple[str, str, str]]:
    return read(text, "ar")


class TestArabic(unittest.TestCase):
    def test_the_unit_comes_before_the_ten(self):
        # 5 + 20 = 25; 1000 + 900 + 5 + 80 = 1985
        self.assertEqual(ar("خمسة وعشرون"), [("خمسة وعشرون", "25", C)])
        self.assertEqual(ar("ألف وتسعمائة وخمسة وثمانون"), [("ألف وتسعمائة وخمسة وثمانون", "1985", C)])

    def test_teens_and_bound_units(self):
        # 3 + 10 = 13; أحد and اثنا stand only in compounds
        self.assertEqual(ar("ثلاثة عشر"), [("ثلاثة عشر", "13", C)])
        self.assertEqual(ar("أحد عشر كوكبا"), [("أحد عشر", "11", C)])
        self.assertEqual(ar("اثنا عشر"), [("اثنا عشر", "12", C)])
        self.assertEqual(ar("يوم الأحد"), [])

    def test_digits_glued_to_the_joiner_prefix(self):
        # 2 x 10^6 + 500 x 10^3 = 2500000; with no scale word after them
        # the digits start a new number
        self.assertEqual(ar("2 مليون و500 ألف"), [("2 مليون و500 ألف", "2500000", C)])
        self.assertEqual(ar("2 مليون و 500 ألف"), [("2 مليون و 500 ألف", "2500000", C)])
        self.assertEqual(ar("بين 15 و20"), [("15", "15", C), ("20", "20", C)])
        self.assertEqual(ar("mp3"), [])

    def test_the_span_starts_after_an_unused_joiner(self):
        # و (and) is a prefix that starts a new number: the span is the number word
        for text, word, value in [("عندي خمس تفاحات وسبع برتقالات", "سبع", "7"),
                                  ("بين عشرة وعشرين شخصا", "عشرين", "20"),
                                  ("المراكز الرابع والخامس", "الخامس", "5"),
                                  ("بين 15 و20 درجة", "20", "20")]:
            start = text.index(word)
            mention = tag_numbers(text, "ar")[-1]
            self.assertEqual((mention.char_span, mention.text, mention.value), ((start, start + len(word)), word, value), text)
        # the joiner inside a number stays in the span: 5 + 20 = 25
        self.assertEqual([(m.char_span, m.text) for m in tag_numbers("خمسة وعشرون", "ar")], [((0, 11), "خمسة وعشرون")])

    def test_the_dual_holds_its_count(self):
        # ألفان = 2 x 1000, + 500 = 2500; مليونان = 2 x 10^6
        self.assertEqual(ar("ألفان وخمسمائة"), [("ألفان وخمسمائة", "2500", C)])
        self.assertEqual(ar("مليونان"), [("مليونان", "2000000", C)])
        self.assertEqual(ar("ثلاثة آلاف"), [("ثلاثة آلاف", "3000", C)])

    def test_harakat_and_letter_forms_read_the_same(self):
        self.assertEqual(ar("ثَلَاثَةٌ"), [("ثَلَاثَةٌ", "3", C)])
        self.assertEqual(ar("ثلاثه"), [("ثلاثه", "3", C)])
        # tanwin on the accusative: 11 x 1000 = 11000
        self.assertEqual(ar("أحد عشر ألفاً"), [("أحد عشر ألفاً", "11000", C)])

    def test_the_hamza_sets_and_eleven_apart_from_one(self):
        # و + أحد عشر after a hundred: 100 + 11 = 111; "واحد" is one, and the
        # hamza-less "احد" still reads as أحد
        self.assertEqual(ar("مئة وأحد عشر"), [("مئة وأحد عشر", "111", C)])
        self.assertEqual(ar("ألف وإحدى عشرة"), [("ألف وإحدى عشرة", "1011", C)])
        self.assertEqual(ar("واحد"), [("واحد", "1", C)])
        self.assertEqual(ar("احد عشر"), [("احد عشر", "11", C)])

    def test_the_first_starts_no_compound_ordinal(self):
        # 11th is "الحادي عشر", so "الأولى" stays the 1st and 10 x 1000 follows
        self.assertEqual(ar("الدفعة الأولى عشرة آلاف"), [("الأولى", "1", O), ("عشرة آلاف", "10000", C)])

    def test_cldr_spellings_and_the_construct_dual(self):
        # CLDR "إثنا عشر" = 12; "مليوني" = 2 x 10^6 before a noun
        self.assertEqual(ar("الطابق إثنا عشر"), [("إثنا عشر", "12", C)])
        self.assertEqual(ar("رصدنا مليوني ريال"), [("مليوني", "2000000", C)])

    def test_ordinals_read_unit_first(self):
        # 1 + 20 = 21st; 5 + 10 = 15th
        self.assertEqual(ar("القرن الحادي والعشرون"), [("الحادي والعشرون", "21", O)])
        self.assertEqual(ar("الخامس عشر"), [("الخامس عشر", "15", O)])
        self.assertEqual(ar("الفصل الثالث"), [("الثالث", "3", O)])
        # الحادي stands only before عشر or a ten
        self.assertEqual(ar("الحادي"), [])

    def test_a_half_after_a_thousand_is_half_of_it(self):
        # 1000 + 500 = 1500; 3 + 1/2 = 3.5
        self.assertEqual(ar("ألف ونصف"), [("ألف ونصف", "1500", C)])
        self.assertEqual(ar("ثلاثة ونصف"), [("ثلاثة ونصف", "3.5", F)])

    def test_fraction_nouns(self):
        # ثلث = 1/3; ثلاثة أرباع = 3/4
        self.assertEqual(ar("ثلث"), [("ثلث", "1/3", F)])
        self.assertEqual(ar("ثلاثة أرباع"), [("ثلاثة أرباع", "0.75", F)])

    def test_arabic_indic_digits(self):
        # ١٢٬٣٤٥٫٦ = 12345.6
        self.assertEqual(ar("١٢٬٣٤٥٫٦ دينار"), [("١٢٬٣٤٥٫٦", "12345.6", D)])

    def test_a_preposition_needs_three_letters_after_it(self):
        # ب + خمسة = with five; لست is "I am not", not ل + ست
        self.assertEqual(ar("بخمسة دولارات"), [("بخمسة", "5", C)])
        self.assertEqual(ar("لست أدري"), [])

    def test_a_word_with_a_preposition_starts_a_new_number(self):
        # "بالمائة" is "per hundred": the hundred is no part of 2.7
        self.assertEqual(ar("اثنان فاصل سبعة بالمائة"),
                         [("اثنان فاصل سبعة", "2.7", D), ("بالمائة", "100", C)])

    def test_the_spoken_hundred_takes_a_count(self):
        # 5 x 100; 3 x 100; alone it is also water
        self.assertEqual(ar("خمس مية"), [("خمس مية", "500", C)])
        self.assertEqual(ar("ثلاث مية ريال"), [("ثلاث مية", "300", C)])
        self.assertEqual(sure("شربت مية", "ar"), [("مية", "100", 0.4)])
        self.assertEqual(sure("مائة ريال", "ar"), [("مائة", "100", 1.0)])

    def test_the_spoken_hundreds_are_fused_words(self):
        # 200 to 900, each spelled with ة and with ه (the spelling of ميه)
        for value, words in [("200", ["ميتين"]), ("300", ["ثلاثمية", "تلتمية"]),
                             ("400", ["اربعمية", "أربعمية", "ربعمية"]), ("500", ["خمسمية", "خمسميه"]),
                             ("600", ["ستمية"]), ("700", ["سبعمية"]),
                             ("800", ["تمنمية", "ثمنمية", "ثمانمية"]), ("900", ["تسعمية", "تسعميه"])]:
            for word in words:
                self.assertEqual(ar(word + " كيلو"), [(word, value, C)], word)

    def test_the_spoken_hundreds_join_with_the_joiner(self):
        # 1000 + 200 = 1200; 300 + 11 = 311; 400 + 50 = 450; 300 + 25 = 325
        self.assertEqual(ar("الف وميتين"), [("الف وميتين", "1200", C)])
        self.assertEqual(ar("ثلاثمية وواحد عشر"), [("ثلاثمية وواحد عشر", "311", C)])
        self.assertEqual(ar("اربعمية وخمسين"), [("اربعمية وخمسين", "450", C)])
        self.assertEqual(ar("ثلاثمية وخمسة وعشرين"), [("ثلاثمية وخمسة وعشرين", "325", C)])
        # 600 + 10 x 1000 + 200 = 610200
        self.assertEqual(ar("ستمية وعشرة الاف وميتين"), [("ستمية وعشرة الاف وميتين", "610200", C)])

    def test_the_homograph_hundred_reads_as_before(self):
        # water, and a hundred before a number: 100 + 2 = 102
        self.assertEqual(sure("شربت مية", "ar"), [("مية", "100", 0.4)])
        self.assertEqual(ar("مية واثنين"), [("مية واثنين", "102", C)])
        # ميتين is also "dead" (plural): alone it reads 200 at the homograph confidence
        self.assertEqual(sure("ناس ميتين", "ar"), [("ميتين", "200", 0.4)])


class TestSpokenArabic(unittest.TestCase):
    def test_the_spoken_teens_are_one_word(self):
        # Egyptian 11, South Levantine 15, North Levantine 13, Moroccan 16
        for word, value in (("حداشر", "11"), ("خمستعش", "15"), ("تلطعش", "13"), ("ستاش", "16"), ("هدعش", "11")):
            with self.subTest(word=word):
                self.assertEqual(ar(word), [(word, value, C)])

    def test_spoken_tens_and_hundreds_join_a_number(self):
        # 3 + 30 = 33; 1000 + 15 = 1015; 500 with ه for ة; 1000 + 200 = 1200
        self.assertEqual(ar("ثلاث وتلاتين"), [("ثلاث وتلاتين", "33", C)])
        self.assertEqual(ar("الف وخمستعش"), [("الف وخمستعش", "1015", C)])
        self.assertEqual(ar("خمسميه"), [("خمسميه", "500", C)])
        self.assertEqual(ar("الف وميتين"), [("الف وميتين", "1200", C)])

    def test_two_hundred_alone_is_weak(self):
        # "ميتين" is also the plural of "dead"
        self.assertEqual(sure("ناس ميتين", "ar"), [("ميتين", "200", 0.4)])

    def test_standard_arabic_words_stay_words(self):
        # the dragon, the price, the spouse; Monday and Tuesday
        for text in ("ثم ظهر التنين", "ثمن السيارة", "زوج أختي", "يوم الاتنين", "ويوم التلاتة"):
            with self.subTest(text=text):
                self.assertEqual(ar(text), [])

    def test_illiteracy_and_umayya_read_no_number(self):
        # "امية" is the plain-alif spelling of "illiteracy" and of the name Umayya
        for text in ("محو الامية", "نسبة الامية في مصر", "بنو امية", "امية بن ابي الصلت"):
            with self.subTest(text=text):
                self.assertEqual(sure(text, "ar"), [])


@pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/161")
@pytest.mark.parametrize("text, expected", [
    ('ألفان ومليون', [('ألفان ومليون', '1002000', C)]),
    ('خمسة آلاف ومليون', [('خمسة آلاف ومليون', '1005000', C)]),
])
def test_ar_a_larger_scale_joined_with_and_adds(text, expected):
    # 2000 + 1000000 = 1002000; 5000 + 1000000 = 1005000
    assert read(text, "ar") == expected



if __name__ == "__main__":
    unittest.main()
