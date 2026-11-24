"""Grammar rules of ru, uk, bg, pl, cs, sk, sl and hr. Each expected value is
worked out by hand in the comment beside it; sources are in the lexicon of
each language under numtag/lexicon/."""
import unittest

import pytest
from helpers import read, sure
from numtag import Scale, tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


class TestScales(unittest.TestCase):
    def test_russian_milliard_is_ten_to_the_ninth_in_both_scales(self):
        # 2 x 10^9 under the short and the long scale
        for scale in (Scale.SHORT, Scale.LONG):
            self.assertEqual(read("два миллиарда", "ru", scale=scale), [("два миллиарда", "2000000000", C)])

    def test_polish_uses_the_long_scale(self):
        # bilion = 10^12, miliard = 10^9
        self.assertEqual(read("dwa biliony", "pl"), [("dwa biliony", "2000000000000", C)])
        self.assertEqual(read("trzy miliardy", "pl"), [("trzy miliardy", "3000000000", C)])

    def test_russian_quintillion_is_ten_to_the_eighteenth(self):
        # short scale: 3 x 5 + 3 = 18. 12 x 10^18 + 345 = 12000000000000000000 + 345
        self.assertEqual(read("двенадцать квинтиллионов триста сорок пять", "ru"),
                         [("двенадцать квинтиллионов триста сорок пять", "12000000000000000345", C)])
        # 12 x 10^18 + 5 x 1000 = 12000000000000000000 + 5000
        self.assertEqual(read("двенадцать квинтиллионов пять тысяч", "ru"),
                         [("двенадцать квинтиллионов пять тысяч", "12000000000000005000", C)])

    def test_russian_quintillion_in_every_case(self):
        # each count times 10^18: 1 and 18 zeros, 2 and 18 zeros, 5 and 18 zeros
        one, two, five = "1" + "0" * 18, "2" + "0" * 18, "5" + "0" * 18
        for text, value in (("один квинтиллион", one), ("два квинтиллиона", two), ("одному квинтиллиону", one),
                            ("одним квинтиллионом", one), ("одном квинтиллионе", one), ("пять квинтиллионов", five),
                            ("пяти квинтиллионам", five), ("пятью квинтиллионами", five), ("пяти квинтиллионах", five)):
            with self.subTest(text=text):
                self.assertEqual(read(text, "ru"), [(text, value, C)])

    def test_croatian_trilijun_is_ten_to_the_eighteenth(self):
        # long scale: 6 x 3 = 18. 12 x 10^18 + 345 = 12000000000000000000 + 345
        self.assertEqual(read("dvanaest trilijuna tristo četrdeset pet", "hr"),
                         [("dvanaest trilijuna tristo četrdeset pet", "12000000000000000345", C)])
        self.assertEqual(read("jedan trilijun", "hr"), [("jedan trilijun", "1000000000000000000", C)])

    def test_croatian_genitive_scale_word_alone_is_one_of_it(self):
        # "oko milijuna" and "oko trilijuna" are the genitive singular: 10^6 and 10^18
        self.assertEqual(read("Bilo ih je oko milijuna.", "hr"), [("milijuna", "1000000", C)])
        self.assertEqual(read("Bilo ih je oko trilijuna.", "hr"), [("trilijuna", "1" + "0" * 18, C)])
        self.assertEqual(read("više od milijuna ljudi", "hr"), [("milijuna", "1000000", C)])

    def test_croatian_vague_quantity_before_a_scale_word_is_no_number(self):
        # "nekoliko", "puno", "više" and "mnogo" take the genitive plural, so the scale word is no count of one
        for text in ("nekoliko milijuna ljudi", "nekoliko bilijuna kuna", "nekoliko trilijuna kuna",
                     "nekoliko milijardi eura", "nekoliko tisuća ljudi", "nekoliko stotina", "nekoliko stotina ljudi",
                     "puno tisuća", "više milijuna ljudi", "mnogo milijuna ljudi"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "hr"), [])
        # hr.wikipedia, "Honduras"
        self.assertEqual(read("Nemirno vrijeme nastanka vulkanske visoravni na jugozapadu Hondurasa "
                              "odvijalo se prije nekoliko milijuna godina.", "hr"), [])

    def test_croatian_vague_quantity_changes_only_the_word_after_it(self):
        # 2 x 10^6, 5 x 10^6, 21 x 10^6 and 20 x 10^6 + 3
        self.assertEqual(read("dva milijuna", "hr"), [("dva milijuna", "2000000", C)])
        self.assertEqual(read("pet milijuna ljudi", "hr"), [("pet milijuna", "5000000", C)])
        self.assertEqual(read("dvadeset i jedan milijun", "hr"), [("dvadeset i jedan milijun", "21000000", C)])
        self.assertEqual(read("dvadeset milijuna tri", "hr"), [("dvadeset milijuna tri", "20000003", C)])
        self.assertEqual(read("nekoliko ljudi, dva milijuna", "hr"), [("dva milijuna", "2000000", C)])
        self.assertEqual(read("nekoliko, milijuna", "hr"), [("milijuna", "1000000", C)])
        self.assertEqual(read("malo milijuna", "hr"), [("milijuna", "1000000", C)])
        self.assertEqual(read("nekoliko", "hr"), [])

    def test_croatian_clitic_between_vague_quantity_and_scale_word(self):
        # hr.wikipedia, "Amaterska astronomija": "je" takes the second place and splits "nekoliko tisuća"
        self.assertEqual(read("Najbliža zvijezda nekoliko je tisuća puta dalje od posljednjeg planeta.", "hr"), [])
        self.assertEqual(read("nekoliko je stotina", "hr"), [])

    def test_croatian_vague_quantity_holds_through_a_chain_of_scale_words(self):
        # hr.wikipedia, "Woodstock": "stotina" counts several, so "tisuća" after it has no count either
        self.assertEqual(read("ondje je bilo nekoliko stotina tisuća ljudi, vjerojatno i cijeli milijun", "hr"),
                         [("milijun", "1000000", C)])
        self.assertEqual(read("nekoliko stotina milijuna", "hr"), [])

    def test_croatian_hundred_after_a_vague_scale_word_starts_its_own_number(self):
        # "sto" right after "nekoliko" has no count; after "nekoliko milijuna" it counts the
        # thousands of a lower group: 100 x 1000 = 100000
        self.assertEqual(read("nekoliko sto", "hr"), [])
        # the clitic "je" between the vague word and the hundred keeps the guard
        self.assertEqual(read("Nekoliko je sto", "hr"), [])
        self.assertEqual(read("nekoliko milijuna sto tisuća", "hr"), [("sto tisuća", "100000", C)])

    def test_croatian_hundred_word_with_its_own_count_keeps_it(self):
        # "dvjesto" is two hundred in one word, so the vague word before it takes no count away: 200
        self.assertEqual(read("nekoliko dvjesto ljudi", "hr"), [("dvjesto", "200", C)])

    def test_croatian_vague_quantity_stops_at_punctuation(self):
        # a full stop or a comma ends the phrase, so "Tisuću" and "tisuću" count one thousand
        self.assertEqual(read("Bilo ih je nekoliko stotina. Tisuću ljudi je došlo.", "hr"), [("Tisuću", "1000", C)])
        self.assertEqual(read("nekoliko stotina, tisuću ljudi", "hr"), [("tisuću", "1000", C)])

    def test_croatian_digits_before_a_vague_quantity_do_not_cancel_it(self):
        # a year in digits is a number of its own and says nothing about "nekoliko milijuna"
        self.assertEqual(read("Do 2030 nekoliko milijuna ljudi", "hr"), [("2030", "2030", C)])

    def test_croatian_future_and_conditional_clitics_split_the_phrase(self):
        # hr.wikipedia, "Enklitika": "će" and "bi" are clitics too
        self.assertEqual(read("nekoliko će tisuća ljudi doći", "hr"), [])
        self.assertEqual(read("nekoliko bi tisuća", "hr"), [])

    def test_croatian_clitic_skip_ignores_the_case_of_the_scale_word(self):
        # Known trade-off: after "je" the scale word may stand in the nominative or accusative singular
        # ("Puno je milijun eura", where 1000000 would be right), and it reads no number
        self.assertEqual(read("Puno je milijun eura za taj projekt.", "hr"), [])
        self.assertEqual(read("Mnogo je tisuću kuna.", "hr"), [])
        self.assertEqual(read("Više je milijun nego tisuću.", "hr"), [("tisuću", "1000", C)])

    def test_croatian_vise_after_a_number_is_plus(self):
        # HJP "više", sense 5: "plus (+)". The scale word before "više" is a count, and so is the one after it
        self.assertEqual(read("milijun više milijun su dva milijuna", "hr"),
                         [("milijun", "1000000", C), ("milijun", "1000000", C), ("dva milijuna", "2000000", C)])
        self.assertEqual(read("tisuću više tisuću je dvije tisuće", "hr"),
                         [("tisuću", "1000", C), ("tisuću", "1000", C), ("dvije tisuće", "2000", C)])

    def test_croatian_trilijun_scale_words_with_a_count(self):
        # 2 x 10^18 + 3 and 5 x 10^18
        self.assertEqual(read("dva trilijuna tri", "hr"), [("dva trilijuna tri", "2000000000000000003", C)])
        self.assertEqual(read("pet trilijuna", "hr"), [("pet trilijuna", "5000000000000000000", C)])

    def test_croatian_hundreds_noun_is_the_count_of_a_scale_word(self):
        # Hrvatski pravopis 5.4.1: "pet stotina" writes the hundreds "petsto". 5 x 100 x 1000, 2 x 100 x 1000,
        # 3 x 100 x 10^6, 10^6 + 3 x 100 x 1000 twice, 5 x 100 x 1000 + 5
        for text, value in (("pet stotina tisuća", "500000"), ("dvije stotine tisuća", "200000"),
                            ("tri stotine milijuna", "300000000"), ("milijun tri stotine tisuća", "1300000"),
                            ("jedan milijun i tri stotine tisuća", "1300000"),
                            ("pet stotina tisuća i pet", "500005")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "hr"), [(text, value, C)])
        # hr.wikipedia, "Domovinski rat": 2 x 100 x 1000
        self.assertEqual(read("pobili dvije stotine tisuća civila bez suda", "hr"),
                         [("dvije stotine tisuća", "200000", C)])
        # 5 x 100 + 20: the hundreds noun is the hundreds of a longer cardinal, as "petsto dvadeset" is
        self.assertEqual(read("pet stotina dvadeset", "hr"), [("pet stotina dvadeset", "520", C)])

    def test_croatian_stotinu_is_the_hundred(self):
        # Hrvatski pravopis 5.4.1: "sto ili stotinu". 100 x 1000, 100 x 10^6
        self.assertEqual(read("stotinu tisuća ljudi", "hr"), [("stotinu tisuća", "100000", C)])
        self.assertEqual(read("stotinu milijuna", "hr"), [("stotinu milijuna", "100000000", C)])

    def test_croatian_digits_count_the_hundreds_noun(self):
        # digits count "stotina" as a word count does: 5 x 100, 2 x 100, 10 x 100, 5 x 100 x 1000,
        # 2 x 100 x 1000, 3 x 100 x 10^6, 10^6 + 3 x 100 x 1000
        for text, value in (("5 stotina", "500"), ("2 stotine", "200"), ("10 stotina", "1000"),
                            ("5 stotina tisuća", "500000"), ("2 stotine tisuća", "200000"),
                            ("3 stotine milijuna", "300000000"), ("milijun 3 stotine tisuća", "1300000")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "hr"), [(text, value, C)])
        self.assertEqual(read("Prodano je 5 stotina tisuća primjeraka.", "hr"), [("5 stotina tisuća", "500000", C)])
        # 2.5 x 100 = 250
        self.assertEqual(read("2,5 stotina", "hr"), [("2,5 stotina", "250", C)])

    def test_croatian_word_decimals_count_the_hundreds_noun(self):
        # a decimal in words counts "stotina" as "one point five hundred" counts "hundred":
        # 2.5 x 100, 0.5 x 100, 2.25 x 100, 2.5 x 100 x 1000
        for text, value in (("dva zarez pet stotina", "250"), ("nula zarez pet stotina", "50"),
                            ("dva zarez dvadeset pet stotina", "225"), ("dva zarez pet stotine tisuća", "250000")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "hr"), [(text, value, C)])
        # 3.5 x 100
        self.assertEqual(read("tri zarez pet stotina ljudi", "hr"), [("tri zarez pet stotina", "350", C)])

    def test_slovak_triliarda_and_kvadrilion_in_the_long_scale(self):
        # triliarda = 10^3 x 10^18 = 10^21: 5 x 10^21 and 2 x 10^21
        self.assertEqual(read("päť triliárd", "sk"), [("päť triliárd", "5000000000000000000000", C)])
        self.assertEqual(read("dve triliardy", "sk"), [("dve triliardy", "2000000000000000000000", C)])
        # kvadrilión = 10^(6 x 4) = 10^24: 12 x 10^24
        self.assertEqual(read("dvanásť kvadriliónov", "sk"), [("dvanásť kvadriliónov", "12000000000000000000000000", C)])
        # 1 x 10^21 and the cases of 1 x 10^24, 2 x 10^24
        one_kvadrilion = "1" + "0" * 24
        for text, value in (("jedna triliarda", "1" + "0" * 21), ("jeden kvadrilión", one_kvadrilion),
                            ("dva kvadrilióny", "2" + "0" * 24), ("jedným kvadriliónom", one_kvadrilion),
                            ("jedného kvadrilióna", one_kvadrilion)):
            with self.subTest(text=text):
                self.assertEqual(read(text, "sk"), [(text, value, C)])

    def test_a_plural_scale_noun_alone_is_no_number(self):
        self.assertEqual(read("тысячи людей", "ru"), [])
        self.assertEqual(read("tisuće ljudi", "hr"), [])

    def test_a_singular_scale_noun_alone_is_one_of_it(self):
        self.assertEqual(read("тысячу рублей", "ru"), [("тысячу", "1000", C)])
        self.assertEqual(read("tisuća", "hr"), [("tisuća", "1000", C)])

    def test_the_scale_noun_agrees_with_the_last_word_of_its_count(self):
        # (20 + 1) x 10^6: the singular "миллион" after a count that ends in one
        self.assertEqual(read("двадцать один миллион", "ru"), [("двадцать один миллион", "21000000", C)])
        self.assertEqual(read("dvadeset i jedan milijun", "hr"), [("dvadeset i jedan milijun", "21000000", C)])

    def test_slovene_dual_and_plural_of_the_scale_noun(self):
        # 2 x 10^6, 3 x 10^6, 5 x 10^6
        self.assertEqual(read("dva milijona", "sl"), [("dva milijona", "2000000", C)])
        self.assertEqual(read("tri milijone", "sl"), [("tri milijone", "3000000", C)])
        self.assertEqual(read("pet milijonov", "sl"), [("pet milijonov", "5000000", C)])


    def test_a_hundred_word_after_the_thousands_is_no_multiplier_of_them(self):
        # 8 x 10^6 + 2 x 1000 + 100: "sta" is the genitive of 100 and the
        # multiplier in "tři sta" (300)
        self.assertEqual(read("osmi miliónů dvou tisíc sta", "cs"), [("osmi miliónů dvou tisíc sta", "8002100", C)])
        self.assertEqual(read("tři sta", "cs"), [("tři sta", "300", C)])


