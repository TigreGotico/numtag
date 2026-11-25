"""Esperanto grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/eo.json."""
import unittest

from helpers import read

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def eo(text: str) -> list[tuple[str, str, str]]:
    return read(text, "eo")


class TestCardinals(unittest.TestCase):
    def test_a_ten_and_a_unit_stand_side_by_side(self):
        # 20 + 3
        self.assertEqual(eo("dudek tri"), [("dudek tri", "23", C)])
        # 10 + 1
        self.assertEqual(eo("dek unu infanoj"), [("dek unu", "11", C)])

    def test_a_count_and_cent_are_one_word_from_two_up(self):
        # 2 x 100 + 70 + 8
        self.assertEqual(eo("ducent sepdek ok"), [("ducent sepdek ok", "278", C)])
        # "cent" alone is 100
        self.assertEqual(eo("cent homoj"), [("cent", "100", C)])

    def test_the_thousands_are_apart_words(self):
        # 2 x 1000
        self.assertEqual(eo("du mil"), [("du mil", "2000", C)])
        # 12 x 1000 + 4 x 100 + 30 + 2
        self.assertEqual(eo("dek du mil kvarcent tridek du"), [("dek du mil kvarcent tridek du", "12432", C)])
        # 999 x 1000 + 999
        self.assertEqual(eo("naŭcent naŭdek naŭ mil naŭcent naŭdek naŭ"),
                         [("naŭcent naŭdek naŭ mil naŭcent naŭdek naŭ", "999999", C)])

    def test_no_word_joins_two_numbers_and_kaj_splits_them(self):
        # 5, 7 and 5 + 7 = 12
        self.assertEqual(eo("Kvin kaj sep faras dek du."),
                         [("Kvin", "5", C), ("sep", "7", C), ("dek du", "12", C)])

    def test_unudek_and_unucent_are_no_numbers(self):
        # "dek" and "cent" take no count of one
        self.assertEqual(eo("unudek"), [])
        self.assertEqual(eo("unucent"), [])


class TestLargeNumbers(unittest.TestCase):
    def test_the_scale_is_long(self):
        # biliono has twelve zeros, miliardo nine
        self.assertEqual(eo("du bilionoj"), [("du bilionoj", "2000000000000", C)])
        self.assertEqual(eo("tri miliardoj"), [("tri miliardoj", "3000000000", C)])
        # 1 x 10^9
        self.assertEqual(eo("unu miliardo"), [("unu miliardo", "1000000000", C)])

    def test_a_plural_scale_noun_with_no_count_is_no_number(self):
        self.assertEqual(eo("El multaj milonoj fariĝas milionoj."), [])

    def test_the_accusative_keeps_the_count(self):
        # 10 x 10^6
        self.assertEqual(eo("Ŝi vidis dek milionojn da homoj."), [("dek milionojn", "10000000", C)])

    def test_a_singular_scale_noun_takes_no_count_above_one(self):
        # "du miliono" is two words: 2, and a scale noun that counts nothing
        self.assertEqual(eo("du miliono"), [("du", "2", C)])


class TestOrdinals(unittest.TestCase):
    def test_the_ending_a_goes_on_the_last_word(self):
        # 20 + 7
        self.assertEqual(eo("la dudek sepa tago"), [("dudek sepa", "27", O)])
        # 1000 + 200 + 5, the last word is a thousand-ordinal only for 1000
        self.assertEqual(eo("la mil ducent kvina"), [("mil ducent kvina", "1205", O)])

    def test_one_written_word_and_hyphens_read_the_same(self):
        for text in ("dudeksepa", "dudek-sepa", "dudek sepa"):
            self.assertEqual(eo(text), [(text, "27", O)])

    def test_the_endings_j_and_n_stay_in_the_span(self):
        self.assertEqual(eo("la sepan tagon"), [("sepan", "7", O)])
        self.assertEqual(eo("ses unuaj tagoj"), [("ses", "6", C), ("unuaj", "1", O)])

    def test_a_digit_string_takes_the_ordinal_ending_after_a_hyphen(self):
        self.assertEqual(eo("la 1-a de Majo"), [("1-a", "1", O)])
        self.assertEqual(eo("la 5-ajn"), [("5-ajn", "5", O)])


class TestPartsAndGroups(unittest.TestCase):
    def test_on_words_are_parts(self):
        # 3 x 1/4
        self.assertEqual(eo("tri kvaronoj"), [("tri kvaronoj", "0.75", F)])
        # 25 x 1/100
        self.assertEqual(eo("dudek kvin centonojn"), [("dudek kvin centonojn", "0.25", F)])

    def test_a_group_noun_counts_its_members(self):
        # 2 x 12
        self.assertEqual(eo("du dekduojn da forkoj"), [("du dekduojn", "24", C)])
        # one group of 10
        self.assertEqual(eo("Mi aĉetis dekon da ovoj."), [("dekon", "10", C)])

    def test_decimals(self):
        # 12 and 5 tenths
        self.assertEqual(eo("dek du komo kvin"), [("dek du komo kvin", "12.5", D)])
        self.assertEqual(eo("2,75 kg"), [("2,75", "2.75", D)])


class TestDigits(unittest.TestCase):
    def test_a_narrow_no_break_space_and_a_space_group_digits(self):
        for mark in (" ", " "):
            self.assertEqual(eo(f"10{mark}000 homoj"), [(f"10{mark}000", "10000", C)])


class TestSmallWords(unittest.TestCase):
    def test_nul_and_nulo_are_zero(self):
        # the cipher 0
        self.assertEqual(eo("nul gradoj"), [("nul", "0", C)])
        self.assertEqual(eo("nulo"), [("nulo", "0", C)])

    def test_a_tenth_and_a_dozen(self):
        # 1 x 1/10
        self.assertEqual(eo("unu dekono"), [("unu dekono", "0.1", F)])
        # one group of 12
        self.assertEqual(eo("Mi aĉetis dekduon da kuleroj."), [("dekduon", "12", C)])

    def test_a_milliard_is_ten_to_the_ninth(self):
        # 3 x 10^9
        self.assertEqual(eo("tri miliardoj"), [("tri miliardoj", "3000000000", C)])
        # 1 x 10^9
        self.assertEqual(eo("unu miliardo"), [("unu miliardo", "1000000000", C)])

    def test_a_word_that_holds_the_letters_of_a_number_word_is_no_number(self):
        for text in ("centro", "milito", "okuloj", "dekstren"):
            self.assertEqual(eo(text), [])

    def test_biliardo_is_no_esperanto_number(self):
        # PMEG 23.2: only "du" reads
        self.assertEqual(eo("du biliardoj"), [("du", "2", C)])

    def test_kaj_inside_a_hyphenated_word_joins_nothing(self):
        # "kaj" is the conjunction "and", which no number holds
        self.assertEqual(eo("dek-kaj-unu"), [])

    def test_the_ranks_of_the_large_scale_nouns(self):
        # 10^(6 x rank), PMEG 23.2: kvadriliono has 24 zeros, deciliono 60
        self.assertEqual(eo("unu kvadriliono"), [("unu kvadriliono", "1" + "0" * 24, C)])
        self.assertEqual(eo("du decilionoj"), [("du decilionoj", "2" + "0" * 60, C)])
