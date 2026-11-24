"""Serbian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/sr.json."""
import unittest

import pytest

from numtag import tag_vague_quantities
from helpers import read, sure
from numtag import tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def sr(text: str) -> list[tuple[str, str, str]]:
    return read(text, "sr")


class TestSerbian(unittest.TestCase):
    def test_both_scripts_read(self):
        # 25; "љ" is the two Latin letters "lj"
        self.assertEqual(sr("двадесет пет"), [("двадесет пет", "25", C)])
        self.assertEqual(sr("хиљаду"), [("хиљаду", "1000", C)])
        self.assertEqual(sr("Хиљаду и једна ноћ"), [("Хиљаду и једна", "1001", C)])

    def test_one_to_four_decline(self):
        for form, value in (("jednim", "1"), ("jedne", "1"), ("dvema", "2"), ("dvama", "2"), ("trima", "3"),
                            ("četiriju", "4")):
            with self.subTest(form=form):
                self.assertEqual(sr(form), [(form, value, C)])

    def test_ekavian_and_ijekavian_forms(self):
        self.assertEqual(sr("dve sestre"), [("dve", "2", C)])
        self.assertEqual(sr("dvije sestre"), [("dvije", "2", C)])
        self.assertEqual(sr("dvesta"), [("dvesta", "200", C)])
        self.assertEqual(sr("dvjesta"), [("dvjesta", "200", C)])

    def test_the_scale_noun_agrees_with_its_count(self):
        # 2 x 1000; 5 x 1000; 2 x 10^6; 7 x 10^6 + 0; 2 x 1000 + 25
        self.assertEqual(sr("dve hiljade"), [("dve hiljade", "2000", C)])
        self.assertEqual(sr("pet hiljada"), [("pet hiljada", "5000", C)])
        self.assertEqual(sr("dva miliona"), [("dva miliona", "2000000", C)])
        self.assertEqual(sr("sedam miliona"), [("sedam miliona", "7000000", C)])
        self.assertEqual(sr("dve hiljade dvadeset pet"), [("dve hiljade dvadeset pet", "2025", C)])

    def test_a_plural_scale_noun_with_no_count_is_no_number(self):
        self.assertEqual(sr("Hiljade ljudi su izašle na ulice."), [])
        self.assertEqual(sr("Milioni ljudi gledaju utakmicu."), [])
        self.assertEqual(sr("Stotine ljudi su čekale."), [])

    def test_the_long_scale(self):
        # milijarda is 10^9 and bilion 10^12
        self.assertEqual(sr("dve milijarde"), [("dve milijarde", "2000000000", C)])
        self.assertEqual(sr("jedan bilion"), [("jedan bilion", "1000000000000", C)])

    def test_the_conjunction_i_is_optional(self):
        # 20 + 1 = 21 with and without "i"; two units joined by "i" are two numbers
        self.assertEqual(sr("dvadeset i jedan"), [("dvadeset i jedan", "21", C)])
        self.assertEqual(sr("dvadeset jedan"), [("dvadeset jedan", "21", C)])
        self.assertEqual(sr("pet i šest"), [("pet", "5", C), ("šest", "6", C)])

    def test_the_day_is_a_genitive_ordinal(self):
        # the 5th, the 25th and the 31st
        self.assertEqual(sr("petog maja"), [("petog", "5", O)])
        self.assertEqual(sr("dvadeset petog decembra"), [("dvadeset petog", "25", O)])
        self.assertEqual(sr("trideset prvog marta"), [("trideset prvog", "31", O)])
        self.assertEqual(sr("trećeg aprila"), [("trećeg", "3", O)])

    def test_a_year_ends_in_an_ordinal(self):
        # 2000 + 25 = 2025; 1000 + 900 + 91 = 1991
        self.assertEqual(sr("dve hiljade dvadeset pete godine"), [("dve hiljade dvadeset pete", "2025", O)])
        self.assertEqual(sr("hiljadu devetsto devedeset prve godine"),
                         [("hiljadu devetsto devedeset prve", "1991", O)])

    def test_the_hundredth_and_the_thousandth(self):
        self.assertEqual(sr("stoti rođendan"), [("stoti", "100", O)])
        self.assertEqual(sr("tristotu godišnjicu"), [("tristotu", "300", O)])
        self.assertEqual(sr("na hiljaditom kilometru"), [("hiljaditom", "1000", O)])
        self.assertEqual(sr("milioniti posetilac"), [("milioniti", "1000000", O)])

    def test_a_period_after_digits_makes_an_ordinal(self):
        self.assertEqual(sr("Rođen je 25. avgusta."), [("25", "25", O)])
        self.assertEqual(sr("Došao je u 5. Onda je otišao."), [("5", "5", C)])

    def test_fractions_count_parts(self):
        # 3/4 = 0.75; 2/3; 5/8 = 0.625; 3/1000 = 0.003
        self.assertEqual(sr("tri četvrtine"), [("tri četvrtine", "0.75", F)])
        self.assertEqual(sr("dve trećine"), [("dve trećine", "2/3", F)])
        self.assertEqual(sr("pet osmina"), [("pet osmina", "0.625", F)])
        self.assertEqual(sr("tri hiljaditine"), [("tri hiljaditine", "0.003", F)])

    def test_decimals(self):
        self.assertEqual(sr("dva zarez pet"), [("dva zarez pet", "2.5", D)])
        self.assertEqual(sr("tri koma četiri"), [("tri koma četiri", "3.4", D)])
        self.assertEqual(sr("2,5 evra"), [("2,5", "2.5", D)])
        self.assertEqual(sr("1.500.000 stanovnika"), [("1.500.000", "1500000", C)])

    def test_homographs_are_not_sure(self):
        # "drugi" is also "other", "četvrti" also "quarters", "jednom" also "once", "pola" also "of the sex"
        self.assertEqual(sure("drugi put", "sr"), [("drugi", "2", 0.4)])
        self.assertEqual(sure("u četvrti", "sr"), [("četvrti", "4", 0.4)])
        self.assertEqual(sure("Bio sam tamo jednom.", "sr"), [("jednom", "1", 0.4)])
        self.assertEqual(sure("pola sata", "sr"), [("pola", "0.5", 0.4)])
        self.assertEqual(sure("četvrtog jula", "sr"), [("četvrtog", "4", 1.0)])

    def test_a_vague_amount_holds_no_number(self):
        self.assertEqual(sr("nekoliko hiljada ljudi"), [])
        self.assertEqual(sr("desetak hiljada ljudi"), [])
        self.assertEqual([q.text for q in tag_vague_quantities("nekoliko hiljada ljudi", "sr")],
                         ["nekoliko hiljada"])


class TestOpenIssues(unittest.TestCase):
    # Rows each open issue lists. The expected value is the issue's, worked out by hand.

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/250")
    def test_bilijarda_is_ten_to_the_fifteenth(self):
        self.assertEqual(read("jedan bilijarda", "sr"), [("jedan bilijarda", "1000000000000000", C)])

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/250")
    def test_three_bilijarde(self):
        self.assertEqual(read("tri bilijarde", "sr"), [("tri bilijarde", "3000000000000000", C)])

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/251")
    def test_quarter_noun_after_a_whole(self):
        self.assertEqual(read("tri i četvrt", "sr"), [("tri i četvrt", "3.25", F)])

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/251")
    def test_quarter_noun_before_a_unit(self):
        self.assertEqual(read("četvrt sata", "sr"), [("četvrt", "0.25", F)])

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/251")
    def test_collective_dvojica(self):
        self.assertEqual(read("Došla su dvojica ljudi.", "sr"), [("dvojica", "2", C)])

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/251")
    def test_collective_troje(self):
        self.assertEqual(read("troje dece", "sr"), [("troje", "3", C)])


if __name__ == "__main__":
    unittest.main()