class TestCases(unittest.TestCase):
    def test_oblique_cases_read(self):
        # 2 x 1000; 300; 2
        self.assertEqual(read("около двух тысяч человек", "ru"), [("двух тысяч", "2000", C)])
        self.assertEqual(read("о трёхстах страницах", "ru"), [("трёхстах", "300", C)])
        self.assertEqual(read("с двумя друзьями", "ru"), [("двумя", "2", C)])
        self.assertEqual(read("одною", "ru"), [("одною", "1", C)])

    def test_bulgarian_definite_forms(self):
        self.assertEqual(read("двата брата", "bg"), [("двата", "2", C)])
        self.assertEqual(read("третият път", "bg"), [("третият", "3", O)])

    def test_alternative_forms(self):
        # 40 + 5; 200; (600 + 70 + 8) x 1000
        self.assertEqual(read("четирийсет и пет", "bg"), [("четирийсет и пет", "45", C)])
        self.assertEqual(read("dvjesta", "hr"), [("dvjesta", "200", C)])
        self.assertEqual(read("šesto sedamdeset osam tisuća", "hr"), [("šesto sedamdeset osam tisuća", "678000", C)])
        # "šesto" alone is the neuter ordinal 6th
        self.assertEqual(read("šesto dijete", "hr"), [("šesto", "6", O)])


