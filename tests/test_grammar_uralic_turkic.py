"""Finnish, Estonian, Hungarian, Turkish and Azerbaijani grammar rules. Each
expected value is worked out by hand in the comment beside it; sources are in
numtag/lexicon/<lang>.json."""
import unittest
from dataclasses import replace
from unittest.mock import patch

from helpers import read, sure
from numtag import Reason, tag_numbers
from numtag.lexicon import load

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

    def test_a_soft_hyphen_inside_a_word_is_no_break(self):
        # ICU writes U+00AD between the parts: 20 + 5 = 25; 10 + 5 = 15 in the genitive
        self.assertEqual(read("huszon\u00adöt forint", "hu"), [("huszon\u00adöt", "25", C)])
        self.assertEqual(read("viiden\u00adtoista päivän", "fi"), [("viiden\u00adtoista", "15", C)])
        self.assertEqual(read("kolme\u00adsataa\u00adkuusi\u00adkymmentä\u00adviisi", "fi"),
                         [("kolme\u00adsataa\u00adkuusi\u00adkymmentä\u00adviisi", "365", C)])
        # a soft hyphen joins letters only: a hyphen or a space still splits
        self.assertEqual(read("huszon öt", "hu"), [("huszon öt", "25", C)])
        self.assertEqual(read("kaksi \u00ad viisi", "fi"), [("kaksi", "2", C), ("viisi", "5", C)])


class TestColloquialUnits(unittest.TestCase):
    def test_the_colloquial_six_and_seven(self):
        # "kuus" is "kuusi" (6) and "seittemän" is "seitsemän" (7)
        self.assertEqual(read("kuus", "fi"), [("kuus", "6", C)])
        self.assertEqual(read("seittemän", "fi"), [("seittemän", "7", C)])
        # "kuus" is also the shortened "kuussa" (in the month): a weak number alone
        self.assertEqual(sure("kerran kuus", "fi"), [("kuus", "6", 0.4)])
        # 6 + 7 as two numbers
        self.assertEqual(read("kuus ja seittemän", "fi"), [("kuus", "6", C), ("seittemän", "7", C)])


class TestGroupsAfterAScale(unittest.TestCase):
    def test_a_bare_hundred_or_ten_after_thousands_joins_the_number(self):
        # 10^6 + 2 x 1000 + 100 + 40 + 5 = 1002145
        self.assertEqual(read("bir milyon iki bin yüz kırk beş", "tr"),
                         [("bir milyon iki bin yüz kırk beş", "1002145", C)])
        # 10^6 + 2 x 1000 + 10 = 1002010
        self.assertEqual(read("miljoona kaksituhatta kymmenen", "fi"), [("miljoona kaksituhatta kymmenen", "1002010", C)])


class TestScaleNamesAboveATrillion(unittest.TestCase):
    def test_kentilyon_is_ten_to_the_eighteenth(self):
        # kentilyon = 1000 x katrilyon = 10^3 x 10^15 = 10^18, written as 1 and 18 zeros
        self.assertEqual(read("bir kentilyon", "tr"), [("bir kentilyon", "1000000000000000000", C)])
        # 12 x 10^18 + 345 = 12000000000000000000 + 345
        self.assertEqual(read("on iki kentilyon üç yüz kırk beş", "tr"),
                         [("on iki kentilyon üç yüz kırk beş", "12000000000000000345", C)])


