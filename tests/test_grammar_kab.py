"""Kabyle grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/kab.json."""
import unittest

import pytest
from helpers import read, sure

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def kab(text: str) -> list[tuple[str, str, str]]:
    return read(text, "kab")


class TestKabyle(unittest.TestCase):
    def test_the_unit_comes_before_the_ten(self):
        # 6 + 20 = 26; 1 + 20 = 21
        self.assertEqual(kab("setta u ɛecrin"), [("setta u ɛecrin", "26", C)])
        self.assertEqual(kab("waḥed u ɛecrin"), [("waḥed u ɛecrin", "21", C)])

    def test_wahed_also_stands_alone(self):
        # 1 alone, as in counting "waḥed, sin, tlata"; 100 + 1 = 101
        self.assertEqual(kab("waḥed"), [("waḥed", "1", C)])
        self.assertEqual(kab("mya u waḥed n wussan"), [("mya u waḥed", "101", C)])

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


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/149")
@pytest.mark.parametrize("text, expected", [
    ('ɣef lweḥda n tmeddit', [('lweḥda', '1', C)]),
    ('ɣef ssaɛtin n tmeddit', [('ssaɛtin', '2', C)]),
    ('ɣef ṛṛebɛa n tmeddit', [('ṛṛebɛa', '4', C)]),
    ('ɣef lxemsa n tmeddit', [('lxemsa', '5', C)]),
    ('ɣef ssetta n tmeddit', [('ssetta', '6', C)]),
    ('ɣef ssebɛa n tmeddit', [('ssebɛa', '7', C)]),
    ('ɣef ttmanya n tmeddit', [('ttmanya', '8', C)]),
    ('ɣef ttesɛa n tmeddit', [('ttesɛa', '9', C)]),
    ('ɣef lɛecṛa n tmeddit', [('lɛecṛa', '10', C)]),
    ('ɣef leḥdac n tmeddit', [('leḥdac', '11', C)]),
    ('ɣef ttnac n tmeddit', [('ttnac', '12', C)]),
])
def test_kab_the_clock_hours_with_the_arabic_article(text, expected):
    assert read(text, "kab") == expected


@pytest.mark.parametrize("text, expected", [
    ('mraw d yiwen', [('mraw d yiwen', '11', C)]),
    ('ɣur-i mraw d sin n wussan', [('mraw d sin', '12', C)]),
])
def test_kab_word_forms_and_the_joiner_d(text, expected):
    # "mraw d yiwen" is 10 + 1 = 11; "mraw d sin" is 10 + 2 = 12
    assert read(text, "kab") == expected



if __name__ == "__main__":
    unittest.main()
