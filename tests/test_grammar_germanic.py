"""Germanic grammar rules: compound words, the unit before the ten, Danish
tens by twenties, the two Norwegian counting orders, ordinals in digits and
"and a half" words. Each expected value is worked out by hand in the comment
beside it; sources are in numtag/lexicon/<lang>.json."""
import unittest

import pytest

from helpers import read, sure
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
        for text, lang in (("Gegen 11.29 Uhr zog der Protest los.", "de"), ("om 14.30 uur", "nl"), ("kl. 23.59", "da"),
                           ("um 24.00 Uhr", "de")):
            with self.subTest(text=text):
                self.assertEqual(tag_numbers(text, lang), [])
        # past the hours and minutes of a day the point marks decimals again
        for text, value in (("24.30", "24.3"), ("1.60", "1.6"), ("0.60", "0.6")):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.value) for m in tag_numbers(text, "de")], [(text, value)])

    def test_a_day_and_month_with_a_period_after_them_read_no_number(self):
        # en.wikipedia "Date and time notation in Finland": "When the year is
        # not specified, a trailing full stop is used, such as 31.5. for 31 May"
        for text, lang in (("am 24.12.", "de"), ("am 1.5. ist Feiertag", "de"), ("vom 24.12. bis 26.12.", "de"),
                           ("17.5. er nasjonaldagen", "nb"), ("den 24.12.", "da"), ("den 31.12.", "nn")):
            with self.subTest(text=text):
                self.assertEqual(tag_numbers(text, lang), [])
        # no day above 31 and no month above 12: 32.12 and 24.15 are decimals
        self.assertEqual([(m.text, m.value) for m in tag_numbers("am 32.12.", "de")], [("32.12", "32.12")])
        self.assertEqual([(m.text, m.value) for m in tag_numbers("am 24.15.", "de")], [("24.15", "24.15")])
        # where the point marks decimals, a period after them ends the sentence
        self.assertEqual([(m.text, m.value) for m in tag_numbers("The rate is 2.5.", "en")], [("2.5", "2.5")])
        # three digits after the point are a group, also before a period
        self.assertEqual([(m.text, m.value) for m in tag_numbers("Es kostet 1.500.", "de")], [("1.500", "1500")])


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

    def test_the_frisian_letter_suffix(self):
        # Wikipedia (fy), "21e iuw": "De 21e iuw of ienentweintichste iuw"
        self.assertEqual(read("de 21e iuw", "fy"), [("21e", "21", O)])


class TestFrisianClockHours(unittest.TestCase):
    def test_the_hour_after_healwei_kertier_oer_and_foar_is_sure(self):
        # the inflected hour forms: "fiven" is 5, "fjouweren" 4, "trijen" 3, "tolven" 12
        self.assertEqual(sure("healwei fiven", "fy"), [("fiven", "5", 1.0)])
        self.assertEqual(sure("kertier oer fjouweren", "fy"), [("fjouweren", "4", 1.0)])
        self.assertEqual(sure("kertier foar trijen", "fy"), [("trijen", "3", 1.0)])
        self.assertEqual(read("om healwei tolven", "fy"), [("tolven", "12", C)])

    def test_the_hour_form_alone_is_also_a_plural_noun(self):
        # Wiktionary, "achten": plural of "acht"
        self.assertEqual(sure("de achten", "fy"), [("achten", "8", 0.4)])

    def test_the_hour_form_is_no_first_part_of_a_compound(self):
        # 1 + 20 = 21, 8 + 40 = 48, 9 + 30 = 39: "ienen", "achten" and
        # "njoggenen" end in the joiner "en", and the split keeps the joiner
        self.assertEqual(read("ienentweintich", "fy"), [("ienentweintich", "21", C)])
        self.assertEqual(read("achtenfjirtich", "fy"), [("achtenfjirtich", "48", C)])
        self.assertEqual(read("njoggenentritich", "fy"), [("njoggenentritich", "39", C)])