class TestCompoundWords(unittest.TestCase):
    def test_a_word_made_of_number_words_reads_as_its_parts(self):
        # 2 x 1000, ordinal
        self.assertEqual(read("двухтысячный год", "ru"), [("двухтысячный", "2000", O)])
        # 7 x 10^6 + 150 x 1000
        self.assertEqual(read("sedemmilijonovsto petdesettisoči", "sl"),
                         [("sedemmilijonovsto petdesettisoči", "7150000", O)])

    def test_a_word_in_the_lexicon_is_never_split(self):
        # "desetin" is a fraction noun, not "deset" + "in"
        self.assertNotIn(("deset", "10", C), read("desetin", "sl"))

    def test_slovene_inverted_tens(self):
        # 1 + 20; 5 + 20
        self.assertEqual(read("enaindvajset", "sl"), [("enaindvajset", "21", C)])
        self.assertEqual(read("petindvajset let", "sl"), [("petindvajset", "25", C)])

    def test_czech_inverted_tens_inside_one_word_only(self):
        # 1 + 20 in one word; "jedna a dvacet" is two numbers
        self.assertEqual(read("jedenadvacet", "cs"), [("jedenadvacet", "21", C)])
        self.assertEqual(read("jedna a dvacet", "cs"), [("jedna", "1", C), ("dvacet", "20", C)])

    def test_slovak_tens_and_units_in_one_word(self):
        # 20 + 1
        self.assertEqual(read("dvadsaťjeden", "sk"), [("dvadsaťjeden", "21", C)])


