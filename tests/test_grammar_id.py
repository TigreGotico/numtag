"""Indonesian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/id.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C, O, F = "cardinal", "ordinal", "fraction"


def id_(text: str) -> list[tuple[str, str, str]]:
    return read(text, "id")


def confidence(text: str, lang: str) -> list[tuple[str, float]]:
    return [(m.text, m.confidence) for m in tag_numbers(text, lang)]


class TestPrefixSe(unittest.TestCase):
    def test_se_is_one_before_a_scale_word(self):
        # 1 x 100; 1 x 1000; 1 x 1000000; 10 + 1 = 11
        self.assertEqual(id_("seratus"), [("seratus", "100", C)])
        self.assertEqual(id_("seribu"), [("seribu", "1000", C)])
        self.assertEqual(id_("sejuta"), [("sejuta", "1000000", C)])
        self.assertEqual(id_("sebelas"), [("sebelas", "11", C)])


class TestTensAndTeens(unittest.TestCase):
    def test_belas_adds_ten(self):
        # 10 + 2 = 12; 10 + 7 = 17
        self.assertEqual(id_("dua belas"), [("dua belas", "12", C)])
        self.assertEqual(id_("tujuh belas"), [("tujuh belas", "17", C)])

    def test_puluh_multiplies_by_ten(self):
        # 2 x 10 + 3 = 23; 9 x 10 + 9 = 99; 2 x 100 + 5 x 10 = 250
        self.assertEqual(id_("dua puluh tiga"), [("dua puluh tiga", "23", C)])
        self.assertEqual(id_("sembilan puluh sembilan"), [("sembilan puluh sembilan", "99", C)])
        self.assertEqual(id_("dua ratus lima puluh"), [("dua ratus lima puluh", "250", C)])

    def test_a_scale_word_keeps_one_form_after_every_count(self):
        self.assertEqual(id_("dua juta"), [("dua juta", "2000000", C)])


class TestPrefixKe(unittest.TestCase):
    def test_ke_makes_an_ordinal(self):
        self.assertEqual(id_("kedua"), [("kedua", "2", O)])
        self.assertEqual(id_("ke-20"), [("ke-20", "20", O)])

    def test_ke_alone_starts_no_number(self):
        self.assertEqual(id_("ke dua"), [("dua", "2", C)])
        self.assertEqual(id_("turun ke negatif tiga"), [("negatif tiga", "-3", C)])
        self.assertEqual(id_("kesatuan"), [])


class TestFractions(unittest.TestCase):
    def test_per_names_the_denominator(self):
        # 1/3; 2/3; 3/4 = 0.75; 1/2 = 0.5
        self.assertEqual(id_("sepertiga"), [("sepertiga", "1/3", F)])
        self.assertEqual(id_("dua pertiga"), [("dua pertiga", "2/3", F)])
        self.assertEqual(id_("tiga perempat"), [("tiga perempat", "0.75", F)])
        self.assertEqual(id_("seperdua"), [("seperdua", "0.5", F)])

    def test_setengah_follows_the_count_with_no_joiner(self):
        # 2 + 1/2 = 2.5
        self.assertEqual(id_("dua setengah"), [("dua setengah", "2.5", F)])



class TestDenominatorPrefix(unittest.TestCase):
    def test_per_makes_a_cardinal_of_several_words_the_denominator(self):
        # 1/(6 + 10) = 1/16 = 0.0625; 2/(1 x 100) = 0.02
        self.assertEqual(id_("seperenam belas"), [("seperenam belas", "0.0625", F)])
        self.assertEqual(id_("dua perseratus"), [("dua perseratus", "0.02", F)])

    def test_per_alone_or_spaced_names_no_denominator(self):
        self.assertEqual(id_("dua per tiga"), [("dua", "2", C), ("tiga", "3", C)])
        self.assertEqual(id_("persen"), [])


class TestFractionAfterWhole(unittest.TestCase):
    def test_a_fraction_follows_the_whole_with_no_joiner(self):
        # 3 + 2/3 = 11/3
        self.assertEqual(id_("tiga dua-pertiga"), [("tiga dua-pertiga", "11/3", F)])

    def test_digits_take_no_fraction_without_a_joiner(self):
        self.assertEqual(id_("tahun 1998 dua pertiga"), [("1998", "1998", C), ("dua pertiga", "2/3", F)])


class TestKeBeforeAWord(unittest.TestCase):
    def test_ke_that_starts_a_phrase_before_a_word_is_a_weak_ordinal(self):
        # KBBI: "kedua (buku)" is a group of two; "anaknya yang kedua" is second
        self.assertEqual(confidence("kedua pihak", "id"), [("kedua", 0.4)])
        self.assertEqual(confidence("Akhirnya, kelima medali tersebut", "id"), [("kelima", 0.4)])
        self.assertEqual(confidence("ketiga puluh empat provinsi", "id"), [("ketiga puluh empat", 0.4)])

    def test_ke_after_a_word_or_at_the_end_is_an_ordinal(self):
        self.assertEqual(confidence("anaknya yang kedua lahir kemarin", "id"), [("kedua", 1.0)])
        self.assertEqual(confidence("kota terbesar kedua di Indonesia", "id"), [("kedua", 1.0)])
        self.assertEqual(confidence("Kedua, kami pulang.", "id"), [("Kedua", 1.0)])
        self.assertEqual(confidence("peringkat ke-2 di dunia", "id"), [("ke-2", 1.0)])


if __name__ == "__main__":
    unittest.main()