class TestHalvesAndFractionWords(unittest.TestCase):
    def test_a_word_that_adds_a_half(self):
        # 2 + 1/2 = 2.5; (4 + 1/2) x 10^9 = 4500000000
        self.assertEqual(read("zweieinhalb Stunden", "de"), [("zweieinhalb", "2.5", F)])
        self.assertEqual(read("viereinhalb Milliarden", "de"), [("viereinhalb Milliarden", "4500000000", C)])

    def test_a_quarter_fraction_glued_to_the_whole(self):
        # 2 + 1/4 = 2.25; 1 + 1/4 = 1.25; 10 + 1/4 = 10.25; 2 + 3/4 = 2.75; 1 + 3/4 = 1.75
        self.assertEqual(read("in zweieinviertel Stunden", "de"), [("zweieinviertel", "2.25", F)])
        self.assertEqual(read("in eineinviertel Stunden", "de"), [("eineinviertel", "1.25", F)])
        self.assertEqual(read("in zehneinviertel Stunden", "de"), [("zehneinviertel", "10.25", F)])
        self.assertEqual(read("in zweidreiviertel Stunden", "de"), [("zweidreiviertel", "2.75", F)])
        self.assertEqual(read("eindreiviertel Jahre", "de"), [("eindreiviertel", "1.75", F)])
        # 21 + 1/4 = 21.25
        self.assertEqual(read("einundzwanzigeinviertel", "de"), [("einundzwanzigeinviertel", "21.25", F)])

    def test_a_glued_count_and_part_with_no_whole_stay_one_fraction(self):
        # "zweidrittel" is 2/3, not 2 + 1/3: the part has no count of its own
        self.assertEqual(read("zweidrittel", "de"), [("zweidrittel", "2/3", F)])
        self.assertEqual(read("zweieinhalb", "de"), [("zweieinhalb", "2.5", F)])
        # a part word of a hundred or more after a count is a glued denominator,
        # never a part after the whole: no 2 + 10/10000 or 2 + 1/100
        self.assertEqual(read("zweizehntausendstel", "de"), [])
        self.assertEqual(read("zweieinhundertstel", "de"), [])

    def test_only_a_quarter_glues_to_the_whole(self):
        # Duden and DWDS show "ein|drei|vier|tel" and "einviertel" only; a count
        # glued to any other part word stays a count and a fraction, not a whole plus a part
        self.assertEqual(read("zweieinzehntel", "de"), [])
        self.assertEqual(read("zweieinsechstel", "de"), [])
        self.assertEqual(read("zweizweiviertel", "de"), [])

    def test_a_part_glued_to_the_whole_is_only_german(self):
        # no lexicon but German turns the setting on
        self.assertEqual(read("tvåtrekvart", "sv"), [])

    def test_a_word_whose_value_is_a_fraction(self):
        # 3/2 = 1.5; 3/2 x 10^6 = 1500000
        self.assertEqual(read("anderthalb Liter", "de"), [("anderthalb", "1.5", F)])
        # the inflected form before a common-gender noun
        self.assertEqual(read("anderhalve week", "nl"), [("anderhalve", "1.5", F)])
        self.assertEqual(read("anderhalf jaar", "nl"), [("anderhalf", "1.5", F)])
        self.assertEqual(read("halvanden million", "da"), [("halvanden million", "1500000", C)])

    def test_a_fraction_written_as_one_word(self):
        # 3/4 = 0.75
        self.assertEqual(read("dreiviertel", "de"), [("dreiviertel", "0.75", F)])
        self.assertEqual(read("trekvart", "sv"), [("trekvart", "0.75", F)])

    def test_kwart_is_a_quarter(self):
        # 1 / 4 = 0.25, the article is in the span as in "in fjirde"
        self.assertEqual(read("in kwart", "fy"), [("in kwart", "0.25", F)])
        # 3 / 4 = 0.75; 2 + 1 / 4 = 2.25
        self.assertEqual(read("trije kwart fan de befolking", "fy"), [("trije kwart", "0.75", F)])
        self.assertEqual(read("twa en in kwart", "fy"), [("twa en in kwart", "2.25", F)])

    def test_kwart_alone_is_no_sure_number(self):
        # a quarter past the hour holds the hour 3 only; "kwart" of "kwart finales" is no number
        self.assertEqual(read("kwart oer trije", "fy"), [("trije", "3", C)])
        self.assertEqual(read("de kwart finales", "fy"), [])

    def test_halb_before_an_hour_is_the_half_hour(self):
        # "halb drei" is 2:30: the hour 3 is the number, "halb" is no half of it
        for text, hour, value in (("um halb drei", "drei", "3"), ("weck mich um halb zwölf", "zwölf", "12"),
                                  ("um halb 3", "3", "3")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "de"), [(hour, value, C)])
        # a half with no number after it stays a weak half
        self.assertEqual(read("halb so viel", "de"), [("halb", "0.5", F)])
        self.assertEqual(read("ein halbes Brot", "de"), [("ein halbes", "0.5", F)])


