"""Germanic grammar rules: compound words, the unit before the ten, Danish
tens by twenties, the two Norwegian counting orders, ordinals in digits and
"and a half" words. Each expected value is worked out by hand in the comment
beside it; sources are in numtag/lexicon/<lang>.json."""
import unittest

from helpers import read
from numtag import Scale, tag_numbers
from numtag.lexicon import load
from numtag.tokenize import tokenize

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


class TestCompoundWords(unittest.TestCase):
    def test_a_number_written_as_one_word_reads_whole(self):
        # 2 x 1000 + 5 x 100 = 2500; 200 + 20 + 3 = 223
        self.assertEqual(read("zweitausendfünfhundert Euro", "de"), [("zweitausendfünfhundert", "2500", C)])
        self.assertEqual(read("zweihundertdreiundzwanzig Gäste", "de"), [("zweihundertdreiundzwanzig", "223", C)])
        self.assertEqual(read("tweeduizendvijfhonderd", "nl"), [("tweeduizendvijfhonderd", "2500", C)])
        self.assertEqual(read("etthundratjugoett", "sv"), [("etthundratjugoett", "121", C)])
        # the splitter is off where the language does not ask for it
        self.assertEqual(read("twentyone", "en"), [])

    def test_the_fewest_parts_win(self):
        # "achttienhonderd" is 18 x 100, not 8, 10 and 100
        self.assertEqual(read("achttienhonderd", "nl"), [("achttienhonderd", "1800", C)])

    def test_a_word_with_a_part_that_is_no_number_word_stays_one_word(self):
        self.assertEqual(read("Das Dreizimmerapartment ist hell.", "de"), [])
        self.assertEqual(read("Femrumslägenheten är ljus.", "sv"), [])

    def test_a_number_never_starts_or_ends_inside_a_word(self):
        # "enen" splits into "en" and "en", which read no one number
        self.assertEqual(read("enen", "sv"), [])
        self.assertEqual(read("zwanzigeins", "de"), [])

    def test_a_joiner_is_never_the_first_or_last_part(self):
        lexicon = load("nl")
        words = [t.text for t in tokenize("vieren", compound_words=lexicon.number_words,
                                          compound_inner=lexicon.joiners)]
        self.assertEqual(words, ["vieren"])

    def test_offsets_hold_with_a_letter_whose_case_fold_is_longer(self):
        # "ß" folds to "ss"; 3 + 30 = 33
        text = "dreiunddreißig Tage"
        self.assertEqual(read(text, "de"), [("dreiunddreißig", "33", C)])