class TestOrdinals(unittest.TestCase):
    def test_only_the_last_word_is_ordinal_in_russian(self):
        # 2000 + 23
        self.assertEqual(read("две тысячи двадцать третий", "ru"), [("две тысячи двадцать третий", "2023", O)])

    def test_every_word_after_the_cardinal_prefix_is_ordinal_in_polish(self):
        # 20 + 1; 2000 + 20 + 3
        self.assertEqual(read("dwudziesty pierwszy", "pl"), [("dwudziesty pierwszy", "21", O)])
        self.assertEqual(read("dwa tysiące dwudziesty trzeci", "pl"), [("dwa tysiące dwudziesty trzeci", "2023", O)])
        self.assertEqual(read("dvacátý první", "cs"), [("dvacátý první", "21", O)])

    def test_an_ordinal_scale_word_counts_only_the_groups_below_it(self):
        # 2 x 10^6 + 300 x 10^3, not (2 x 10^6 + 300) x 10^3
        self.assertEqual(read("два миллиона трехсоттысячный", "ru"), [("два миллиона трехсоттысячный", "2300000", O)])
        self.assertEqual(read("tri milijuna dvjestotisućiti", "hr"), [("tri milijuna dvjestotisućiti", "3200000", O)])
        self.assertEqual(read("two million three hundred thousandth", "en"),
                         [("two million three hundred thousandth", "2300000", O)])

    def test_a_digit_ordinal_takes_a_hyphen_before_its_suffix(self):
        self.assertEqual(read("2-й", "ru"), [("2-й", "2", O)])
        self.assertEqual(read("5-ий", "uk"), [("5-ий", "5", O)])
        self.assertEqual(read("4-ма", "bg"), [("4", "4", C)])

    def test_a_uk_digit_ordinal_takes_the_final_part_of_its_case_form(self):
        # Український правопис (2019), § 106, п. 2
        self.assertEqual(read("5-й поверх", "uk"), [("5-й", "5", O)])
        self.assertEqual(read("на 36-му кілометрі", "uk"), [("36-му", "36", O)])
        self.assertEqual(read("після 7-ї години", "uk"), [("7-ї", "7", O)])
        # пʼятого, пʼятих
        self.assertEqual(read("з 2014-го року", "uk"), [("2014-го", "2014", O)])
        self.assertEqual(read("у 1990-х роках", "uk"), [("1990-х", "1990", O)])


