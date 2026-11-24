"""Lithuanian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/lt.json."""
import unittest

import pytest

from numtag import tag_vague_quantities
from helpers import read, sure

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def lt(text: str) -> list[tuple[str, str, str]]:
    return read(text, "lt")


class TestLithuanian(unittest.TestCase):
    def test_every_case_of_a_cardinal_reads(self):
        # 5 in the genitive, accusative, dative, instrumental and locative
        for form in ("penkių", "penkis", "penkiems", "penkiais", "penkiuose", "penkias", "penkioms"):
            with self.subTest(form=form):
                self.assertEqual(lt(form), [(form, "5", C)])
        # 11 in the accusative as the norm writes it, and as CLDR writes it
        self.assertEqual(lt("vienuolika"), [("vienuolika", "11", C)])
        self.assertEqual(lt("vienuoliką"), [("vienuoliką", "11", C)])

    def test_the_hundreds_and_thousands_are_counted_nouns(self):
        # 2 x 100 + 50 = 250; 2 x 1000 + 25 = 2025; 14 x 1000 = 14000
        self.assertEqual(lt("dviejų šimtų penkiasdešimt"), [("dviejų šimtų penkiasdešimt", "250", C)])
        self.assertEqual(lt("du tūkstančiai dvidešimt penki"), [("du tūkstančiai dvidešimt penki", "2025", C)])
        self.assertEqual(lt("keturiolika tūkstančių"), [("keturiolika tūkstančių", "14000", C)])
        # 2 x 10^6 + 3 x 100 x 1000 = 2300000
        self.assertEqual(lt("du milijonai trys šimtai tūkstančių"),
                         [("du milijonai trys šimtai tūkstančių", "2300000", C)])

    def test_a_plural_scale_word_with_no_count_is_no_number(self):
        self.assertEqual(lt("Šimtai žmonių laukė."), [])
        self.assertEqual(lt("Tūkstančiai paukščių išskrido."), [])

    def test_the_short_scale(self):
        # trilijonas is 10^12 in the short scale, the Lithuanian default
        self.assertEqual(lt("vienas trilijonas"), [("vienas trilijonas", "1000000000000", C)])
        self.assertEqual(lt("du milijardai"), [("du milijardai", "2000000000", C)])

    def test_the_pronominal_ordinal_names_the_day(self):
        # the 5th, the 21st and the 31st of a month
        self.assertEqual(lt("gegužės penktąją"), [("penktąją", "5", O)])
        self.assertEqual(lt("birželio dvidešimt pirmąją"), [("dvidešimt pirmąją", "21", O)])
        self.assertEqual(lt("iki gruodžio trisdešimt pirmosios"), [("trisdešimt pirmosios", "31", O)])
        self.assertEqual(lt("trečiąją"), [("trečiąją", "3", O)])
        self.assertEqual(lt("tretieji"), [("tretieji", "3", O)])

    def test_a_year_ends_in_an_ordinal(self):
        # 2000 + 25 = 2025; 1000 + 900 + 90 = 1990
        self.assertEqual(lt("du tūkstančiai dvidešimt penktieji metai"),
                         [("du tūkstančiai dvidešimt penktieji", "2025", O)])
        self.assertEqual(lt("tūkstantis devyni šimtai devyniasdešimtaisiais metais"),
                         [("tūkstantis devyni šimtai devyniasdešimtaisiais", "1990", O)])

    def test_the_round_hundredth_and_thousandth(self):
        self.assertEqual(lt("šimtasis koncertas"), [("šimtasis", "100", O)])
        self.assertEqual(lt("šimtame puslapyje"), [("šimtame", "100", O)])
        self.assertEqual(lt("tūkstantasis lankytojas"), [("tūkstantasis", "1000", O)])
        # 2 x 100 = 200: a count before the 100th counts hundreds
        self.assertEqual(lt("du šimtasis"), [("du šimtasis", "200", O)])
        # "šimtas" is the cardinal noun, not the indefinite ordinal
        self.assertEqual(lt("šimtas"), [("šimtas", "100", C)])

    def test_an_ending_after_a_hyphen_makes_digits_an_ordinal(self):
        self.assertEqual(lt("Vasario 16-oji"), [("16-oji", "16", O)])
        self.assertEqual(lt("2025-aisiais metais"), [("2025-aisiais", "2025", O)])
        self.assertEqual(lt("3-iasis"), [("3-iasis", "3", O)])

    def test_fractions_name_their_parts_with_the_feminine_ordinal(self):
        # 3/5 = 0.6; 1/2 = 0.5; 7/10 = 0.7; 3/4 = 0.75
        self.assertEqual(lt("trys penktosios"), [("trys penktosios", "0.6", F)])
        self.assertEqual(lt("viena antroji"), [("viena antroji", "0.5", F)])
        self.assertEqual(lt("septynias dešimtąsias"), [("septynias dešimtąsias", "0.7", F)])
        self.assertEqual(lt("tris ketvirtadalius"), [("tris ketvirtadalius", "0.75", F)])
        self.assertEqual(lt("dvi trečiosios"), [("dvi trečiosios", "2/3", F)])

    def test_the_quarter_noun_softens_t_to_c_before_i(self):
        # 3 x 1/4 = 0.75
        self.assertEqual(lt("trys ketvirčiai"), [("trys ketvirčiai", "0.75", F)])
        self.assertEqual(lt("tris ketvirčius"), [("tris ketvirčius", "0.75", F)])

    def test_ir_joins_a_whole_number_to_a_fraction_only(self):
        # 2 + 5/10 = 2.5; 3 + 1/2 = 3.5; "penki ir šeši" is two numbers
        self.assertEqual(lt("du ir penkios dešimtosios"), [("du ir penkios dešimtosios", "2.5", F)])
        self.assertEqual(lt("tris ir pusę"), [("tris ir pusę", "3.5", F)])
        self.assertEqual(lt("penki ir šeši"), [("penki", "5", C), ("šeši", "6", C)])

    def test_halves(self):
        # 3/2 and 5/2
        self.assertEqual(lt("pusantro litro"), [("pusantro", "1.5", F)])
        self.assertEqual(lt("pustrečio mėnesio"), [("pustrečio", "2.5", F)])
        # "pusė" is also "side": alone it is not sure
        self.assertEqual(sure("pusė valandos", "lt"), [("pusė", "0.5", 0.4)])

    def test_the_decimal_comma_and_its_word(self):
        self.assertEqual(lt("trys kablelis penki"), [("trys kablelis penki", "3.5", D)])
        self.assertEqual(lt("2,5 laipsnio"), [("2,5", "2.5", D)])
        self.assertEqual(lt("2 800 000 žmonių"), [("2 800 000", "2800000", C)])

    def test_ten_is_also_a_noun(self):
        # 2 x 10 = 20; a plural ten with no count is no number
        self.assertEqual(lt("dvi dešimtys"), [("dvi dešimtys", "20", C)])
        self.assertEqual(lt("iki dešimties"), [("dešimties", "10", C)])
        self.assertEqual(lt("Dešimtys tūkstančių žmonių protestavo."), [])

    def test_the_plural_of_one_is_also_alone(self):
        self.assertEqual(sure("vieni metai", "lt"), [("vieni", "1", 0.4)])

    def test_a_vague_amount_holds_no_number(self):
        self.assertEqual(lt("keli tūkstančiai žmonių"), [])
        self.assertEqual(lt("prieš kelias dienas"), [])
        self.assertEqual(lt("po keleto metų"), [])
        self.assertEqual([q.text for q in tag_vague_quantities("keli tūkstančiai žmonių", "lt")],
                         ["keli tūkstančiai"])


class TestOpenIssues(unittest.TestCase):
    # Rows each open issue lists. The expected value is the issue's, worked out by hand.

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/252")
    def test_collective_dveji(self):
        self.assertEqual(read("dveji metai", "lt"), [("dveji", "2", C)])

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/252")
    def test_collective_dvejus(self):
        self.assertEqual(read("prieš dvejus metus", "lt"), [("dvejus", "2", C)])

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/252")
    def test_collective_treji(self):
        self.assertEqual(read("treji metai", "lt"), [("treji", "3", C)])


if __name__ == "__main__":
    unittest.main()
