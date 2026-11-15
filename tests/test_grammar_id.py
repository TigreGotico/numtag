"""Indonesian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/id.json."""
import unittest

from helpers import read

C, O, F = "cardinal", "ordinal", "fraction"


def id_(text: str) -> list[tuple[str, str, str]]:
    return read(text, "id")


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


if __name__ == "__main__":
    unittest.main()
