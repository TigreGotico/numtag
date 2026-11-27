"""Italian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/it.json."""
import unittest

import pytest
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

    def test_a_latin_unit_ordinal_ends_no_longer_ordinal(self):
        # 22nd is "ventiduesimo" and 103rd "centotreesimo": "dieci secondi"
        # is 10 and the time unit, never 12
        for text, count in [("cento terzo", "100"), ("venti primi", "20")]:
            with self.subTest(text=text):
                found = it(text)
                self.assertEqual(found[0][1:], (count, C))
                self.assertEqual(len(found), 2)
                self.assertEqual(found[1][2], O)
        # after a cardinal the plural "secondi" is the time unit and no ordinal
        for text, count in [("tra dieci secondi", "10"), ("trenta secondi", "30")]:
            with self.subTest(text=text):
                self.assertEqual([f[1:] for f in it(text)], [(count, C)])
        # "decimo" ends "centodecimo", so 100 + 10 = 110 still reads
        self.assertEqual(it("cento decimo"), [("cento decimo", "110", O)])


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


class TestScaleNounsAboveATrillion(unittest.TestCase):
    def test_a_quadrilione_is_a_million_trilioni(self):
        # long scale: quadrilione = 10^(6 x 4) = 10^24, written as 1 and 24 zeros
        self.assertEqual(it("un quadrilione"), [("un quadrilione", "1000000000000000000000000", C)])
        # 2 x 10^24
        self.assertEqual(it("due quadrilioni"), [("due quadrilioni", "2000000000000000000000000", C)])
        # a half of 10^24 = 5 x 10^23, written as 5 and 23 zeros
        self.assertEqual(it("mezzo quadrilione"), [("mezzo quadrilione", "500000000000000000000000", C)])


class TestMinus(unittest.TestCase):
    def test_meno_after_a_is_a_minus(self):
        self.assertEqual(it("scesa a meno tre gradi"), [("meno tre", "-3", C)])

    def test_piu_o_meno_is_no_minus(self):
        self.assertEqual(it("più o meno tre"), [("tre", "3", C)])


class TestHomographs(unittest.TestCase):
    def test_the_elided_article_un_is_weak(self):
        # "un'ora" is "una ora": the noun follows the apostrophe
        for text in ("un timer di un'ora", "un’altra volta", "fammi vedere un' altra foto"):
            with self.subTest(text=text):
                self.assertTrue(all(m.confidence == 0.3 for m in tag_numbers(text, "it")))
        # the elided "ventun" stays a number, and a digit after the apostrophe is no noun
        self.assertEqual([(m.text, m.confidence) for m in tag_numbers("ventun'ore", "it")], [("ventun", 1.0)])
        self.assertEqual([(m.text, m.confidence) for m in tag_numbers("un' 3", "it")], [("un", 1.0), ("3", 1.0)])

    def test_cento_after_per_and_a_number_is_the_percent_sign(self):
        self.assertEqual(read("il cinquanta per cento", "it"), [("cinquanta", "50", "cardinal")])
        self.assertEqual(read("20 per cento", "it"), [("20", "20", "cardinal")])
        # "per cento euro" is for a hundred euros
        self.assertEqual(read("l'ho venduto per cento euro", "it"), [("cento", "100", "cardinal")])

    def test_sei_and_venti_alone_may_be_words(self):
        # "sei" may be "you are", "venti" "winds"
        self.assertEqual(confidence("Sei sicuro?", "it"), [("Sei", 0.4)])
        self.assertEqual(confidence("venti forti", "it"), [("venti", 0.4)])
        self.assertEqual(confidence("ventisei", "it"), [("ventisei", 1.0)])
        self.assertEqual(confidence("seimila", "it"), [("seimila", 1.0)])


class TestMinusIdioms(unittest.TestCase):
    def test_quanto_meno_is_no_sign(self):
        self.assertEqual(read("Ci vogliono quanto meno tre ore.", "it"), [("tre", "3", C)])
        self.assertEqual(read("quanto meno 3 ore", "it"), [("3", "3", C)])

    def test_meno_before_a_number_still_signs(self):
        self.assertEqual(read("Fuori ci sono meno tre gradi.", "it"), [("meno tre", "-3", C)])

    def test_a_point_before_the_first_digit_marks_decimals(self):
        self.assertEqual(read("-.5", "it"), [("-.5", "-0.5", "decimal")])


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/161")
@pytest.mark.parametrize("text, expected", [
    ('novecentonovantanove sistiliardi', [('novecentonovantanove sistiliardi', '999000000000000000000000000000000000000000', C)]),
])
def test_it_sistiliardi_is_10_to_the_39(text, expected):
    # sistiliardo is 10^39; 999 x 10^39
    assert read(text, "it") == expected



if __name__ == "__main__":
    unittest.main()