class TestUnitBeforeTen(unittest.TestCase):
    def test_the_unit_and_the_joiner_go_before_the_ten(self):
        # 1 + 20 = 21; 5 + 50 = 55
        self.assertEqual(read("einundzwanzig", "de"), [("einundzwanzig", "21", C)])
        self.assertEqual(read("vijfenvijftig", "nl"), [("vijfenvijftig", "55", C)])
        self.assertEqual(read("tweeëntwintig", "nl"), [("tweeëntwintig", "22", C)])
        self.assertEqual(read("ienentweintich", "fy"), [("ienentweintich", "21", C)])

    def test_a_ten_takes_no_unit_after_it_where_the_unit_goes_first(self):
        self.assertEqual(read("zwanzig eins", "de"), [("zwanzig", "20", C), ("eins", "1", C)])

    def test_spaced_words_are_two_numbers_where_the_unit_and_ten_are_one_word(self):
        # Duden D 65, Team Taaladvies, Dansk Sprognaevn: 2 and 40, not 42
        self.assertEqual(read("zwischen zwei und vierzig Grad", "de"), [("zwei", "2", C), ("vierzig", "40", C)])
        self.assertEqual(read("Kapitel eins und zwanzig", "de"), [("eins", "1", C), ("zwanzig", "20", C)])
        self.assertEqual(read("tussen twee en veertig graden", "nl"), [("twee", "2", C), ("veertig", "40", C)])
        self.assertEqual(read("mellem to og fyrre grader", "da"), [("to", "2", C), ("fyrre", "40", C)])
        # the old Norwegian order is written as separate words: 3 + 20 = 23
        self.assertEqual(read("tre og tjue", "nb"), [("tre og tjue", "23", C)])

    def test_a_joiner_between_two_units_joins_nothing(self):
        self.assertEqual(read("sieben und neun", "de"), [("sieben", "7", C), ("neun", "9", C)])

    def test_the_unit_before_an_ordinal_ten(self):
        # 2 + 50 = 52nd; 100 + 1 + 20 = 121st
        self.assertEqual(read("zweiundfünfzigste", "de"), [("zweiundfünfzigste", "52", O)])
        self.assertEqual(read("hunderteinundzwanzigste", "de"), [("hunderteinundzwanzigste", "121", O)])

    def test_a_scale_ordinal_counts_only_the_last_group(self):
        # 6000 + 9 x 100 = 6900th; 162000 + 8 x 100 = 162800th
        self.assertEqual(read("sechstausendneunhundertste", "de"), [("sechstausendneunhundertste", "6900", O)])
        self.assertEqual(read("honderdtweeënzestigduizendachthonderdste", "nl"),
                         [("honderdtweeënzestigduizendachthonderdste", "162800", O)])

    def test_a_scale_ordinal_below_the_last_group_adds_one_of_its_own(self):
        # 1000 + 100 = 1100; 2 x 10^6 + 1000 = 2001000; 1000 + 100 = 1100
        self.assertEqual(read("duizendhonderdste", "nl"), [("duizendhonderdste", "1100", O)])
        self.assertEqual(read("tweemiljoenduizendste", "nl"), [("tweemiljoenduizendste", "2001000", O)])
        self.assertEqual(read("zwei Millionen tausendste", "de"), [("zwei Millionen tausendste", "2001000", O)])
        self.assertEqual(read("ettusen hundrade", "sv"), [("ettusen hundrade", "1100", O)])
        # a scale ordinal above the last group still multiplies: 2 x 1000 = 2000
        self.assertEqual(read("zweitausendste", "de"), [("zweitausendste", "2000", O)])

    def test_a_scale_ordinal_adds_only_where_its_cardinal_word_stands_alone(self):
        # en "thousand" needs a count, so "two million thousand" is no number
        # and "two million thousandth" adds no thousand
        self.assertEqual(read("two million thousand", "en"), [("two million", "2000000", C)])
        self.assertNotEqual(read("two million thousandth", "en")[0][1], "2001000")
        # pt-PT makes every word ordinal, so "dois milhões milésimo" adds no
        # thousand to 2000000
        self.assertNotEqual(read("dois milhões milésimo", "pt-PT")[0][1], "2001000")

    def test_one_before_a_scale_ordinal_is_an_ordinal_where_fractions_take_their_own_word(self):
        # German fractions end in -stel ("Hundertstel"), so 1 x 100 = 100th
        self.assertEqual(read("einhundertste", "de"), [("einhundertste", "100", O)])


class TestDanishTwenties(unittest.TestCase):
    def test_the_tens_from_fifty_count_by_twenties(self):
        # 50, 60, 70, 80, 90; 5 + 90 = 95; 2 + 50 = 52
        for word, value in (("halvtreds", "50"), ("tres", "60"), ("halvfjerds", "70"), ("firs", "80"),
                            ("halvfems", "90"), ("femoghalvfems", "95"), ("tooghalvtreds", "52"),
                            ("halvfjerdsindstyve", "70")):
            with self.subTest(word=word):
                self.assertEqual(read(word, "da"), [(word, value, C)])

    def test_the_ordinal_tens_long_and_short(self):
        # 2 + 50 = 52nd in both forms
        self.assertEqual(read("tooghalvtredsindstyvende", "da"), [("tooghalvtredsindstyvende", "52", O)])
        self.assertEqual(read("tooghalvtredsende", "da"), [("tooghalvtredsende", "52", O)])