class TestVagueQuantity(unittest.TestCase):
    def test_a_vague_word_before_a_scale_word_is_no_number(self):
        # TDK "birkaç": "Çok olmayan, az sayıda": the word stands where the count would, so no number
        for text in ("birkaç milyon kişi", "birkaç bin", "birkaç yüz", "birkaç milyar lira", "Birkaç milyon insan",
                     "birkaç bine", "birkaç milyonu", "birkaç yüz bin", "birçok milyon", "onlarca milyon dolar",
                     "yüzlerce bin", "binlerce milyon", "milyonlarca milyar", "Kaç bin kişi geldi?"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "tr"), [])

    def test_a_vague_word_changes_only_the_word_after_it(self):
        # 10^6; 2 x 10^3; 10^6 / 2; 3 x 10^6 + 2 x 10^5 = 3200000
        self.assertEqual(read("bir milyon", "tr"), [("bir milyon", "1000000", C)])
        self.assertEqual(read("iki bin", "tr"), [("iki bin", "2000", C)])
        self.assertEqual(read("yarım milyon", "tr"), [("yarım milyon", "500000", C)])
        self.assertEqual(read("üç milyon iki yüz bin", "tr"), [("üç milyon iki yüz bin", "3200000", C)])
        self.assertEqual(read("birkaç", "tr"), [])
        self.assertEqual(read("birkaç kişi", "tr"), [])
        # a comma or a full stop ends the vague phrase, so the next scale word counts one
        self.assertEqual(read("birkaç milyon, bin kişi", "tr"), [("bin", "1000", C)])
        self.assertEqual(read("birkaç yüz. Bin kişi geldi.", "tr"), [("Bin", "1000", C)])
        # a year in digits is its own number
        self.assertEqual(read("2030 birkaç milyon", "tr"), [("2030", "2030", C)])

    def test_the_split_spelling_bir_kac_reads_as_birkac(self):
        # the Yazım Kılavuzu writes "birkaç" as one word; the split spelling names no number either,
        # while "bir" before a scale word stays one: 1 x 10^6
        self.assertEqual(read("bir kaç milyon", "tr"), [])
        self.assertEqual(read("bir kaç kişi", "tr"), [])
        self.assertEqual(read("bir milyon", "tr"), [("bir milyon", "1000000", C)])

    def test_a_vague_word_before_a_quarter_is_no_number(self):
        # "birkaç çeyrek" is a few quarters, with no number; "çeyrek" alone stays 1/4 at the homograph score
        self.assertEqual(read("birkaç çeyrek", "tr"), [])
        self.assertEqual([(m.value, m.confidence) for m in tag_numbers("çeyrek", "tr")], [("0.25", 0.4)])

    def test_the_vague_words_that_are_also_other_words_are_ambiguous(self):
        # TDK lists "onlarca" also as the adverb "Onlara göre" and "kaç" also as the verb "kaçmak";
        # "birkaç" has one sense only
        vague = load("tr").vague_quantifiers
        self.assertEqual((vague[("birkaç",)], vague[("onlarca",)], vague[("kaç",)]), (False, True, True))


