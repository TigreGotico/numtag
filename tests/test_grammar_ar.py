"""Arabic grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/ar.json."""
import unittest

from helpers import read, sure

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


if __name__ == "__main__":
    unittest.main()
