"""Finnish, Estonian, Hungarian, Turkish and Azerbaijani grammar rules. Each
expected value is worked out by hand in the comment beside it; sources are in
numtag/lexicon/<lang>.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


class TestCompoundWords(unittest.TestCase):
    def test_a_finnish_number_is_one_word(self):
        # 2 x 1000 + 5 x 100 + 2 x 10 + 1 = 2521
        self.assertEqual(read("kaksituhattaviisisataakaksikymmentäyksi", "fi"),
                         [("kaksituhattaviisisataakaksikymmentäyksi", "2521", C)])

    def test_hungarian_hyphenates_above_two_thousand(self):
        # 2 x 1000 + 500 = 2500; 1000 + 900 + 90 + 9 = 1999
        self.assertEqual(read("kétezer-ötszáz", "hu"), [("kétezer-ötszáz", "2500", C)])
        self.assertEqual(read("ezerkilencszázkilencvenkilenc", "hu"),
                         [("ezerkilencszázkilencvenkilenc", "1999", C)])

    def test_a_word_that_splits_into_two_numbers_is_no_number(self):
        # "viisi" + "kolme" in one word is no well-formed number
        self.assertEqual(read("viisikolme", "fi"), [])


class TestGroupsAfterAScale(unittest.TestCase):
    def test_a_bare_hundred_or_ten_after_thousands_joins_the_number(self):
        # 10^6 + 2 x 1000 + 100 + 40 + 5 = 1002145
        self.assertEqual(read("bir milyon iki bin yüz kırk beş", "tr"),
                         [("bir milyon iki bin yüz kırk beş", "1002145", C)])
        # 10^6 + 2 x 1000 + 10 = 1002010
        self.assertEqual(read("miljoona kaksituhatta kymmenen", "fi"), [("miljoona kaksituhatta kymmenen", "1002010", C)])


class TestTeensAndTens(unittest.TestCase):
    def test_a_teen_is_a_unit_and_a_bound_ten(self):
        # 1 + 10 = 11; 2 + 10 = 12; Hungarian 10 + 1 = 11, 20 + 5 = 25
        self.assertEqual(read("yksitoista", "fi"), [("yksitoista", "11", C)])
        self.assertEqual(read("kaksteist", "et"), [("kaksteist", "12", C)])
        self.assertEqual(read("tizenegy huszonöt", "hu"), [("tizenegy", "11", C), ("huszonöt", "25", C)])

    def test_a_ten_multiplier_counts_tens(self):
        # 3 x 10 = 30; 3 x 10 + 4 = 34
        self.assertEqual(read("kolmekymmentä", "fi"), [("kolmekymmentä", "30", C)])
        self.assertEqual(read("kolmkümmend neli", "et"), [("kolmkümmend neli", "34", C)])

    def test_a_turkic_ten_takes_a_unit(self):
        # 10 + 4 = 14; 40 + 5 = 45
        self.assertEqual(read("on dört", "tr"), [("on dört", "14", C)])
        self.assertEqual(read("qırx beş", "az"), [("qırx beş", "45", C)])


class TestInflection(unittest.TestCase):
    def test_every_part_of_a_finnish_number_takes_the_case(self):
        # allative of 35: 3 x 10 + 5
        self.assertEqual(read("kolmellekymmenelleviidelle", "fi"), [("kolmellekymmenelleviidelle", "35", C)])
        # inessive of 2500
        self.assertEqual(read("kahdessatuhannessaviidessäsadassa", "fi"),
                         [("kahdessatuhannessaviidessäsadassa", "2500", C)])

    def test_every_part_of_an_estonian_number_takes_the_case(self):
        # allative of 25: 2 x 10 + 5
        self.assertEqual(read("kahekümne viiele", "et"), [("kahekümne viiele", "25", C)])

    def test_a_turkic_case_ending_goes_on_the_last_word(self):
        # 1000 + 900 + 80 + 4 = 1984, locative; 20 + 5 = 25, dative
        self.assertEqual(read("bin dokuz yüz seksen dörtte doğdu", "tr"), [("bin dokuz yüz seksen dörtte", "1984", C)])
        self.assertEqual(read("iyirmi beşə qədər", "az"), [("iyirmi beşə", "25", C)])
        self.assertEqual(read("kétezer-ötszázat", "hu"), [("kétezer-ötszázat", "2500", C)])

    def test_a_case_ending_closes_the_number(self):
        # "beşte" (at five) ends the number, so "iki" (two) starts the next one
        self.assertEqual(read("saat beşte iki kişi geldi", "tr"), [("beşte", "5", C), ("iki", "2", C)])

    def test_a_case_ending_ends_the_count_of_a_scale_word(self):
        # "ikide" (at two) is no count of "yüz": 2 and 100, not 200
        self.assertEqual(read("ikide yüz kişi vardı", "tr"), [("ikide", "2", C), ("yüz", "100", C)])

    def test_the_turkish_stem_change_before_a_vowel(self):
        # dört -> dörd- before a vowel: accusative "dördü", dative "dörde"; "dörtte" keeps t
        self.assertEqual(read("dördü dörde dörtte", "tr"), [("dördü", "4", C), ("dörde", "4", C), ("dörtte", "4", C)])

    def test_a_listed_form_is_no_number(self):
        # "yüzde" is percent, not "at a hundred"
        self.assertEqual(read("yüzde kırk", "tr"), [("kırk", "40", C)])


class TestOrdinals(unittest.TestCase):
    def test_the_last_word_decides_the_kind(self):
        # 20 + 1 = 21, every part ordinal in Finnish; only the last in Turkish
        self.assertEqual(read("kahdeskymmenesensimmäinen", "fi"), [("kahdeskymmenesensimmäinen", "21", O)])
        self.assertEqual(read("yirmi birinci yüzyıl", "tr"), [("yirmi birinci", "21", O)])
        self.assertEqual(read("huszonötödik", "hu"), [("huszonötödik", "25", O)])

    def test_an_inflected_ordinal_is_ordinal(self):
        # elative of the 3rd; inessive of the 5th
        self.assertEqual(read("kolmannesta", "fi"), [("kolmannesta", "3", O)])
        self.assertEqual(read("ikinciden sonra", "tr"), [("ikinciden", "2", O)])

    def test_an_ordinal_form_counts_no_parts(self):
        # elative of the 20th, not 2 tenths
        self.assertEqual(read("kahdennestakymmenennestä", "fi"), [("kahdennestakymmenennestä", "20", O)])

    def test_an_estonian_form_that_is_also_a_case_reads_as_the_ordinal(self):
        # "viies" is the 5th and also the inessive of "viis"
        self.assertEqual(read("viies", "et"), [("viies", "5", O)])

    def test_a_period_after_digits_makes_an_ordinal(self):
        self.assertEqual(read("Asumme 5. kerroksessa.", "fi"), [("5", "5", O)])
        self.assertEqual(read("Az 5. emeleten lakunk.", "hu"), [("5", "5", O)])
        # a period that ends the sentence is no ordinal mark
        self.assertEqual(read("Kokous on 5. Se alkaa.", "fi"), [("5", "5", C)])

    def test_an_apostrophe_suffix_after_digits(self):
        self.assertEqual(read("5'inci sınıf", "tr"), [("5'inci", "5", O)])


class TestDigitCaseEndings(unittest.TestCase):
    def test_a_case_ending_after_digits_is_dropped(self):
        self.assertEqual(read("Jaa luku 5:llä.", "fi"), [("5", "5", C)])
        self.assertEqual(read("5-öt fizettem", "hu"), [("5", "5", C)])
        self.assertEqual(read("Toplantı 5'te başlıyor.", "tr"), [("5", "5", C)])


class TestFractionsAndDecimals(unittest.TestCase):
    def test_a_bound_half_follows_its_count(self):
        # 2 + 1/2 = 2.5; 2.5 x 10^6 = 2500000
        self.assertEqual(read("iki buçuk litre", "tr"), [("iki buçuk", "2.5", F)])
        self.assertEqual(read("iki buçuk milyon", "tr"), [("iki buçuk milyon", "2500000", C)])

    def test_a_part_word_alone_is_one_part(self):
        # 1/4; 1/3
        self.assertEqual(read("Ootasin veerand tundi.", "et"), [("veerand", "0.25", F)])
        self.assertEqual(read("kolmannes", "fi"), [("kolmannes", "1/3", F)])

    def test_a_value_word(self):
        # one and a half
        self.assertEqual(read("másfél óra", "hu"), [("másfél", "1.5", F)])
        self.assertEqual(read("puolitoista tuntia", "fi"), [("puolitoista", "1.5", F)])

    def test_hungarian_reads_a_decimal_as_whole_and_parts(self):
        # 5 + 2/10 = 5.2; 3 + 15/100 = 3.15; 1 + 5/1000 = 1.005
        self.assertEqual(read("öt egész két tized", "hu"), [("öt egész két tized", "5.2", D)])
        self.assertEqual(read("három egész tizenöt század", "hu"), [("három egész tizenöt század", "3.15", D)])
        self.assertEqual(read("egy egész öt ezred", "hu"), [("egy egész öt ezred", "1.005", D)])

    def test_a_part_word_after_a_count_stays_singular(self):
        # 2/3; 3/4 = 0.75
        self.assertEqual(read("két harmad", "hu"), [("két harmad", "2/3", F)])
        self.assertEqual(read("üç çeyrek saat", "tr"), [("üç çeyrek", "0.75", F)])

    def test_azerbaijani_decimal_words(self):
        # 2 + 5/10 = 2.5
        self.assertEqual(read("iki tam beş", "az"), [("iki tam beş", "2.5", D)])


class TestCaseFolding(unittest.TestCase):
    def test_a_dotted_capital_i(self):
        # Turkish İ folds to i, I to ı
        self.assertEqual(read("İKİ BİN", "tr"), [("İKİ BİN", "2000", C)])
        self.assertEqual(read("ALTI", "tr"), [("ALTI", "6", C)])


class TestConfidence(unittest.TestCase):
    def confidence(self, text, lang):
        return [(m.text, m.confidence < 0.5) for m in tag_numbers(text, lang)]

    def test_a_lone_word_with_another_common_meaning_is_weak(self):
        # "sataa" is "it rains"; "yhdessä" is "together"; "ona" is "to him"
        self.assertEqual(self.confidence("Ulkona sataa.", "fi"), [("sataa", True)])
        self.assertEqual(self.confidence("Teimme sen yhdessä.", "fi"), [("yhdessä", True)])
        self.assertEqual(self.confidence("Ona söyledim.", "tr"), [("Ona", True)])

    def test_the_same_word_inside_a_number_is_sure(self):
        # 100 x 1000 = 100000 in the partitive
        self.assertEqual(self.confidence("sataatuhatta", "fi"), [("sataatuhatta", False)])
        self.assertEqual(self.confidence("on dört", "tr"), [("on dört", False)])

    def test_an_article_before_a_noun_is_weak(self):
        self.assertEqual(self.confidence("bir elma aldım", "tr"), [("bir", True)])
        self.assertEqual(self.confidence("van egy almám", "hu"), [("egy", True)])


if __name__ == "__main__":
    unittest.main()
