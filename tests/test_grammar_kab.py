"""Kabyle grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/kab.json."""
import unittest

from helpers import read, sure

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def kab(text: str) -> list[tuple[str, str, str]]:
    return read(text, "kab")


class TestKabyle(unittest.TestCase):
    def test_the_unit_comes_before_the_ten(self):
        # 6 + 20 = 26; waḥed stands only in a compound: 1 + 20 = 21
        self.assertEqual(kab("setta u ɛecrin"), [("setta u ɛecrin", "26", C)])
        self.assertEqual(kab("waḥed u ɛecrin"), [("waḥed u ɛecrin", "21", C)])
        self.assertEqual(kab("waḥed"), [])

    def test_a_short_unit_counts_the_hundreds_and_thousands(self):
        # 3 x 100 = 300; 8 x 100 x 1000 = 800000
        self.assertEqual(kab("telt-mya"), [("telt-mya", "300", C)])
        self.assertEqual(kab("temn-myat alef n tefyar"), [("temn-myat alef", "800000", C)])
        self.assertEqual(kab("juǧ alaf"), [("juǧ alaf", "2000", C)])

    def test_a_particle_makes_an_ordinal(self):
        self.assertEqual(kab("arraz wis tlata"), [("wis tlata", "3", O)])

    def test_marks_and_stand_in_letters(self):
        # ṛebεa with Greek ε reads as ṛebɛa; 4 x 100 = 400
        self.assertEqual(kab("ṛebεa-mya"), [("ṛebεa-mya", "400", C)])
        self.assertEqual(kab("rebɛa"), [("rebɛa", "4", C)])

    def test_digits_group_with_a_space(self):
        self.assertEqual(kab("1 000 000"), [("1 000 000", "1000000", C)])

    def test_tesa_alone_is_also_the_verb_to_have(self):
        # 9 alone at low confidence; 9 + 20 = 29
        self.assertEqual(sure("tesɛa", "kab"), [("tesɛa", "9", 0.4)])
        self.assertEqual(sure("tesɛa u ɛecrin", "kab"), [("tesɛa u ɛecrin", "29", 1.0)])
        self.assertEqual(sure("tmanya", "kab"), [("tmanya", "8", 1.0)])


if __name__ == "__main__":
    unittest.main()


class TestClockHours(unittest.TestCase):
    def test_an_hour_noun_with_the_article_is_its_number(self):
        # kab.wikipedia "ɣef lxemsa n tmeddit", "ɣef ttnac n yiḍ"; Tatoeba "d ssaɛtin ɣiṛ ṛṛbeɛ"
        self.assertEqual(kab("ɣef lxemsa n tmeddit"), [("lxemsa", "5", C)])
        self.assertEqual(kab("ɣef ttnac n yiḍ"), [("ttnac", "12", C)])
        self.assertEqual(kab("d ssaɛtin ɣiṛ ṛṛbeɛ"), [("ssaɛtin", "2", C)])
        self.assertEqual(kab("d leḥḍac u ṛṛbeɛ"), [("leḥḍac", "11", C)])
        self.assertEqual(kab("Attan d lεacra d wezgen"), [("lεacra", "10", C)])

    def test_the_hour_closes_the_number(self):
        # "ɣef lxemsa u xemsin n ddqayeq" is five and fifty minutes, not 55;
        # the bare unit still joins its ten: 5 + 50 = 55
        self.assertEqual(kab("ɣef lxemsa u xemsin n ddqayeq"), [("lxemsa", "5", C), ("xemsin", "50", C)])
        self.assertEqual(kab("xemsa u xemsin"), [("xemsa u xemsin", "55", C)])

    def test_the_cardinal_two_takes_a_ten(self):
        # "jjuǧ" is the cardinal 2, not only the hour: 2 + 20 = 22
        self.assertEqual(kab("jjuǧ u ɛecrin"), [("jjuǧ u ɛecrin", "22", C)])