class TestGluedPartWords(unittest.TestCase):
    # Sources: Wiktionary de "Zehntausendstel" ("der zehntausendste Teil von
    # etwas"), DWDS corpus examples; see numtag/lexicon/de.json.
    def test_a_count_glued_to_a_part_word_names_one_denominator(self):
        # 1/200 = 0.005; 1/3000 has no finite decimal form
        self.assertEqual(read("ein Zweihundertstel", "de"), [("ein Zweihundertstel", "0.005", F)])
        self.assertEqual(read("ein Dreitausendstel", "de"), [("ein Dreitausendstel", "1/3000", F)])

    def test_the_glued_part_word_alone_is_one_of_the_part(self):
        # 1/200 = 0.005; 1/(10 x 1000) = 0.0001; 1/(2 x 100 x 1000) = 0.000005
        self.assertEqual(read("Zweihundertstel", "de"), [("Zweihundertstel", "0.005", F)])
        self.assertEqual(read("Zehntausendstel", "de"), [("Zehntausendstel", "0.0001", F)])
        self.assertEqual(read("Zweihunderttausendstel", "de"), [("Zweihunderttausendstel", "0.000005", F)])

    def test_a_separate_count_before_a_glued_part_word_is_the_numerator(self):
        # 3/200 = 0.015; 5/10000 = 0.0005
        self.assertEqual(read("drei Zweihundertstel", "de"), [("drei Zweihundertstel", "0.015", F)])
        self.assertEqual(read("fünf Zehntausendstel", "de"), [("fünf Zehntausendstel", "0.0005", F)])

    def test_a_part_word_with_a_separate_count_is_unchanged(self):
        # 2/100 = 0.02; 3/1000 = 0.003; 1/100 = 0.01
        self.assertEqual(read("zwei Hundertstel", "de"), [("zwei Hundertstel", "0.02", F)])
        self.assertEqual(read("drei Tausendstel", "de"), [("drei Tausendstel", "0.003", F)])
        self.assertEqual(read("ein Hundertstel", "de"), [("ein Hundertstel", "0.01", F)])
        self.assertEqual(read("Hundertstel", "de"), [])

    def test_digits_before_a_glued_part_word_are_its_numerator(self):
        # DWDS, Aktuelles Lexikon: 164 hundred-thousandths of a second
        self.assertEqual(read("Der Tag wird damit in einem Jahrhundert um 164 Hunderttausendstel Sekunden länger.", "de"),
                         [("einem", "1", C), ("164 Hunderttausendstel", "0.00164", F)])
        self.assertEqual(read("3 Zweihundertstel", "de"), [("3 Zweihundertstel", "0.015", F)])

    def test_an_ordinal_is_no_part_word(self):
        self.assertEqual(read("der zweihundertste Tag", "de"), [("zweihundertste", "200", O)])

    def test_a_hyphen_before_the_glued_word_is_no_glued_count(self):
        # no source rules this shape; the old reading stays: 1 and 2/100 = 0.02
        self.assertEqual(read("ein-Zweihundertstel", "de"), [("ein", "1", C), ("Zweihundertstel", "0.02", F)])

    def test_sentences_from_the_dwds_corpus(self):
        # Die Welt, 05.08.2003: 1/200 = 0.005
        self.assertEqual(read("Aber der Grundstoff für Bier mache gerade mal ein Zweihundertstel des Endpreises aus.", "de"),
                         [("ein Zweihundertstel", "0.005", F)])
        # Süddeutsche Zeitung, 30.03.1995: 1/(100 x 1000) = 0.00001
        self.assertEqual(read("Insgesamt empfängt die Erde vom Mond etwa ein Hunderttausendstel der direkten Sonnenstrahlung.", "de"),
                         [("ein Hunderttausendstel", "0.00001", F)])
        # Süddeutsche Zeitung, 14.07.1994: 5/10000 mm = 0.0005 mm = 0.5 micrometre, half of 1
        self.assertEqual(read("Die gesamte Lage mißt kaum einen halben Mikrometer, das sind fünf Zehntausendstel Millimeter.", "de"),
                         [("einen halben", "0.5", F), ("fünf Zehntausendstel", "0.0005", F)])

    def test_a_glued_part_word_with_no_count_has_the_score_of_a_homograph(self):
        # 3 + 1/200 = 3.005; the word alone can be a plural with no determiner
        # ("wertvolle Hundertstel"), so these score 0.4, and a count before it scores 1.0
        self.assertEqual(sure("Zweihundertstel", "de"), [("Zweihundertstel", "0.005", 0.4)])
        self.assertEqual(sure("wertvolle Zweihundertstel", "de"), [("Zweihundertstel", "0.005", 0.4)])
        self.assertEqual(sure("drei und Zweihundertstel", "de"), [("drei und Zweihundertstel", "3.005", 0.4)])
        self.assertEqual(sure("ein Zweihundertstel", "de"), [("ein Zweihundertstel", "0.005", 1.0)])
        self.assertEqual(sure("drei Zweihundertstel", "de"), [("drei Zweihundertstel", "0.015", 1.0)])


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