class TestFractionsAndDecimals(unittest.TestCase):
    def test_one_and_a_half_is_one_word(self):
        # 3/2; 3/2 x 10^6
        self.assertEqual(read("полтора", "ru"), [("полтора", "1.5", F)])
        self.assertEqual(read("полтора миллиона", "ru"), [("полтора миллиона", "1500000", C)])
        self.assertEqual(read("półtora", "pl"), [("półtora", "1.5", F)])

    def test_a_bound_half_stands_only_before_the_rest_of_the_number(self):
        # 1/2 x 10^6; "пол" alone is "floor"
        self.assertEqual(read("полмиллиона", "ru"), [("полмиллиона", "500000", C)])
        self.assertEqual(read("пол", "ru"), [])

    def test_a_half_noun_alone_is_a_half(self):
        # 1/2; 1/2 x 10^6
        self.assertEqual(read("połowa", "pl"), [("połowa", "0.5", F)])
        self.assertEqual(read("połowę miliona", "pl"), [("połowę miliona", "500000", C)])

    def test_a_fraction_noun_alone_counts_one(self):
        # 1/3; 1 x 100
        self.assertEqual(read("trećina glasova", "hr"), [("trećina", "1/3", F)])
        self.assertEqual(read("stotinu ljudi", "hr"), [("stotinu", "100", C)])

    def test_decimals_as_a_fraction_of_a_power_of_ten(self):
        # 2 + 5/10; 3 + 14/100
        self.assertEqual(read("dvě celé pět desetin", "cs"), [("dvě celé pět desetin", "2.5", D)])
        self.assertEqual(read("три целых четырнадцать сотых", "ru"), [("три целых четырнадцать сотых", "3.14", D)])

    def test_digits_before_a_power_of_ten_are_its_numerator(self):
        # 2 + 5/100 = 2.05; 2 + 25/100; 3 + 7/10; never 2.5 and a stray ordinal 100
        self.assertEqual(read("2 целых 5 сотых", "ru"), [("2 целых 5 сотых", "2.05", D)])
        self.assertEqual(read("две целых 5 сотых", "ru"), [("две целых 5 сотых", "2.05", D)])
        self.assertEqual(read("2 целых 25 сотых", "ru"), [("2 целых 25 сотых", "2.25", D)])
        self.assertEqual(read("3 целых 7 десятых процента", "ru"), [("3 целых 7 десятых", "3.7", D)])
        self.assertEqual(read("2 цілих 5 сотих", "uk"), [("2 цілих 5 сотих", "2.05", D)])
        self.assertEqual(read("2 celé 5 setin", "cs"), [("2 celé 5 setin", "2.05", D)])
        # sl and hr part words: 2 + 5/100; SSKJ "ena cela, pet stotink 1,05"
        self.assertEqual(read("2 celi 5 stotink", "sl"), [("2 celi 5 stotink", "2.05", D)])
        self.assertEqual(read("dve celi pet stotink", "sl"), [("dve celi pet stotink", "2.05", D)])
        self.assertEqual(read("2 cijela 5 stotinki", "hr"), [("2 cijela 5 stotinki", "2.05", D)])
        self.assertEqual(read("dva cijela pet stotinki", "hr"), [("dva cijela pet stotinki", "2.05", D)])
        # 2 + 5/10 in Slovak digits
        self.assertEqual(read("2 celé 5", "sk"), [("2 celé 5", "2.5", D)])

    def test_digits_before_another_part_word_are_no_decimals(self):
        # 2 3/5 is no 2.3: the digits are no decimals
        for text, lang in (("2 целых 3 пятых", "ru"), ("2 целых 1 треть", "ru"), ("2 целых 3 четверти", "ru"),
                           ("2 цілих 3 п'ятих", "uk"), ("2 celé 3 pětiny", "cs")):
            with self.subTest(text=text):
                self.assertNotIn(D, [kind for _, _, kind in read(text, lang)])

    def test_a_joiner_after_the_decimal_marker(self):
        # 2 + 0.5
        self.assertEqual(read("две цяло и пет", "bg"), [("две цяло и пет", "2.5", D)])


class TestCompoundEdges(unittest.TestCase):
    def test_a_joiner_never_starts_or_ends_a_split_word(self):
        # "isto" is "the same", not i|sto; "ijedan" is "any", not i|jedan
        for word in ("isto", "ijedan", "ijednog"):
            self.assertEqual(read(word, "hr"), [])
        # whole words from the declension tables, never štyri|a or tisíc|a
        self.assertEqual(read("štyria", "sk"), [("štyria", "4", C)])
        self.assertEqual(read("tisíca", "sk"), [("tisíca", "1000", C)])
        self.assertEqual(read("třema", "cs"), [("třema", "3", C)])

    def test_a_joiner_inside_a_split_word_still_joins(self):
        # 4 + 50; 1 + 20
        self.assertEqual(read("čtyřiapadesát", "cs"), [("čtyřiapadesát", "54", C)])
        self.assertEqual(read("enaindvajset", "sl"), [("enaindvajset", "21", C)])

    def test_number_words_inside_a_longer_word_are_no_mention(self):
        # "Trojedne" (triune) splits into tro|jedne, but no number covers the
        # whole word, so no part of it reads
        self.assertEqual(read("bana Trojedne Kraljevine", "hr"), [])
        self.assertEqual(read("Půldruhého století", "cs"), [])