class TestNorwegianCountingOrders(unittest.TestCase):
    def test_both_orders_read_the_same_number(self):
        # 20 + 1 = 21 both ways; 100 + 21 = 121
        for lang in ("nb", "nn"):
            with self.subTest(lang=lang):
                self.assertEqual(read("tjuefem", lang), [("tjuefem", "25", C)])
                self.assertEqual(read("femogtjue", lang), [("femogtjue", "25", C)])
        self.assertEqual(read("hundre og enogtjue", "nb"), [("hundre og enogtjue", "121", C)])
        self.assertEqual(read("enogtjuende", "nb"), [("enogtjuende", "21", O)])

    def test_the_new_order_takes_no_joiner(self):
        self.assertEqual(read("tjue og tre", "nb"), [("tjue", "20", C), ("tre", "3", C)])

    def test_no_joiner_stands_between_a_ten_and_its_ordinal_unit(self):
        self.assertEqual(read("tjue og tredje", "nb"), [("tjue", "20", C), ("tredje", "3", O)])

    def test_the_joiner_after_hundred_comes_before_the_ordinal(self):
        # 100 + 5 = 105th; CLDR RBNF da "hundrede og første" is 101st
        self.assertEqual(read("hundre og femte", "nb"), [("hundre og femte", "105", O)])
        self.assertEqual(read("hundrede og femte", "da"), [("hundrede og femte", "105", O)])

    def test_no_joiner_stands_before_a_scale_ordinal(self):
        self.assertEqual(read("to og hundrede", "nb"), [("to", "2", C), ("hundrede", "100", O)])
        # "og" may follow "hundre", but no scale ordinal comes after it
        self.assertEqual(read("hundre og tusende", "nb"), [("hundre", "100", C), ("tusende", "1000", O)])

    def test_a_unit_ordinal_joins_no_ten(self):
        self.assertEqual(read("zehn dritte", "de"), [("zehn", "10", C), ("dritte", "3", O)])


class TestPointDecimals(unittest.TestCase):
    def test_a_point_that_cannot_group_digits_marks_decimals(self):
        self.assertEqual([(m.text, m.value) for m in tag_numbers("Das kostet 1.5 Millionen.", "de")],
                         [("1.5 Millionen", "1500000")])
        self.assertEqual([(m.text, m.value) for m in tag_numbers("0.500", "nl")], [("0.500", "0.5")])

    def test_a_time_of_day_with_a_point_reads_no_number(self):
        # de.wikipedia "Uhrzeit": the Swiss Federal Chancellery writes "ein
        # Punkt und kein Doppelpunkt" between hours and minutes
        for text, lang in (("Gegen 11.29 Uhr zog der Protest los.", "de"), ("om 14.30 uur", "nl"), ("kl. 23.59", "da")):
            with self.subTest(text=text):
                self.assertEqual(tag_numbers(text, lang), [])


