"""French grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/fr-FR.json, fr-BE.json and
fr-CH.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C, O, F = "cardinal", "ordinal", "fraction"


def fr(text: str, lang: str = "fr-FR") -> list[tuple[str, str, str]]:
    return read(text, lang)


def confidence(text: str, lang: str) -> list[tuple[str, float]]:
    return [(m.text, m.confidence) for m in tag_numbers(text, lang)]


class TestVigesimalTens(unittest.TestCase):
    def test_soixante_takes_the_teens(self):
        # 60 + 17 = 77; 60 + 11 = 71
        self.assertEqual(fr("soixante-dix-sept"), [("soixante-dix-sept", "77", C)])
        self.assertEqual(fr("soixante et onze"), [("soixante et onze", "71", C)])

    def test_quatre_vingt_takes_the_teens(self):
        # 4 x 20 + 19 = 99; 4 x 20 + 11 = 91
        self.assertEqual(fr("quatre-vingt-dix-neuf"), [("quatre-vingt-dix-neuf", "99", C)])
        self.assertEqual(fr("quatre-vingt-onze"), [("quatre-vingt-onze", "91", C)])

    def test_a_number_word_of_several_words_is_one_word(self):
        # "quatre-vingts" is 80, with a hyphen or a space; "dix-sept" is 17
        self.assertEqual(fr("quatre-vingts"), [("quatre-vingts", "80", C)])
        self.assertEqual(fr("quatre vingt dix"), [("quatre vingt dix", "90", C)])
        self.assertEqual(fr("dix sept"), [("dix sept", "17", C)])

    def test_an_ordinal_after_a_vigesimal_ten_takes_the_teens(self):
        # 60 + 10 = 70; 4 x 20 + 19 = 99
        self.assertEqual(fr("soixante-dixième"), [("soixante-dixième", "70", O)])
        self.assertEqual(fr("quatre-vingt-dix-neuvième"), [("quatre-vingt-dix-neuvième", "99", O)])
        self.assertEqual(fr("vingt et unième"), [("vingt et unième", "21", O)])


class TestRegionalTens(unittest.TestCase):
    def test_septante_is_belgian(self):
        # 70 + 7 = 77
        self.assertEqual(fr("septante-sept", "fr-BE"), [("septante-sept", "77", C)])
        self.assertEqual(fr("septante"), [])

    def test_huitante_is_swiss(self):
        # 80 + 2 = 82
        self.assertEqual(fr("huitante-deux", "fr-CH"), [("huitante-deux", "82", C)])
        self.assertEqual(fr("huitante", "fr-BE"), [])


class TestScaleNouns(unittest.TestCase):
    def test_a_singular_scale_noun_takes_only_the_count_one(self):
        # "deux millions" is 2 x 1000000; "deux million" is no number of millions
        self.assertEqual(fr("deux millions"), [("deux millions", "2000000", C)])
        self.assertEqual(fr("deux million"), [("deux", "2", C)])

    def test_et_demi_adds_half_the_scale_noun(self):
        # 1000000 + 1000000 / 2 = 1500000
        self.assertEqual(fr("un million et demi"), [("un million et demi", "1500000", C)])

    def test_a_group_of_a_higher_scale_is_no_count_of_cent(self):
        # 2 x 1000000 + 3 x 1000 + 100 = 2003100; 4000000 + 4000 + 100 + 99 = 4004199
        self.assertEqual(fr("deux millions trois mille cent"), [("deux millions trois mille cent", "2003100", C)])
        self.assertEqual(fr("quatre millions quatre mille cent quatre-vingt-dix-neuf"),
                         [("quatre millions quatre mille cent quatre-vingt-dix-neuf", "4004199", C)])

    def test_un_demi_is_one_half(self):
        self.assertEqual(fr("un demi"), [("un demi", "0.5", F)])

    def test_tiers_is_the_same_in_the_plural(self):
        self.assertEqual(fr("deux tiers"), [("deux tiers", "2/3", F)])


class TestMinus(unittest.TestCase):
    def test_moins_after_a_is_a_minus(self):
        self.assertEqual(fr("descendue à moins cinq degrés"), [("moins cinq", "-5", C)])

    def test_au_moins_is_no_minus(self):
        self.assertEqual(fr("au moins trois"), [("trois", "3", C)])



class TestHomographs(unittest.TestCase):
    def test_an_article_before_a_hyphenated_noun_is_weak(self):
        self.assertEqual([(m.text, m.confidence) for m in tag_numbers("Prends un rendez-vous.", "fr-FR")],
                         [("un", 0.3)])

    def test_cent_after_pour_and_a_number_is_the_percent_sign(self):
        # six percent, not 6 and 100; "cent pour cent" is 100 once
        for lang in ("fr-FR", "fr-BE", "fr-CH"):
            with self.subTest(lang=lang):
                self.assertEqual(read("Augmentation de six pour cent.", lang), [("six", "6", "cardinal")])
                self.assertEqual(read("Il est cent pour cent pour Volange.", lang), [("cent", "100", "cardinal")])
        self.assertEqual(read("Il l'a vendu pour cent euros.", "fr-FR"), [("cent", "100", "cardinal")])

    def test_a_point_marks_decimals_but_three_digits_stay_unread(self):
        self.assertEqual(fr("3.5"), [("3.5", "3.5", "decimal")])
        # fr groups with a space, so "1.500" is 1.5 or 1500: no number
        self.assertEqual(fr("1.500"), [])
        # a day and a month with a period after them are a date
        self.assertEqual(fr("le 24.12."), [])

    def test_neuf_that_no_word_follows_may_be_new(self):
        self.assertEqual(confidence("un manteau neuf", "fr"), [("un", 0.3), ("neuf", 0.4)])
        self.assertEqual(confidence("Quoi de neuf ?", "fr"), [("neuf", 0.4)])
        self.assertEqual(confidence("les neuf Muses", "fr"), [("neuf", 1.0)])
        self.assertEqual(confidence("dix-neuf", "fr"), [("dix-neuf", 1.0)])
        self.assertEqual(confidence("neuf cents", "fr"), [("neuf cents", 1.0)])
        # a hyphenated noun gives no token, but a word follows "neuf" all the same
        self.assertEqual(confidence("mes neuf arrière-petits-enfants", "fr"), [("neuf", 1.0)])

    def test_neuf_as_the_whole_text_is_nine(self):
        # a one-word text with no punctuation is a spoken answer
        for text in ("neuf", "Neuf", " neuf "):
            with self.subTest(text=text):
                self.assertEqual(confidence(text, "fr"), [(text.strip(), 1.0)])
        self.assertEqual(confidence("Neuf.", "fr"), [("Neuf", 0.4)])
        self.assertEqual(confidence("C'est neuf", "fr"), [("neuf", 0.4)])


class TestStandaloneOrdinals(unittest.TestCase):
    def test_premier_and_second_end_no_longer_ordinal(self):
        # 10 and the noun "secondes"; 10 and 1st; 21st and 22nd take
        # "unième" and "deuxième"
        self.assertEqual(fr("dix secondes"), [("dix", "10", C)])
        self.assertEqual(fr("les dix premiers"), [("dix", "10", C), ("premiers", "1", O)])
        self.assertEqual(fr("vingt et unième"), [("vingt et unième", "21", O)])
        self.assertEqual(fr("vingt-deuxième"), [("vingt-deuxième", "22", O)])

    def test_premier_and_second_alone_stay_ordinals(self):
        self.assertEqual(fr("le premier"), [("premier", "1", O)])
        self.assertEqual(confidence("Il est arrivé second.", "fr"), [("second", 0.4)])

    def test_seconde_after_an_article_stays_an_ordinal(self):
        # only a sure cardinal counts the noun: "une" may be the article, so
        # "une seconde fois" keeps its ordinal
        self.assertEqual(read("Essaie une seconde fois.", "fr-FR"),
                         [("une", "1", "cardinal"), ("seconde", "2", O)])


class TestENotation(unittest.TestCase):
    def test_a_number_in_e_notation_holds_no_ordinal(self):
        # "1e5" is 10^5 in E notation: neither the 1st nor 1 and 5
        for text in ("1e5", "1e309", "5e3", "2,5e-3", "1E5 cellules"):
            with self.subTest(text=text):
                self.assertEqual(fr(text), [])
        # the ordinal suffix with no digit after it stays
        self.assertEqual(fr("le 2e jour"), [("2e", "2", O)])
        self.assertEqual(fr("le 1er mai"), [("1er", "1", O)])

    def test_an_ordinal_range_is_no_exponent(self):
        # "2e-3e" is the 2nd to the 3rd: a letter after the digits ends the exponent
        two_three = [("2e", "2", O), ("3e", "3", O)]
        for text, lang in (("le 2e-3e rang", "fr-FR"), ("en 2e-3e année", "fr-BE"), ("de 2e-3e graad", "nl")):
            with self.subTest(text=text):
                self.assertEqual(read(text, lang), two_three)


class TestSwissDigits(unittest.TestCase):
    def test_an_apostrophe_groups_digits_in_switzerland(self):
        # 1 x 10^6 + 234 x 10^3 + 567.5 = 1234567.5
        self.assertEqual(read("1'234'567,5", "fr-CH"), [("1'234'567,5", "1234567.5", "decimal")])
        self.assertEqual(read("1 234 567,5", "fr-CH"), [("1 234 567,5", "1234567.5", "decimal")])
        self.assertEqual(read("1'234", "fr-FR"), [("1", "1", C), ("234", "234", C)])


class TestBillion(unittest.TestCase):
    def test_billion_carries_its_scale(self):
        # long: 10^12; short ("mille millions"): 10^9
        self.assertEqual(read("un billion", "fr"), [("un billion", "1000000000000", C)])
        self.assertEqual(read("un billion", "fr", scale="short"), [("un billion", "1000000000", C)])
        self.assertEqual([m.number_scale.value for m in tag_numbers("un billion", "fr")], ["long"])


class TestMinusAfterAnHour(unittest.TestCase):
    def test_moins_after_an_hour_counts_the_minutes(self):
        # "midi moins dix" is ten to noon: the minutes are 10, no -10
        self.assertEqual(read("Il est midi moins dix.", "fr"), [("dix", "10", C)])
        self.assertEqual(read("minuit moins 10", "fr"), [("10", "10", C)])
        self.assertEqual(read("Il est 9h moins 10.", "fr"), [("9", "9", C), ("10", "10", C)])
        self.assertEqual(read("Il est neuf heures moins dix.", "fr"), [("neuf", "9", C), ("dix", "10", C)])

    def test_a_tout_le_moins_is_no_sign(self):
        self.assertEqual(read("Il faut à tout le moins trois jours.", "fr"), [("trois", "3", C)])

    def test_moins_before_a_number_still_signs(self):
        # 0 - 3 = -3
        self.assertEqual(read("Il fait moins trois degrés.", "fr"), [("moins trois", "-3", C)])


class TestLonePoint(unittest.TestCase):
    def test_a_point_before_the_first_digit_marks_decimals(self):
        # 5/10 = 0.5, and the sign makes it -0.5
        self.assertEqual(read("-.5", "fr"), [("-.5", "-0.5", "decimal")])
        self.assertEqual(read("La taxe est de .5 pour cent.", "fr"), [(".5", "0.5", "decimal")])


if __name__ == "__main__":
    unittest.main()