class TestHomographs(unittest.TestCase):
    def test_one_after_a_negative_particle_counts_nothing(self):
        # ru "ни одного", pl "ani jednego": not a single, no count of one
        self.assertEqual(read("я не пропустил ни одного таймера", "ru"), [])
        self.assertEqual(read("ни один будильник", "ru"), [])
        self.assertEqual(read("Nie było ani jednego ciasteczka.", "pl"), [])
        self.assertEqual(read("ani jedna", "pl"), [])
        # the number after it still counts, and so does one with no particle
        self.assertEqual(read("ни один из ста", "ru"), [("ста", "100", "cardinal")])
        self.assertEqual(read("ни двух", "ru"), [("двух", "2", "cardinal")])
        self.assertEqual(read("один будильник", "ru"), [("один", "1", "cardinal")])

    def test_one_and_the_same_counts_nothing(self):
        # "один и тот же" is "the same", in every gender, number and case
        self.assertEqual(read("Всегда одно и то же.", "ru"), [])
        self.assertEqual(read("Мы учились в одном и том же классе.", "ru"), [])
        self.assertEqual(read("Она поёт одну и ту же песню.", "ru"), [])
        self.assertEqual(read("одни и те же люди", "ru"), [])
        # uk "один і той самий", pl "jeden i ten sam", cs "jeden a tentýž"
        self.assertEqual(read("всю зиму йому снився один і той же сон", "uk"), [])
        self.assertEqual(read("за одне й те саме", "uk"), [])
        self.assertEqual(read("Однієї й тієї самої ночі.", "uk"), [])
        self.assertEqual(read("był to często jeden i ten sam człowiek", "pl"), [])
        self.assertEqual(read("To jedno i to samo.", "pl"), [])
        self.assertEqual(read("Jsou to stále jedni a titíž!", "cs"), [])
        self.assertEqual(read("Položila mi jednu a tutéž otázku.", "cs"), [])
        # one and another number still count
        self.assertEqual(read("один и два", "ru"), [("один", "1", "cardinal"), ("два", "2", "cardinal")])

    def confidences(self, text: str, lang: str) -> list[tuple[str, str, float]]:
        return [(m.text, m.value, m.confidence) for m in tag_numbers(text, lang)]

    def test_a_number_word_that_is_also_a_common_word_reads_with_low_confidence(self):
        for text, lang, value in (("семью", "ru", "7"), ("сорока", "ru", "40"), ("nič", "sl", "0"),
                                  ("друга", "uk", "2"), ("četvrti", "hr", "4"), ("druga", "sl", "2"),
                                  ("drugi", "hr", "2"), ("druhý", "cs", "2"), ("druhý", "sk", "2"),
                                  ("drugi", "pl", "2"), ("žádná", "cs", "0"), ("stotina", "hr", "100"),
                                  ("stotinu", "hr", "100"), ("jednou", "cs", "1")):
            with self.subTest(text=text, lang=lang):
                (word, read_value, confidence), = self.confidences(text, lang)
                self.assertEqual((word, read_value), (text, value))
                self.assertLess(confidence, 1.0)

    def test_the_plain_number_word_keeps_full_confidence(self):
        for text, lang in (("семь", "ru"), ("сорок", "ru"), ("dva", "cs"), ("dvije stotine", "hr")):
            with self.subTest(text=text, lang=lang):
                self.assertEqual([c for *_, c in self.confidences(text, lang)], [1.0])

    def test_a_homograph_inside_a_longer_number_is_no_homograph(self):
        # 0 + 5/10
        self.assertEqual(self.confidences("nič cela pet", "sl"), [("nič cela pet", "0.5", 1.0)])
        self.assertEqual(self.confidences("žádná celá pět", "cs"), [("žádná celá pět", "0.5", 1.0)])


class TestPersonalAndCountForms(unittest.TestCase):
    def test_slovak_masculine_personal_forms(self):
        # 2, 3, 4; 120 + 4
        self.assertEqual(read("dvaja pocestní", "sk"), [("dvaja", "2", C)])
        self.assertEqual(read("traja muži", "sk"), [("traja", "3", C)])
        self.assertEqual(read("stodvadsiati štyria muži", "sk"), [("stodvadsiati štyria", "124", C)])

    def test_czech_one_hundred_counted_by_jedno(self):
        # 2 x 1000 + 1 x 100 + 60 + 8
        self.assertEqual(read("dva tisíce jedno sto šedesát osm", "cs"), [("dva tisíce jedno sto šedesát osm", "2168", C)])

    def test_russian_whole_part_and_a_fraction(self):
        # 3 + 6/7 = 27/7; 2 + 5/10
        self.assertEqual(read("три целых и шесть седьмых", "ru"), [("три целых и шесть седьмых", "27/7", F)])
        self.assertEqual(read("две целых и пять десятых", "ru"), [("две целых и пять десятых", "2.5", D)])


class TestDigitGroups(unittest.TestCase):
    def test_a_space_groups_digits_where_the_group_mark_is_a_space(self):
        # 10^6
        for lang in ("ru", "uk", "bg", "pl", "cs", "sk"):
            with self.subTest(lang=lang):
                self.assertEqual(read("1 000 000", lang), [("1 000 000", "1000000", C)])

    def test_a_dot_groups_digits_only_where_a_source_says_so(self):
        # CLDR sl and hr; IJP for Czech money amounts; no dot in ru, uk, bg, pl, sk
        for lang in ("sl", "hr", "cs"):
            with self.subTest(lang=lang):
                self.assertEqual(read("1.000.000", lang), [("1.000.000", "1000000", C)])
        for lang in ("ru", "uk", "bg", "pl", "sk"):
            with self.subTest(lang=lang):
                self.assertNotIn("1000000", [value for _, value, _ in read("1.000.000", lang)])

class TestDigitCountOfAHundredNoun(unittest.TestCase):
    def test_a_zero_count_multiplies_no_hundred_noun(self):
        # 0 x 100 is no count of hundreds: the noun stands alone, a weak hundred (as "0 tisuća" leaves "tisuća")
        self.assertEqual(sure("0 stotina", "hr"), [("stotina", "100", 0.4)])
        self.assertEqual(read("0 stotine", "hr"), [])

    def test_digits_count_hundreds_below_a_thousand(self):
        # 5 x 100 = 500, and 3 x 100 = 300
        self.assertEqual(read("5 stotina", "hr"), [("5 stotina", "500", C)])
        self.assertEqual(read("3 stotine", "hr"), [("3 stotine", "300", C)])

    def test_digits_after_a_scale_word_do_not_multiply_into_the_scale_group(self):
        # 2 x 1000 = 2000 and 5 x 100 = 500: the hundreds after the thousands are a new number, not 2005 x 100
        self.assertEqual(read("2 tisuće 5 stotina", "hr"), [("2 tisuće", "2000", C), ("5 stotina", "500", C)])