class TestDigitOrdinals(unittest.TestCase):
    def test_a_period_after_digits_makes_an_ordinal(self):
        self.assertEqual(read("am 3. Mai", "de"), [("3", "3", O)])
        self.assertEqual(read("den 17. mai", "nb"), [("17", "17", O)])
        # not where the language has no such mark
        self.assertEqual(read("o 3. lugar", "pt-PT"), [("3", "3", C)])

    def test_a_period_at_the_end_of_the_text_ends_a_sentence(self):
        self.assertEqual(read("Ich habe 3.", "de"), [("3", "3", C)])

    def test_a_period_before_a_new_sentence_ends_it(self):
        self.assertEqual(read("Unionen ble oppløst i 1905. Dette ble bekreftet.", "nb"), [("1905", "1905", C)])
        self.assertEqual(read("Die Stadt wuchs bis 1905. Danach schrumpfte sie.", "de"), [("1905", "1905", C)])
        # up to three digits, a capital after the period is a German noun: 3rd place
        self.assertEqual(read("Er wurde 3. Sieger.", "de"), [("3", "3", O)])

    def test_a_cue_marks_the_period_as_an_ordinal(self):
        # a contracted article before four digits, a lower-case word after the period
        self.assertEqual(read("Er kam zum 1000. Mal.", "de"), [("1000", "1000", O)])
        # four digits with no cue read as a year that ends a sentence
        self.assertEqual(read("Er kam 1000. Mal.", "de"), [("1000", "1000", C)])
        self.assertEqual(read("han kom på 2. plass", "nb"), [("2", "2", O)])
        self.assertEqual(read("Han kom 2. Plass", "nb"), [("2", "2", C)])

    def test_the_swedish_colon_suffix(self):
        self.assertEqual(read("den 3:e maj", "sv"), [("3:e", "3", O)])
        self.assertEqual(read("21:a plats", "sv"), [("21:a", "21", O)])

    def test_the_dutch_letter_suffix(self):
        self.assertEqual(read("de 2de plaats", "nl"), [("2de", "2", O)])


class TestHalvesAndFractionWords(unittest.TestCase):
    def test_a_word_that_adds_a_half(self):
        # 2 + 1/2 = 2.5; (4 + 1/2) x 10^9 = 4500000000
        self.assertEqual(read("zweieinhalb Stunden", "de"), [("zweieinhalb", "2.5", F)])
        self.assertEqual(read("viereinhalb Milliarden", "de"), [("viereinhalb Milliarden", "4500000000", C)])

    def test_a_word_whose_value_is_a_fraction(self):
        # 3/2 = 1.5; 3/2 x 10^6 = 1500000
        self.assertEqual(read("anderthalb Liter", "de"), [("anderthalb", "1.5", F)])
        self.assertEqual(read("halvanden million", "da"), [("halvanden million", "1500000", C)])

    def test_a_fraction_written_as_one_word(self):
        # 3/4 = 0.75
        self.assertEqual(read("dreiviertel", "de"), [("dreiviertel", "0.75", F)])
        self.assertEqual(read("trekvart", "sv"), [("trekvart", "0.75", F)])


class TestScales(unittest.TestCase):
    def test_milliarde_is_ten_to_the_ninth_in_both_scales(self):
        for scale in (Scale.LONG, Scale.SHORT):
            with self.subTest(scale=scale):
                found = tag_numbers("zwei Milliarden", "de", scale=scale)
                self.assertEqual([(m.value, m.number_scale) for m in found], [("2000000000", None)])

    def test_billion_is_the_long_scale(self):
        found = tag_numbers("drei Billionen", "de")
        self.assertEqual([(m.value, m.number_scale) for m in found], [("3000000000000", Scale.LONG)])
        found = tag_numbers("två biljoner", "sv")
        self.assertEqual([(m.value, m.number_scale) for m in found], [("2000000000000", Scale.LONG)])

    def test_a_hundred_with_no_count_after_the_thousands_is_the_next_group(self):
        # 57 x 10^6 + 124 x 1000 + 150 = 57124150
        self.assertEqual(read("zevenenvijftig miljoen honderdvierentwintigduizendhonderdvijftig", "nl"),
                         [("zevenenvijftig miljoen honderdvierentwintigduizendhonderdvijftig", "57124150", C)])
        self.assertEqual(read("to millioner hundrede og fireogtyve tusind hundrede og halvtreds", "da"),
                         [("to millioner hundrede og fireogtyve tusind hundrede og halvtreds", "2124150", C)])

    def test_swedish_ettusen_shares_one_t(self):
        # 1 x 1000; (30 + 1) x 1000 = 31000
        self.assertEqual(read("ettusen kronor", "sv"), [("ettusen", "1000", C)])
        self.assertEqual(read("trettioettusen kronor", "sv"), [("trettioettusen", "31000", C)])