class TestScaleNamesAboveABillion(unittest.TestCase):
    # long scale: the n-th -illion is 10^(6 n), and the -iard after it is 10^(6 n + 3)
    def test_triljoen_is_ten_to_the_eighteenth_in_frisian(self):
        # 12 x 10^18 + 345 = 12000000000000000000 + 345
        self.assertEqual(read("tolve triljoen trijehûndertfiifenfjirtich", "fy"),
                         [("tolve triljoen trijehûndertfiifenfjirtich", "12000000000000000345", C)])

    def test_trillion_is_ten_to_the_eighteenth_in_norwegian(self):
        # 12 x 10^18 + 345 = 12000000000000000000 + 345
        self.assertEqual(read("tolv trillioner tre hundre og førtifem", "nb"),
                         [("tolv trillioner tre hundre og førtifem", "12000000000000000345", C)])
        self.assertEqual(read("tolv trillionar tre hundre og førtifem", "nn"),
                         [("tolv trillionar tre hundre og førtifem", "12000000000000000345", C)])
        # 1 x 10^18, written as 1 and 18 zeros
        self.assertEqual(read("en trillion", "nb"), [("en trillion", "1000000000000000000", C)])
        self.assertEqual(read("ein trillion", "nn"), [("ein trillion", "1000000000000000000", C)])

    def test_triljard_is_ten_to_the_twenty_first_in_dutch(self):
        # 10^3 x 10^18 = 10^21, written as 1 and 21 zeros
        self.assertEqual(read("een triljard", "nl"), [("een triljard", "1000000000000000000000", C)])
        # nl.wiktionary "triljard": 602 x 10^21 + 214 x 10^18 = 602214 x 10^18
        self.assertEqual(read("bij benadering zeshonderdtwee triljard tweehonderdveertien triljoen moleculen", "nl"),
                         [("zeshonderdtwee triljard tweehonderdveertien triljoen", "602214000000000000000000", C)])
        self.assertEqual(read("triljardste", "nl"), [("triljardste", "1000000000000000000000", "ordinal")])


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

    def test_annen_and_fyrste_are_ordinals_that_are_also_other_words(self):
        # Bokmålsordboka "andre, annen": 2nd, and "annen": other;
        # Nynorskordboka "første, fyrste": 1st, and "fyrste": a prince
        self.assertEqual(read("annen mandag i januar", "nb"), [("annen", "2", O)])
        self.assertEqual(read("fyrste måndag", "nn"), [("fyrste", "1", O)])
        self.assertEqual(sure("annen mandag", "nb"), [("annen", "2", 0.4)])
        self.assertEqual(sure("fyrste kvartal", "nn"), [("fyrste", "1", 0.4)])

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


