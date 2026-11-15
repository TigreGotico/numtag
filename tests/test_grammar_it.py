"""Italian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/it.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C, O = "cardinal", "ordinal"


def it(text: str) -> list[tuple[str, str, str]]:
    return read(text, "it")


def confidence(text: str, lang: str) -> list[tuple[str, float]]:
    return [(m.text, m.confidence) for m in tag_numbers(text, lang)]


class TestCompoundWords(unittest.TestCase):
    def test_a_word_splits_into_number_words(self):
        # 20 + 3 = 23; 2 x 1000 + 500 = 2500; 1000 + 100 + 1 = 1101
        self.assertEqual(it("ventitré"), [("ventitré", "23", C)])
        self.assertEqual(it("duemilacinquecento"), [("duemilacinquecento", "2500", C)])
        self.assertEqual(it("millecentouno"), [("millecentouno", "1101", C)])

    def test_a_ten_drops_its_vowel_before_uno_and_otto(self):
        # 20 + 1 = 21; 30 + 8 = 38; 100 + 8 = 108 with or without the "o"
        self.assertEqual(it("ventuno"), [("ventuno", "21", C)])
        self.assertEqual(it("trentotto"), [("trentotto", "38", C)])
        self.assertEqual(it("centootto"), [("centootto", "108", C)])
        self.assertEqual(it("centotto"), [("centotto", "108", C)])

    def test_a_piece_is_no_number_alone(self):
        self.assertEqual(it("vent"), [])
        self.assertEqual(it("cent"), [])

    def test_a_number_neither_starts_nor_ends_inside_a_word(self):
        # "uno" + "tre" splits, but no number is "unotre"
        self.assertEqual(it("unotre"), [])
        self.assertEqual(it("treuno"), [])

    def test_a_word_that_is_no_run_of_number_words_stays_whole(self):
        self.assertEqual(it("novella"), [])
        self.assertEqual(it("settembre"), [])
        self.assertEqual(it("ottobre"), [])


class TestOrdinalEnding(unittest.TestCase):
    def test_esimo_makes_the_cardinal_before_it_an_ordinal(self):
        # 20 + 3 = 23; 30 + 8 = 38
        self.assertEqual(it("ventitreesimo"), [("ventitreesimo", "23", O)])
        self.assertEqual(it("trentottesimo"), [("trentottesimo", "38", O)])
        self.assertEqual(it("centesimo"), [("centesimo", "100", O)])


class TestScaleNouns(unittest.TestCase):
    def test_a_singular_scale_noun_takes_only_the_count_one(self):
        # 2 x 1000000 = 2000000
        self.assertEqual(it("due milioni di euro"), [("due milioni", "2000000", C)])
        self.assertEqual(it("due milione"), [("due", "2", C)])

    def test_a_group_of_a_higher_scale_is_no_count_of_cento(self):
        # 2 x 1000000 + 3 x 1000 + 100 = 2003100
        self.assertEqual(it("due milioni tremilacento"), [("due milioni tremilacento", "2003100", C)])

    def test_mila_needs_a_count(self):
        # 3 x 1000 = 3000
        self.assertEqual(it("tremila"), [("tremila", "3000", C)])
        self.assertEqual(it("mila"), [])


class TestMinus(unittest.TestCase):
    def test_meno_after_a_is_a_minus(self):
        self.assertEqual(it("scesa a meno tre gradi"), [("meno tre", "-3", C)])

    def test_piu_o_meno_is_no_minus(self):
        self.assertEqual(it("più o meno tre"), [("tre", "3", C)])


class TestHomographs(unittest.TestCase):
    def test_sei_and_venti_alone_may_be_words(self):
        # "sei" may be "you are", "venti" "winds"
        self.assertEqual(confidence("Sei sicuro?", "it"), [("Sei", 0.4)])
        self.assertEqual(confidence("venti forti", "it"), [("venti", 0.4)])
        self.assertEqual(confidence("ventisei", "it"), [("ventisei", 1.0)])
        self.assertEqual(confidence("seimila", "it"), [("seimila", 1.0)])


if __name__ == "__main__":
    unittest.main()
