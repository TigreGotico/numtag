"""Maltese grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/mt.json."""
import unittest

import pytest

from helpers import read
from numtag import tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def mt(text: str) -> list[tuple[str, str, str]]:
    return read(text, "mt")


class TestUnits(unittest.TestCase):
    def test_a_counted_noun_takes_the_short_form(self):
        # "tnejn" counts alone, "żewġ" stands before the noun: both are 2
        self.assertEqual(mt("tnejn"), [("tnejn", "2", C)])
        self.assertEqual(mt("żewġ kotba"), [("żewġ", "2", C)])

    def test_the_apostrophe_of_a_short_form_stays_outside_the_span(self):
        # "erba'" is the short form of "erbgħa", 4
        self.assertEqual(mt("erba' kotba"), [("erba", "4", C)])

    def test_a_teen_before_a_noun_takes_il(self):
        # 11 and 11 x 1000
        self.assertEqual(mt("ħdax-il ktieb"), [("ħdax-il", "11", C)])
        self.assertEqual(mt("ħdax-il elf"), [("ħdax-il elf", "11000", C)])


class TestTensAndHundreds(unittest.TestCase):
    def test_the_unit_comes_first_and_u_joins_the_ten(self):
        # 5 + 20 = 25
        self.assertEqual(mt("ħamsa u għoxrin"), [("ħamsa u għoxrin", "25", C)])

    def test_hundreds(self):
        # 100; 2 x 100; 3 x 100; 9 x 100; 100 + 5
        self.assertEqual(mt("mija"), [("mija", "100", C)])
        self.assertEqual(mt("mitejn"), [("mitejn", "200", C)])
        self.assertEqual(mt("tliet mija"), [("tliet mija", "300", C)])
        self.assertEqual(mt("disa' mija"), [("disa' mija", "900", C)])
        self.assertEqual(mt("mija u ħamsa"), [("mija u ħamsa", "105", C)])

    def test_mitt_is_the_hundred_before_a_noun(self):
        self.assertEqual(mt("mitt ewro"), [("mitt", "100", C)])


class TestScale(unittest.TestCase):
    def test_thousands(self):
        # 1000; 2 x 1000; 3 x 1000
        self.assertEqual(mt("elf"), [("elf", "1000", C)])
        self.assertEqual(mt("elfejn"), [("elfejn", "2000", C)])
        self.assertEqual(mt("tlitt elef"), [("tlitt elef", "3000", C)])

    def test_u_joins_the_groups(self):
        # 1000 + 9 x 100 + 4 + 60 = 1964
        self.assertEqual(mt("elf u disa' mija u erbgħa u sittin"),
                         [("elf u disa' mija u erbgħa u sittin", "1964", C)])

    def test_the_scale_noun_keeps_the_singular_after_a_teen(self):
        # 13 x 1000000
        self.assertEqual(mt("tlettax-il miljun ewro"), [("tlettax-il miljun", "13000000", C)])

    def test_biljun_is_ten_to_the_ninth(self):
        self.assertEqual(mt("biljun"), [("biljun", "1000000000", C)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/241")
    def test_a_short_form_with_an_apostrophe_before_a_scale_word(self):
        # 4 x 1000000
        self.assertEqual(mt("erbaʼ miljuni"), [("erbaʼ miljuni", "4000000", C)])


class TestArticle(unittest.TestCase):
    def test_the_article_goes_with_the_ordinal(self):
        self.assertEqual(mt("l-ewwel premju"), [("l-ewwel", "1", O)])
        self.assertEqual(mt("it-tieni triq"), [("it-tieni", "2", O)])
        self.assertEqual(mt("ir-raba' kapitlu"), [("ir-raba", "4", O)])

    def test_a_preposition_with_the_article_goes_with_the_cardinal(self):
        # 5 + 20 = 25
        self.assertEqual(mt("fil-ħamsa u għoxrin ta' Diċembru"), [("fil-ħamsa u għoxrin", "25", C)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/240")
    def test_an_ordinal_from_five_to_ten_after_the_article(self):
        self.assertEqual(mt("Dan huwa l-ħames kapitlu."), [("l-ħames", "5", O)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/240")
    def test_digits_after_the_article(self):
        self.assertEqual(mt("Malta saret indipendenti fl-1964."), [("1964", "1964", C)])


class TestFractionsAndDecimals(unittest.TestCase):
    def test_fractions(self):
        # 1/3; 2/3; 3 x 1/4 = 0.75
        self.assertEqual(mt("terz"), [("terz", "1/3", F)])
        self.assertEqual(mt("żewġ terzi"), [("żewġ terzi", "2/3", F)])
        self.assertEqual(mt("tliet kwarti"), [("tliet kwarti", "0.75", F)])

    def test_punt_starts_the_decimals(self):
        # 2 + 5/10 = 2.5
        self.assertEqual(mt("tnejn punt ħamsa"), [("tnejn punt ħamsa", "2.5", D)])

    def test_the_decimal_mark_is_a_point_and_the_group_mark_a_comma(self):
        self.assertEqual(mt("2.5"), [("2.5", "2.5", D)])
        self.assertEqual(mt("1,000"), [("1,000", "1000", C)])


class TestOpenIssues(unittest.TestCase):
    # Rows each open issue lists. The expected value is the issue's, worked out by hand.

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/248")
    def test_weekday_it_tnejn_is_no_sure_number(self):
        self.assertEqual([m.text for m in tag_numbers("Nhar it-Tnejn immur l-iskola.", "mt") if m.confidence >= 1.0], [])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/248")
    def test_weekday_it_tlieta_is_no_sure_number(self):
        self.assertEqual([m.text for m in tag_numbers("Nhar it-Tlieta immur l-iskola.", "mt") if m.confidence >= 1.0], [])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/248")
    def test_weekday_l_erbgha_is_no_sure_number(self):
        self.assertEqual([m.text for m in tag_numbers("Nhar l-Erbgħa immur l-iskola.", "mt") if m.confidence >= 1.0], [])


if __name__ == "__main__":
    unittest.main()