class TestArticles(unittest.TestCase):
    def test_an_article_before_a_hyphenated_noun_is_weak(self):
        for text, lang, word in (("Mache eine Bildschirm-Aufnahme.", "de", "eine"),
                                 ("Starte einen Internet-Geschwindigkeitstest.", "de", "einen"),
                                 ("Maak een audio-opname.", "nl", "een")):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.confidence) for m in tag_numbers(text, lang)], [(word, 0.3)])

    def test_an_article_alone_is_a_weak_one(self):
        for text, lang in (("ein Haus", "de"), ("een huis", "nl"), ("en bil", "da"), ("ett hus", "sv"),
                           ("ei avis", "nb"), ("ein bil", "nn")):
            with self.subTest(lang=lang):
                found = tag_numbers(text, lang)
                self.assertEqual([m.value for m in found], ["1"])
                self.assertLess(found[0].confidence, 0.5)

    def test_the_accented_numeral_is_no_article(self):
        for text, lang in (("één huis", "nl"), ("én bil", "nb"), ("éin bil", "nn")):
            with self.subTest(lang=lang):
                self.assertEqual([m.confidence for m in tag_numbers(text, lang)], [1.0])

    def test_a_lone_ein_at_the_clause_end_is_the_verb_particle(self):
        found = tag_numbers("Er lud mich ein.", "de")
        self.assertEqual([m.value for m in found], ["1"])
        self.assertLess(found[0].confidence, 0.5)
        # the counting form "eins" is a numeral there
        self.assertEqual([m.confidence for m in tag_numbers("Er nahm eins.", "de")], [1.0])

    def test_a_lone_genitive_article_is_weak(self):
        found = tag_numbers("eines", "de")
        self.assertEqual([m.value for m in found], ["1"])
        self.assertLess(found[0].confidence, 0.5)

    def test_tiende_is_also_the_tithe(self):
        for lang in ("da", "nb"):
            with self.subTest(lang=lang):
                found = tag_numbers("betalte tiende", lang)
                self.assertEqual([m.value for m in found], ["10"])
                self.assertLess(found[0].confidence, 0.5)

    def test_an_article_that_is_no_numeral_is_no_number(self):
        self.assertEqual(read("et fint hus", "nb"), [])
        self.assertEqual(read("eit fint hus", "nn"), [])

    def test_an_article_counts_a_number_noun(self):
        self.assertEqual(read("eine Million", "de"), [("eine Million", "1000000", C)])
        self.assertEqual(read("in miljoen", "fy"), [("in miljoen", "1000000", C)])


class TestRanges(unittest.TestCase):
    def test_a_joiner_inside_a_compound_word_splits_no_range(self):
        # 21 to 30
        self.assertEqual(read("zwischen einundzwanzig und dreißig", "de"),
                         [("einundzwanzig", "21", C), ("dreißig", "30", C)])


class TestLanguageTags(unittest.TestCase):
    def test_no_reads_bokmal(self):
        self.assertEqual(read("tjueen", "no"), [("tjueen", "21", C)])

    def test_cldr_ordinals_read(self):
        # CLDR renderings: da 40th, 1000000th; sv 100th, 1000th, 1000000th
        self.assertEqual(read("fyrrende", "da"), [("fyrrende", "40", O)])
        self.assertEqual(read("millionte", "da"), [("millionte", "1000000", O)])
        self.assertEqual(read("etthundrade", "sv"), [("etthundrade", "100", O)])
        self.assertEqual(read("ettusende", "sv"), [("ettusende", "1000", O)])
        self.assertEqual(read("en miljonte", "sv"), [("en miljonte", "1000000", O)])
        self.assertEqual(read("einundzwanzig", "de-AT"), [("einundzwanzig", "21", C)])


if __name__ == "__main__":
    unittest.main()