class TestOpenIssues(unittest.TestCase):
    # Rows each open issue lists. The expected value is the issue's, worked out by hand.

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/215")
    def test_dreizehntel_is_one_thirteenth(self):
        self.assertEqual(read("dreizehntel", "de"), [("dreizehntel", "1/13", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/215")
    def test_neunzehntel_is_one_nineteenth(self):
        self.assertEqual(read("neunzehntel", "de"), [("neunzehntel", "1/19", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/215")
    def test_ein_dreizehntel_is_one_thirteenth(self):
        self.assertEqual(read("ein Dreizehntel", "de"), [("ein Dreizehntel", "1/13", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/216")
    def test_hundred_and_three_quarters_compound(self):
        self.assertEqual(read("hundertdreiviertel", "de"), [("hundertdreiviertel", "100.75", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/216")
    def test_two_hundred_and_a_quarter_compound(self):
        # 200 + 1/4 = 200.25
        self.assertEqual(read("zweihunderteinviertel", "de"), [("zweihunderteinviertel", "200.25", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/216")
    def test_one_hundred_and_three_quarters_compound(self):
        # 100 + 3/4 = 100.75
        self.assertEqual(read("einhundertdreiviertel", "de"), [("einhundertdreiviertel", "100.75", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/246")
    def test_norwegian_annet_is_second(self):
        self.assertEqual(read("annet kvartal", "nb"), [("annet", "2", O)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/253")
    def test_danish_split_four_and_twenty(self):
        self.assertEqual(read("fire og tyve", "da"), [("fire og tyve", "24", C)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/253")
    def test_danish_two_and_a_half_with_en(self):
        self.assertEqual(read("to en halv", "da"), [("to en halv", "2.5", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/163")
    def test_danish_minus_before_units_and_tens(self):
        self.assertEqual(read("minus fem og tyve", "da"), [("minus fem og tyve", "-25", C)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/264")
    def test_norwegian_nb_zeroth(self):
        self.assertEqual(read("nulte", "nb"), [("nulte", "0", O)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/264")
    def test_norwegian_nn_millionth(self):
        self.assertEqual(read("millionte", "nn"), [("millionte", "1000000", O)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/264")
    def test_danish_sixtieth(self):
        self.assertEqual(read("tressende", "da"), [("tressende", "60", O)])


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/148")
@pytest.mark.parametrize("text, expected", [
    ('in fuenf Tagen', [('fuenf', '5', C)]),
    ('in zwoelf Tagen', [('zwoelf', '12', C)]),
    ('in fuenfzehn Tagen', [('fuenfzehn', '15', C)]),
    ('in fuenfzig Tagen', [('fuenfzig', '50', C)]),
    ('der fuenfte Tag', [('fuenfte', '5', O)]),
    ('der zwoelfte Tag', [('zwoelfte', '12', O)]),
])
def test_de_the_ascii_spellings_of_the_umlaut_number_words(text, expected):
    assert read(text, "de") == expected


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/168")
@pytest.mark.parametrize("text, expected", [
    ('Er hat es außer Acht gelassen', []),
    ('Nimm dich in Acht', []),
    ('Der Elf Legolas', []),
    ('Tausend Dank', []),
])
def test_de_a_capitalised_number_word_in_an_idiom_or_a_name_is_no_number(text, expected):
    assert read(text, "de") == expected


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/168")
@pytest.mark.parametrize("text, expected", [
    ('sechtjin', [('sechtjin', '16', C)]),
])
def test_fy_sechtjin_is_16(text, expected):
    assert read(text, "fy") == expected



if __name__ == "__main__":
    unittest.main()