class TestCzechMinus(unittest.TestCase):
    def test_minus_with_a_long_i_is_a_sign(self):
        # IJP "minus": "lze i: mínus"; -10 and -7
        self.assertEqual(read("teplota mínus deset stupňů", "cs"), [("mínus deset", "-10", C)])
        self.assertEqual(read("mínus sedm", "cs"), [("mínus sedm", "-7", C)])

    def test_minus_after_a_number_is_no_sign(self):
        # "pět mínus dva" is 5 and 2, as "pět minus dva" is
        self.assertEqual(read("pět mínus dva", "cs"), [("pět", "5", C), ("dva", "2", C)])


class TestHundredNounWithAHalfAndAYear(unittest.TestCase):
    def test_a_half_after_the_count_counts_half_a_hundred_too(self):
        # 5.5 x 100 = 550, 2.5 x 100 = 250, 3.5 x 100 x 1000 = 350000, and 5.5 x 1000 = 5500
        self.assertEqual(read("pet i pol stotina", "hr"), [("pet i pol stotina", "550", C)])
        self.assertEqual(read("dvije i pol stotine", "hr"), [("dvije i pol stotine", "250", C)])
        self.assertEqual(read("tri i pol stotine tisuća", "hr"), [("tri i pol stotine tisuća", "350000", C)])
        self.assertEqual(read("pet i pol tisuća", "hr"), [("pet i pol tisuća", "5500", C)])

    def test_a_year_is_no_count_of_a_hundred_noun(self):
        # a count of a thousand or more takes no hundred noun: the year stays 1995, not 1995 x 100
        self.assertEqual(read("Godine 1995 stotine ljudi", "hr"), [("1995", "1995", C)])


class TestApostrophes(unittest.TestCase):
    def test_ukrainian_apostrophe_spellings_are_one_letter(self):
        for word in ("пʼять", "п'ять", "п’ять"):
            self.assertEqual(read(word, "uk"), [(word, "5", C)])


class TestSlovene(unittest.TestCase):
    def test_the_clock_hour_enih_is_one(self):
        # SSKJ2 "en": "ob eni(h) (popoldne) 13 h"; "dveh" names 2 the same way
        self.assertEqual(read("ob enih", "sl"), [("enih", "1", C)])
        self.assertEqual(read("ob dveh", "sl"), [("dveh", "2", C)])

    def test_tisoce_alone_is_weak_and_after_a_count_is_sure(self):
        # "tisoče" is the plural noun of "tisoč" ("na tisoče turistov", SSKJ2 "tisoč 1") and the ordinal
        # of the neuter ("dvatisoče leto" is the 2000th year): the ordinal is sure only after a count
        (alone,) = tag_numbers("na tisoče turistov", "sl")
        self.assertEqual((alone.text, alone.value, alone.kind.value), ("tisoče", "1000", O))
        self.assertLess(alone.confidence, 0.5)
        (counted,) = tag_numbers("dvatisoče leto", "sl")
        self.assertEqual((counted.text, counted.value, counted.kind.value), ("dvatisoče", "2000", O))
        self.assertGreaterEqual(counted.confidence, 0.5)


@pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/97")
@pytest.mark.parametrize("text, expected", [
    ('две целых три пятых', [('две целых три пятых', '2.6', F)]),
    ('две целых одна треть', [('две целых одна треть', '7/3', F)]),
])
def test_ru_a_count_before_a_part_word_after_tselykh_adds_the_whole_part(text, expected):
    # 2 + 3/5 = 13/5 = 2.6; 2 + 1/3 = 7/3
    assert read(text, "ru") == expected


@pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/161")
@pytest.mark.parametrize("text, expected", [
    ('dvanáct trilionů tři sta čtyřicet pět', [('dvanáct trilionů tři sta čtyřicet pět', '12000000000000000345', C)]),
    ('jeden trilion jedna', [('jeden trilion jedna', '1000000000000000001', C)]),
])
def test_cs_a_scale_word_above_million_scales_the_count(text, expected):
    # cs long scale: trilion is 10^18; 12 x 10^18 + 345 = 12000000000000000345; 10^18 + 1 = 1000000000000000001
    assert read(text, "cs") == expected


@pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/162")
@pytest.mark.parametrize("text, expected", [
    ('pięćdziesiąty', [('pięćdziesiąty', '50', O)]),
    ('sześćdziesiątego', [('sześćdziesiątego', '60', O)]),
    ('dziewięćdziesiąty', [('dziewięćdziesiąty', '90', O)]),
    ('rok tysiąc dziewięćset dziewięćdziesiąty pierwszy', [('tysiąc dziewięćset dziewięćdziesiąty pierwszy', '1991', O)]),
    ('tysiąc dziewięćset dziewięćdziesiątym', [('tysiąc dziewięćset dziewięćdziesiątym', '1990', O)]),
])
def test_pl_the_ordinals_of_50_60_and_90(text, expected):
    # 900 + 90 + 1000 + 1 = 1991; 1000 + 900 + 90 = 1990
    assert read(text, "pl") == expected



if __name__ == "__main__":
    unittest.main()