class TestTeensAndTens(unittest.TestCase):
    def test_a_teen_joins_only_the_unit_in_its_own_word(self):
        # "yksi toista vastaan" is "one against the other"; "yksitoista" is 1 + 10 = 11
        self.assertEqual(read("yksi toista vastaan", "fi"), [("yksi", "1", C), ("toista", "2", O)])
        self.assertEqual(read("yksitoista", "fi"), [("yksitoista", "11", C)])
        # an ordinal unit joins a Finnish teen: the 11th; the Estonian 12th is
        # built on the genitive, so "teineteist" (each other) is no number
        self.assertEqual(read("yhdestoista", "fi"), [("yhdestoista", "11", O)])
        self.assertEqual(read("Nad aitavad teineteist.", "et"), [])
        self.assertEqual(read("kaheteistkümnes", "et"), [("kaheteistkümnes", "12", O)])
        self.assertEqual(read("kaksteist", "et"), [("kaksteist", "12", C)])

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
        # "beşte" (at five) ends the number; no count follows it
        self.assertEqual(read("saat beşte geldi", "tr"), [("beşte", "5", C)])
        # "ikide yüz": a hundred is no part of two, so no fraction either
        self.assertEqual(read("ikide yüz kişi", "tr"), [("ikide", "2", C), ("yüz", "100", C)])

    def test_the_locative_names_the_parts_of_a_fraction(self):
        # "üçte biri" is one of three parts, 1/3; "dörtte bir" 1/4; "beşte iki" 2/5 = 0.4
        self.assertEqual(read("pastanın üçte biri", "tr"), [("üçte biri", "1/3", F)])
        self.assertEqual(read("dörtte bir hisse", "tr"), [("dörtte bir", "0.25", F)])
        self.assertEqual(read("saat beşte iki kişi geldi", "tr"), [("beşte iki", "0.4", F)])
        # "beşdə üç" is 3/5 = 0.6
        self.assertEqual(read("beşdə üç", "az"), [("beşdə üç", "0.6", F)])
        # the count must be smaller than the parts: "üçte beş" is 3 and 5
        self.assertEqual(read("üçte beş", "tr"), [("üçte", "3", C), ("beş", "5", C)])

    def test_a_hundred_multiplier_counts_no_hundred_word(self):
        # "yüz yüze" (face to face) is 100 and 100, not 100 x 100
        self.assertEqual(read("yüz yüze", "tr"), [("yüz", "100", C), ("yüze", "100", C)])
        # 2 x 100 = 200; 1000 + 100 = 1100
        self.assertEqual(read("iki yüz", "tr"), [("iki yüz", "200", C)])
        self.assertEqual(read("bin yüz", "tr"), [("bin yüz", "1100", C)])

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

    def test_a_period_after_a_year_before_a_month_is_no_ordinal(self):
        # the year of a Hungarian date takes a full stop: 2008, then the 3rd day
        self.assertEqual(read("2008. február 3-án", "hu"), [("2008", "2008", C), ("3", "3", C)])
        self.assertEqual(read("2008. februárban", "hu"), [("2008", "2008", C)])
        self.assertEqual(read("2008. febr. 3-án", "hu"), [("2008", "2008", C), ("3", "3", C)])
        # any other lower-case word keeps the ordinal: the 3rd line, the 5th novella
        self.assertEqual(read("a 3. sor", "hu"), [("3", "3", O)])
        self.assertEqual(read("a 3. novella", "hu"), [("3", "3", O)])

    def test_azerbaijani_short_ordinal_suffix(self):
        # "5-ci" is the 5th
        self.assertEqual(read("5-ci sinif", "az"), [("5-ci", "5", O)])

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

    def test_a_count_glued_to_a_denominator_multiplies_it(self):
        # Wiktionary Module:number list/data/hu: "tízezred" for 10000,
        # "kétszázad" for 200, "milliomod" for 10^6.
        # 3 + 1/10^4 = 3.0001; 0 + 2500/10^6 = 0.0025; 3 + 7/10^7 = 3.0000007
        self.assertEqual(read("három egész egy tízezred", "hu"), [("három egész egy tízezred", "3.0001", D)])
        self.assertEqual(read("nulla egész kétezer-ötszáz milliomod", "hu"),
                         [("nulla egész kétezer-ötszáz milliomod", "0.0025", D)])
        self.assertEqual(read("három egész hét tízmilliomod", "hu"), [("három egész hét tízmilliomod", "3.0000007", D)])
        # 99999/10^5 = 0.99999: the "száz" of "százezred" counts nothing before it
        self.assertEqual(read("nulla egész kilencvenkilencezer-kilencszázkilencvenkilenc százezred", "hu"),
                         [("nulla egész kilencvenkilencezer-kilencszázkilencvenkilenc százezred", "0.99999", D)])
        # 0 + 1/10^5 = 0.00001 and 1/10^5: "egy" counts "százezred", not the "száz" in it
        self.assertEqual(read("nulla egész egy százezred", "hu"), [("nulla egész egy százezred", "0.00001", D)])
        self.assertEqual(read("egy százezred", "hu"), [("egy százezred", "0.00001", F)])
        # 7/10^5; 1/200 = 0.005; 1/10^6
        self.assertEqual(read("hét százezred", "hu"), [("hét százezred", "0.00007", F)])
        self.assertEqual(read("egy kétszázad", "hu"), [("egy kétszázad", "0.005", F)])
        self.assertEqual(read("egy milliomod", "hu"), [("egy milliomod", "0.000001", F)])
        # "kétharmad" is 2/3
        self.assertEqual(read("kétharmad", "hu"), [("kétharmad", "2/3", F)])

    def test_a_lone_glued_part_word_is_a_multiplier_at_the_homograph_score(self):
        # hu.wikipedia uses the lone glued form as a multiplier; AkH 12 §293
        # reads "háromszázad másodperc" as 3/100 and stays the alternative.
        # 1/(2 x 100) = 0.005; 1/(10 x 1000) = 0.0001; 1/(100 x 1000) = 0.00001;
        # 1/(3 x 100) has no finite decimal; 1/(2 x 1000) = 0.0005; 1/(3 x 1000)
        rows = [
            ("kétszázad", "kétszázad", "0.005"),
            ("tízezred", "tízezred", "0.0001"),
            # hu.wikipedia, "Bróm"
            ("ahol mennyisége körülbelül háromszázad része a klórénak", "háromszázad", "1/300"),
            # hu.wikipedia, "Oxigén"
            ("a teljes légköri oxigén mennyiségének kétezred részét", "kétezred", "0.0005"),
            # hu.wikipedia, "Atommag"
            ("ami az atom méretének tízezred része", "tízezred", "0.0001"),
            # hu.wikipedia, "Izotópos összetétel"
            ("az atommagok mérete átlagosan százezred Å-nyi (1 fm)", "százezred", "0.00001"),
            # hu.wikipedia, "ETME"
            ("a hajszál végének háromezred részével egyenlő", "háromezred", "1/3000"),
        ]
        for text, word, value in rows:
            with self.subTest(text=text):
                self.assertEqual(read(text, "hu")[0], (word, value, F))
                self.assertEqual(tag_numbers(text, "hu")[0].confidence, 0.4)
                self.assertEqual(tag_numbers(text, "hu")[0].reasons, frozenset({Reason.HOMOGRAPH}))

    def test_a_lone_glued_part_word_after_a_joiner_keeps_the_homograph_score(self):
        # 3 + 1/200 = 3.005; 3 + 1/300 = 901/300; 3 + 1/10000 = 3.0001
        for text, value in [("három és kétszázad", "3.005"), ("három és háromszázad", "901/300"),
                            ("három és tízezred", "3.0001")]:
            with self.subTest(text=text):
                self.assertEqual(read(text, "hu"), [(text, value, F)])
                self.assertEqual(tag_numbers(text, "hu")[0].confidence, 0.4)
                self.assertEqual(tag_numbers(text, "hu")[0].reasons, frozenset({Reason.HOMOGRAPH}))

    def test_a_lone_glued_part_word_after_a_number_reads_as_before(self):
        # the count before the word is read alone: no second mention of the part word
        self.assertEqual(read("3 tízezred", "hu"), [("3", "3", C)])
        self.assertEqual(read("3 tízezred része", "hu"), [("3", "3", C)])
        self.assertEqual(read("három egész kétezred", "hu"), [("három", "3", C)])
        self.assertEqual(read("nulla egész kétezred", "hu"), [("nulla", "0", C)])
        self.assertEqual(read("nulla kétszázad", "hu"), [("nulla", "0", C)])

    def test_a_sentence_break_lets_the_lone_reading_back(self):
        self.assertEqual(read("három. Tízezred része", "hu"),
                         [("három", "3", C), ("Tízezred", "0.0001", F)])

    def test_a_lone_glued_part_word_needs_the_lexicon_setting(self):
        for setting in ("glued_denominator_alone", "glued_denominator_alone_ambiguous"):
            lexicon = replace(load("hu"), **{setting: False})
            with self.subTest(setting=setting), patch("numtag.tagger.load", return_value=lexicon):
                mentions = tag_numbers("háromszázad része a klórénak", "hu")
                if setting == "glued_denominator_alone":
                    self.assertEqual(mentions, [])
                else:
                    self.assertEqual([(m.value, m.confidence) for m in mentions], [("1/300", 1.0)])

    def test_a_lone_glued_part_word_leaves_the_other_readings(self):
        # a count before it multiplies it, so the lone reading starts no span there
        self.assertEqual(read("egy kétszázad", "hu"), [("egy kétszázad", "0.005", F)])
        self.assertEqual(read("három egész egy tízezred", "hu"), [("három egész egy tízezred", "3.0001", D)])
        self.assertEqual(read("nulla egész kétezer-ötszáz milliomod", "hu"),
                         [("nulla egész kétezer-ötszáz milliomod", "0.0025", D)])
        self.assertEqual(read("egy milliomod", "hu"), [("egy milliomod", "0.000001", F)])
        # a part word under a hundred is no glued denominator; a bare "milliomod" has no count
        self.assertEqual(read("milliomod", "hu"), [])
        self.assertEqual(read("kétharmad része", "hu"), [("kétharmad", "2/3", F)])
        # 3/10 = 0.3 and 2/10 = 0.2, not 1/30 and 1/20
        self.assertEqual(read("háromtized", "hu"), [("háromtized", "0.3", F)])
        self.assertEqual(read("kéttized része", "hu"), [("kéttized", "0.2", F)])

    def test_a_count_after_a_range_hyphen_is_no_glued_multiplier(self):
        # hu.wikipedia, "Volfrám": a filament one or two hundredths of a
        # millimetre thick; AkH 12 §293 glues the count to the part word
        # before a noun ("háromnegyed óra"), so "kétszázad" is 2/100 = 0.02
        sentence = "Az izzólámpákban használt spirált egy-kétszázad milliméter vastagságú szálból készítik."
        self.assertEqual(read(sentence, "hu"), [("egy", "1", C), ("kétszázad", "0.02", F)])
        self.assertEqual(read("egy–kétszázad milliméter", "hu"), [("egy", "1", C), ("kétszázad", "0.02", F)])

    def test_a_whole_numerator_stays_out_of_parts_in_a_case(self):
        # after "tam" the part word comes in the locative and its count after
        # it ("iki tam onda beş (2,5)"); here the count is "iki min beş yüz",
        # 2500, so 2000/10^6 = 0.002 drops the 500
        self.assertNotIn("0.002", [m.value for m in tag_numbers("sıfır tam milyonda iki min beş yüz", "az")])

    def test_a_part_word_after_a_count_stays_singular(self):
        # 2/3; 3/4 = 0.75
        self.assertEqual(read("két harmad", "hu"), [("két harmad", "2/3", F)])
        self.assertEqual(read("üç çeyrek saat", "tr"), [("üç çeyrek", "0.75", F)])

    def test_a_lone_quarter_word_is_a_quarter(self):
        # TDK "çeyrek": "Dörtte bir" (1/4); "çeyrek saat" is a quarter of an
        # hour; a count before the word still sets the numerator: 1/4, 3/4
        for text in ("çeyrek", "çeyrek saat", "bir çeyrek"):
            with self.subTest(text=text):
                self.assertEqual([(m.value, m.confidence) for m in tag_numbers(text, "tr")], [("0.25", 0.4)])
        self.assertEqual(read("çeyrek saat", "tr"), [("çeyrek", "0.25", F)])
        self.assertEqual(read("üç çeyrek", "tr"), [("üç çeyrek", "0.75", F)])
        self.assertEqual([m.reasons for m in tag_numbers("çeyrek", "tr")], [frozenset({Reason.HOMOGRAPH})])

    def test_a_lone_quarter_reads_as_a_lone_half(self):
        self.assertEqual([(m.text, m.confidence) for m in tag_numbers("yarım saat", "tr")], [("yarım", 0.4)])
        self.assertEqual([(m.text, m.confidence) for m in tag_numbers("çeyrek saat", "tr")], [("çeyrek", 0.4)])

    def test_azerbaijani_decimal_words(self):
        # 2 + 5/10 = 2.5
        self.assertEqual(read("iki tam beş", "az"), [("iki tam beş", "2.5", D)])
        # the parts in the locative, then the count: 2 + 5/10 = 2.5; 2 + 15/100 = 2.15
        self.assertEqual(read("iki tam onda beş", "az"), [("iki tam onda beş", "2.5", D)])
        self.assertEqual(read("iki tam yüzdə on beş", "az"), [("iki tam yüzdə on beş", "2.15", D)])


