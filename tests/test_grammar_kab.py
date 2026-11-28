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



@pytest.mark.parametrize("text, expected", [
    # 17 x 1000 = 17000; 3 x 10^6; 13 x 10^6 with the annexed plural
    ("sbeɛṭac n alef", [("sbeɛṭac n alef", "17000", C)]),
    ("kṛad n yimelyunen n yidularen", [("kṛad n yimelyunen", "3000000", C)]),
    ("Sɛiɣ ṭnac n yimelyunen", [("ṭnac n yimelyunen", "12000000", C)]),
    # 5 x 100 = 500; 500 + 30 = 530; 500 x 10^9
    ("xemsmya u tlatin", [("xemsmya u tlatin", "530", C)]),
    ("xemsmeyya n yimelyaṛen", [("xemsmeyya n yimelyaṛen", "500000000000", C)]),
])
def test_kab_a_count_of_scale_nouns_and_fused_hundreds(text, expected):
    assert read(text, "kab") == expected


@pytest.mark.parametrize("text, expected", [
    # 106 + 74/100; 3 + 3/100
    ("meyya d setta tafrayt rebεa u sebεin", [("meyya d setta tafrayt rebεa u sebεin", "106.74", D)]),
    ("tlata ticcert ilem tlata", [("tlata ticcert ilem tlata", "3.03", D)]),
])
def test_kab_the_decimal_marker(text, expected):
    assert read(text, "kab") == expected


@pytest.mark.parametrize("text, expected", [
    # Dallet p. 704: errbaɛ is a quarter; 3/4 = 0.75; 1/3 of a loaf
    ("tlata errbaɛ n weɣrum", [("tlata errbaɛ", "0.75", F)]),
    ("Yečča kan rrbeɛ n uɣrum", [("rrbeɛ", "0.25", F)]),
])
def test_kab_fractions(text, expected):
    assert read(text, "kab") == expected


@pytest.mark.parametrize("text, expected", [
    # Mokraoui (2026), numtag #379: "1/3: afkraḍ ; 1/4: afkuẓ ; 2/3: sin ifekṛad"
    ("Ččiɣ afkraḍ n weɣrum.", [("afkraḍ", "1/3", F)]),
    ("Yeqqim-d afkuẓ n wakud.", [("afkuẓ", "0.25", F)]),
    # 2 x 1/3 = 2/3
    ("Yeǧǧa sin ifekṛad n wakal i mmi-s.", [("sin ifekṛad", "2/3", F)]),
    # no part word after the count: the count stays 2
    ("Yeǧǧa sin n warrac.", [("sin", "2", C)]),
])
def test_kab_named_fractions(text, expected):
    assert read(text, "kab") == expected


@pytest.mark.parametrize("value", ["1/3", "1/4", "2/3"])
def test_kab_named_fractions_round_trip(value):
    from fractions import Fraction

    from numtag import spell, tag_numbers
    words = spell(value, "kab")[0].text
    mentions = tag_numbers(words, "kab")
    assert [(m.text, Fraction(m.value)) for m in mentions] == [(words, Fraction(value))]


@pytest.mark.parametrize("text, expected", [
    # seg, deg and ɣef between two counts are no fraction: "one of the two", "24 on 24", a score
    ("Issefk-ak ad ferneḍ yiwen seg sin iɣawasen-a.", [("yiwen", "1", C), ("sin", "2", C)]),
    ("Yettwali 24 ɣef 24", [("24", "24", C), ("24", "24", C)]),
    ("yiwen deg yiwen", [("yiwen", "1", C), ("yiwen", "1", C)]),
    ("tlata ɣef yiwen", [("tlata", "3", C), ("yiwen", "1", C)]),
])
def test_kab_seg_deg_and_ɣef_make_no_fraction(text, expected):
    assert read(text, "kab") == expected


if __name__ == "__main__":
    unittest.main()


@pytest.mark.parametrize("text, expected", [
    # the verb "she has": 100 + 5 + 20 = 125, × 1000 = 125000, + 3 = 125003
    ('Deg useggas-agi, tamdint-nneɣ tesɛa miya u xemsa u ɛecrin alef u tlata n yimezdaɣ.',
     [('miya u xemsa u ɛecrin alef u tlata', '125003', C)]),
    ('Tamdint-nneɣ tesεa miya n yimezdaɣ.', [('miya', '100', C)]),
    ('Taddart-nneɣ tesɛa 300 n yimezdaɣ.', [('300', '300', C)]),
    # before a noun or "n", "tesɛa" stays the number 9
    ('Ɛedda-d tesɛa n yiseggasen.', [('tesɛa', '9', C)]),
    ('Tesɛa ixxamen i yellan deg taddart.', [('Tesɛa', '9', C)]),
    ('tesɛa u ɛecrin', [('tesɛa u ɛecrin', '29', C)]),
])
def test_kab_tesa_before_a_number_is_the_verb(text, expected):
    assert read(text, "kab") == expected


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/421")
@pytest.mark.parametrize("text, expected", [
    ('Deg taddart-nneɣ, semmus seg mraw n yixxamen ur sɛin ara aman deg unebdu.', [('semmus seg mraw', '5/10', F)]),
    ('Deg taddart-nneɣ, sin yeḥricen ɣef kraḍ n yilmeẓyen ruḥen ad xedmen di tmdinin timeqranin.',
     [('sin yeḥricen ɣef kraḍ', '2/3', F)]),
    ('Ass-a, sdis ɣef tmanya seg yinelmaden ur d-usin ara ɣer uɣerbaz acku yewwi-d ugeffur.', [('sdis ɣef tmanya', '6/8', F)]),
    ('Deg useggas-a, sebɛa u rebɛin deg temiya n yinelmaden kan i yeɛddan akayad n tagara.',
     [('sebɛa u rebɛin deg temiya', '47/100', F)]),
    ('Ass-a, sin ɣef mraw kan seg yinelmaden i d-yusan ɣer uɣerbaz acku yella ugeffur d ameqqran.', [('sin ɣef mraw', '2/10', F)]),
    ('Ass-a, rebɛa ɣef tnac seg yinelmaden ur d-usin ara ɣer uɣerbaz acku yella ugeffur d aṭas.', [('rebɛa ɣef tnac', '4/12', F)]),
    ('Ass-a, sebɛa deg mraw n yinelmaden ur d-usin ara ɣer uɣerbaz acku yella ugeffur meqqer.', [('sebɛa deg mraw', '7/10', F)]),
])
def test_kab_a_count_over_a_count_is_a_fraction(text, expected):
    assert read(text, "kab") == expected