class TestCaseAgreement(unittest.TestCase):
    """Every word of a Russian cardinal declines: CLDR RBNF ru writes 29 as
    "двадцать девять" in %spellout-cardinal-masculine and as "двадцати
    девяти" in %spellout-cardinal-masculine-genitive."""

    def test_an_oblique_ten_takes_a_unit_in_its_own_case(self):
        self.assertEqual(read("двадцати девяти", "ru"), [("двадцати девяти", "29", C)])
        self.assertEqual(read("с двадцатью девятью", "ru"), [("двадцатью девятью", "29", C)])
        self.assertEqual(read("о сорока двух", "ru"), [("сорока двух", "42", C)])

    def test_an_oblique_ten_and_a_nominative_unit_are_two_numbers(self):
        # the clock "без двадцати девять" is twenty minutes to nine
        self.assertEqual(read("без двадцати девять", "ru"), [("двадцати", "20", C), ("девять", "9", C)])
        self.assertEqual(read("без двадцати пяти девять", "ru"),
                         [("двадцати пяти", "25", C), ("девять", "9", C)])
        self.assertEqual(read("без двадцати одиннадцать", "ru"),
                         [("двадцати", "20", C), ("одиннадцать", "11", C)])

    def test_a_nominative_ten_takes_any_unit(self):
        self.assertEqual(read("двадцать девять", "ru"), [("двадцать девять", "29", C)])
        # the animate accusative: "увидел двадцать одного студента"
        self.assertEqual(read("двадцать одного", "ru"), [("двадцать одного", "21", C)])


class TestCroatianDigitDecimalTakesAMultiplier(unittest.TestCase):
    def test_a_digit_decimal_takes_stotina_as_the_word_decimal_does(self):
        # 2.5 x 100 = 250, as "dva zarez pet stotina" is
        self.assertEqual(read("dva zarez pet stotina", "hr"), [("dva zarez pet stotina", "250", C)])
        self.assertEqual(read("2 zarez 5 stotina", "hr"), [("2 zarez 5 stotina", "250", C)])


class TestDigitsBeforeAnOrdinalFormPart(unittest.TestCase):
    def test_digits_before_a_plural_ordinal_form_count_things(self):
        # Rosenthal § 45.3 writes a fraction in digits as "2/5": "3 пятых класса"
        # is 3 classes of the 5th grade, so the count 3 and the ordinal 5
        for text, lang, digits, word in (("В школе 3 пятых класса.", "ru", "3", "пятых"),
                                         ("У школі 3 п'ятих класи.", "uk", "3", "п'ятих"),
                                         ("W szkole 3 piąte klasy.", "pl", "3", "piąte"),
                                         ("3 пятые", "ru", "3", "пятые"),
                                         ("3 piątych", "pl", "3", "piątych")):
            with self.subTest(text=text):
                self.assertEqual(read(text, lang), [(digits, "3", C), (word, "5", O)])

    def test_words_before_the_same_part_word_keep_the_fraction(self):
        # 3/5 = 0.6 and 2/3, Rosenthal § 45.3 "две пятых (2/5)"
        self.assertEqual(read("три пятых", "ru"), [("три пятых", "0.6", F)])
        self.assertEqual(read("три п'ятих", "uk"), [("три п'ятих", "0.6", F)])
        self.assertEqual(read("dwie trzecie", "pl"), [("dwie trzecie", "2/3", F)])

    def test_digits_before_a_part_noun_keep_the_fraction(self):
        # "четверть" is a noun, no ordinal form: 3/4 = 0.75; a slash fraction is 3/5 = 0.6
        self.assertEqual(read("3 четверти", "ru"), [("3 четверти", "0.75", F)])
        self.assertEqual(read("3/5", "ru"), [("3/5", "0.6", F)])
        # the ruling names the plural forms only: a singular part word keeps 1/5 = 0.2
        self.assertEqual(read("1 пятая", "ru"), [("1 пятая", "0.2", F)])

    def test_a_language_with_no_ruling_keeps_the_digit_fraction(self):
        # bg is left out of the ruling: 3/5 = 0.6
        self.assertEqual(read("3 пети", "bg"), [("3 пети", "0.6", F)])


class TestOneBeforeAnAmbiguousCollective(unittest.TestCase):
    def test_one_before_stotina_is_a_homograph(self):
        # Hrvatski pravopis 5.4.2 "jedna stotina (1/100)", HJP "stȍtina" 100 and "stotìna" 1/100:
        # the count 1 x 100 = 100 at the score of a homograph
        for text, words in (("Na skupu je bila jedna stotina ljudi.", "jedna stotina"),
                            ("Platio je jednu stotinu kuna.", "jednu stotinu")):
            with self.subTest(text=text):
                self.assertEqual(sure(text, "hr"), [(words, "100", 0.4)])
                self.assertEqual([sorted(r.value for r in m.reasons) for m in tag_numbers(text, "hr")], [["homograph"]])

    def test_a_count_above_one_keeps_the_sure_reading(self):
        # 2 x 100 = 200, 5 x 100 = 500, 1000 + 100 = 1100
        self.assertEqual(sure("dvije stotine", "hr"), [("dvije stotine", "200", 1.0)])
        self.assertEqual(sure("pet stotina", "hr"), [("pet stotina", "500", 1.0)])
        self.assertEqual(sure("tisuću i jedna stotina", "hr"), [("tisuću i jedna stotina", "1100", 1.0)])

    def test_one_before_score_reads_as_an_article_before_it(self):
        # "score" is also a mark: 1 x 20 = 20 at the score of a homograph, as "A score"; 3 x 20 + 10 = 70 is sure
        self.assertEqual(sure("One score of people came.", "en"), [("One score", "20", 0.4)])
        self.assertEqual(sure("Three score and ten years.", "en"), [("Three score and ten", "70", 1.0)])