class TestDayAndMonth(unittest.TestCase):
    def test_a_day_and_month_with_a_period_after_them_read_no_number(self):
        # en.wikipedia "Date and time notation in Finland": "20.10 represents
        # 8:10 pm and 20.10. represents 20 October"
        for text, lang in (("Se oli 24.12.", "fi"), ("3.5. Maanantaina", "fi"), ("20.10.", "fi"), ("klo 20.10", "fi"),
                           ("24.12. Pazartesi", "tr"), ("24.12. Esmaspäeval", "et")):
            with self.subTest(text=text):
                self.assertEqual(tag_numbers(text, lang), [])


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

    def test_a_word_with_another_meaning_after_a_sure_count_is_its_noun(self):
        # "öt hét" is five weeks; in "Egy hét hét napból áll." the second
        # "hét" follows a noun, so it stays a weak 7
        self.assertEqual(read("Öt hét múlva jövök vissza.", "hu"), [("Öt", "5", C)])
        self.assertEqual(read("5 hét", "hu"), [("5", "5", C)])
        self.assertEqual(self.confidence("Egy hét hét napból áll.", "hu"), [("Egy", False), ("hét", True)])
        self.assertEqual(self.confidence("öt, hét", "hu"), [("öt", False), ("hét", True)])

    def test_hat_is_also_the_verb_to_take_effect(self):
        # Wiktionary "hat", Verb: "to take effect", "to affect (on something
        # -ra)": weak at the end of a clause, after "nem" and before a -ra pronoun
        # The cues do not look further: "Tulajdonképpen hat, a hegyekben" counts six
        # places, "nem hat perc" six minutes and "hat és hét" is a list; the value
        # stays and the caller decides
        for text in ("A gyógyszer nem hat.", "a gyógyszer nem hat", "Nem hat azonnal.", "Ez a zene hat rám.",
                     "A hír mélyen hat ránk.", "Hogyan hat rájuk?", "Tulajdonképpen hat, a hegyekben",
                     "nem hat perc", "Nem hat órára kértem."):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.value, m.reasons) for m in tag_numbers(text, "hu")],
                                 [("hat", "6", frozenset({Reason.HOMOGRAPH}))])
        # before a noun it counts, and a case form is no verb form
        for text, word in (("hat óra", "hat"), ("Hat perc múlva indulunk.", "Hat"), ("hatkor kelek", "hatkor"),
                           ("Nem. Hat ember jött.", "Hat"),
                           ("hat ITF-tornán győzött", "hat"), ("Láttam hatot.", "hatot"), ("hattal", "hattal")):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.value, m.confidence) for m in tag_numbers(text, "hu")], [(word, "6", 1.0)])

    def test_hat_after_a_request_verb_or_alone_is_six(self):
        # right after a request verb "hat" is no verb: a finite verb does not
        # follow another finite verb in one clause
        for text in ("kérek hat", "Kérem hat", "legyen hat", "Legyen hat!", "állítsd hat", "tedd hat", "hat", "Hat"):
            with self.subTest(text=text):
                self.assertEqual([(m.value, m.confidence) for m in tag_numbers(text, "hu")], [("6", 1.0)])
        # with a full stop, or inside a clause, the end-of-clause cue holds
        for text in ("Hat.", "A válasz hat.", "a gyógyszer nem hat", "Nem kérek, hat."):
            with self.subTest(text=text):
                self.assertEqual([(m.value, m.confidence) for m in tag_numbers(text, "hu")][-1], ("6", 0.4))

    def test_hat_before_a_joiner_and_a_number_is_sure(self):
        # a joiner ends the clause unless a number follows it
        for text in ("hat és hét ember jött", "hat és 7 ember", "hat vagy hét", "hat meg hét", "hat-hét"):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.confidence) for m in tag_numbers(text, "hu")][0], ("hat", 1.0))
        # an article, an ordinal or a form with another meaning is no number after the joiner
        for text in ("hat és működik", "A szer hat és egyben gyógyít.", "A gyógyszer hat és egy kicsit segít.",
                     "A gyógyszer gyorsan hat és első alkalommal is."):
            with self.subTest(text=text):
                self.assertEqual(self.confidence(text, "hu")[0], ("hat", True))

    def test_hat_inside_a_number_is_no_verb(self):
        self.assertEqual(read("nem huszonhat", "hu"), [("huszonhat", "26", C)])

    def test_an_idiom_with_number_words_holds_no_number(self):
        # hu.wiktionary "one and all": "mindenki kivétel nélkül, egytől egyig"
        self.assertEqual(read("Egytől egyig mind ott voltak.", "hu"), [])
        self.assertEqual(read("egytől tízig", "hu"), [("egytől", "1", C), ("tízig", "10", C)])

    def test_the_same_word_inside_a_number_is_sure(self):
        # 100 x 1000 = 100000 in the partitive
        self.assertEqual(self.confidence("sataatuhatta", "fi"), [("sataatuhatta", False)])
        self.assertEqual(self.confidence("on dört", "tr"), [("on dört", False)])

    def test_an_inflected_homograph_is_weak(self):
        # each form is also another word: "for", "his", "him", "because of", "on",
        # "with him", "all of a sudden"
        self.assertEqual(self.confidence("sənin üçün", "az"), [("üçün", True)])
        self.assertEqual(self.confidence("Onun evi", "az"), [("Onun", True)])
        self.assertEqual(self.confidence("Onu gördüm.", "az"), [("Onu", True)])
        self.assertEqual(self.confidence("Bu yüzden geldim.", "tr"), [("yüzden", True)])
        self.assertEqual(self.confidence("Live on Stage", "tr"), [("on", True)])
        self.assertEqual(self.confidence("Onla geldim.", "tr"), [("Onla", True)])
        self.assertEqual(self.confidence("Birden yağmur başladı.", "tr"), [("Birden", True)])
        # "led" or "way"; "each other"; "while leading"
        self.assertEqual(self.confidence("Ta viis lapse kooli.", "et"), [("viis", True)])
        self.assertEqual(self.confidence("Nad aitavad üksteist.", "et"), [("üksteist", True)])
        self.assertEqual(self.confidence("Viies lapse kooli", "et"), [("Viies", True)])
        # "increasingly", "also", "formerly", "at once", "at first"
        for word in ("Egyre", "Egyben", "Egykor", "Egyből", "Elsőre"):
            self.assertEqual(self.confidence(f"{word} jobb.", "hu"), [(word, True)])
        # Wiktionary "egybe", ÉrtSz: "into one, as one"
        self.assertEqual(self.confidence("Összeraktuk egybe a darabokat.", "hu"), [("egybe", True)])
        # "together", "equally", "spruce", "I don't care"
        self.assertEqual(self.confidence("Laske yhteen.", "fi"), [("yhteen", True)])
        self.assertEqual(self.confidence("yhtä hyvä", "fi"), [("yhtä", True)])
        self.assertEqual(self.confidence("Kuusi kasvaa.", "fi"), [("Kuusi", True)])
        self.assertEqual(self.confidence("Viis siitä!", "fi"), [("Viis", True)])

    def test_the_homograph_inside_a_number_or_another_case_is_sure(self):
        # 3 x 100 = 300; 10 + 5 = 15; 2 x 100 = 200; 2 + 10 = 12; the other case
        # forms have no second meaning, but "egyet" is also an adverb
        self.assertEqual(self.confidence("üç yüz", "tr"), [("üç yüz", False)])
        self.assertEqual(self.confidence("on beş", "az"), [("on beş", False)])
        self.assertEqual(self.confidence("kakssada", "et"), [("kakssada", False)])
        self.assertEqual(self.confidence("kaksteist", "et"), [("kaksteist", False)])
        self.assertEqual(self.confidence("egyet", "hu"), [("egyet", True)])
        self.assertEqual(self.confidence("eggyel", "hu"), [("eggyel", False)])
        self.assertEqual(self.confidence("hat ember", "hu"), [("hat", False)])
        self.assertEqual(self.confidence("Kalelerden biri", "tr"), [("biri", False)])
        self.assertEqual(self.confidence("bin asker", "tr"), [("bin", False)])
        self.assertEqual(self.confidence("üçə", "az"), [("üçə", False)])
        self.assertEqual(self.confidence("viiest", "et"), [("viiest", False)])

    def test_an_article_before_a_noun_is_weak(self):
        self.assertEqual(self.confidence("bir elma aldım", "tr"), [("bir", True)])
        self.assertEqual(self.confidence("van egy almám", "hu"), [("egy", True)])


if __name__ == "__main__":
    unittest.main()
