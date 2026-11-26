"""Portuguese grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/pt-PT.json."""
import unittest

import pytest

from helpers import read, sure
from numtag import Form, Scale, tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def pt(text: str, **options) -> list[tuple[str, str, str]]:
    return read(text, "pt-PT", **options)


class TestBindingRulings(unittest.TestCase):
    def test_digits_after_the_first_group_count_only_a_scale_word(self):
        # 2 x 10^6 + 500 x 10^3 = 2500000; digits with no scale word after
        # them start a new number, so a year stays a year
        self.assertEqual(pt("2 milhões e 500 mil"), [("2 milhões e 500 mil", "2500000", C)])
        self.assertEqual(pt("3 milhões e 2021 foi pior"), [("3 milhões", "3000000", C), ("2021", "2021", C)])

    def test_mil_counts_the_whole_cardinal_before_a_collective(self):
        # (1000 + 2) x 12 = 12024
        self.assertEqual(pt("mil e duas dúzias"), [("mil e duas dúzias", "12024", C)])

    def test_a_collective_after_a_scale_numeral_with_no_joiner_starts_a_number(self):
        # Miro: 13000 and 2 x 100
        self.assertEqual(pt("treze mil duas centenas"), [("treze mil", "13000", C), ("duas centenas", "200", C)])
        self.assertEqual(pt("treze mil duas dúzias"), [("treze mil", "13000", C), ("duas dúzias", "24", C)])

    def test_a_place_collective_after_the_joiner_counts_only_its_group(self):
        # Miro: 13000 + 2 x 100
        self.assertEqual(pt("treze mil e duas centenas"), [("treze mil e duas centenas", "13200", C)])
        # 500 x 100 does not fit below 3000, so the whole cardinal counts
        # the collective: (3000 + 500) x 100
        self.assertEqual(pt("três mil e quinhentas centenas"), [("três mil e quinhentas centenas", "350000", C)])
        # (3000 + 2 x 100) x 10^6
        self.assertEqual(pt("três mil e duas centenas de milhões"),
                         [("três mil e duas centenas de milhões", "3200000000", C)])

    def test_after_milhao_the_collective_counts_only_the_cardinal_after_it(self):
        # 1000000 + 2 x 12 = 1000024
        self.assertEqual(pt("um milhão e duas dúzias"), [("um milhão e duas dúzias", "1000024", C)])

    def test_de_and_a_singular_scale_noun_do_not_multiply_a_collective(self):
        self.assertEqual(pt("uma dúzia de milhão"), [("uma dúzia", "12", C)])

    def test_a_collective_ends_its_number(self):
        # 1 x 12 = 12; 2 x 1000 x 12 = 24000
        self.assertEqual(pt("uma dúzia e duas mil dúzias"),
                         [("uma dúzia", "12", C), ("duas mil dúzias", "24000", C)])

    def test_de_and_a_collective_multiply_the_scale_noun(self):
        # 2 x 12 = 24; 1000000 x 12 = 12000000
        self.assertEqual(pt("duas dúzias e um milhão de dúzias"),
                         [("duas dúzias", "24", C), ("um milhão de dúzias", "12000000", C)])

    def test_counted_nouns_end_each_number(self):
        self.assertEqual(pt("comprou duas dúzias de ovos e ganhou um milhão de euros"),
                         [("duas dúzias", "24", C), ("um milhão", "1000000", C)])

    def test_a_multiplied_scale_noun_ends_its_number(self):
        # 2 x 1000000 x 12 = 24000000; 3 x 1000000 = 3000000
        self.assertEqual(pt("dois milhões de dúzias e três milhões"),
                         [("dois milhões de dúzias", "24000000", C), ("três milhões", "3000000", C)])


class TestHalves(unittest.TestCase):
    def test_a_half_after_a_collective_is_half_a_group(self):
        # 2 x 12 + 12 / 2 = 30
        self.assertEqual(pt("duas dúzias e meia"), [("duas dúzias e meia", "30", C)])

    def test_a_half_before_a_number_word_starts_a_new_number(self):
        # 2 x 12 = 24; 1000000 / 2 = 500000
        self.assertEqual(pt("duas dúzias e meio milhão"),
                         [("duas dúzias", "24", C), ("meio milhão", "500000", C)])

    def test_a_half_after_a_scale_noun_is_half_the_noun(self):
        # 1000000 + 1000000 / 2 = 1500000
        self.assertEqual(pt("um milhão e meio"), [("um milhão e meio", "1500000", C)])

    def test_de_and_a_collective_multiply_a_noun_and_its_half(self):
        # (10^6 + 10^6 / 2) x 12 = 18000000
        self.assertEqual(pt("um milhão e meio de dúzias"), [("um milhão e meio de dúzias", "18000000", C)])
        self.assertEqual(pt("um milhão e meio de euros"), [("um milhão e meio", "1500000", C)])

    def test_a_half_after_mil_milhoes_is_half_of_a_thousand_millions(self):
        # 2 x 10^9 + 10^9 / 2 = 2500000000
        self.assertEqual(pt("dois mil milhões e meio"), [("dois mil milhões e meio", "2500000000", C)])

    def test_a_half_after_mil_is_half_of_one(self):
        self.assertEqual(pt("mil e meio"), [("mil e meio", "1000.5", F)])

    def test_a_half_after_a_cardinal_is_half_of_one(self):
        self.assertEqual(pt("dois e meio"), [("dois e meio", "2.5", F)])

    def test_meia_duzia_and_duzia_e_meia(self):
        # 12 / 2 = 6; 12 + 6 = 18
        self.assertEqual(pt("meia dúzia"), [("meia dúzia", "6", C)])
        self.assertEqual(pt("dúzia e meia"), [("dúzia e meia", "18", C)])

    def test_meia_duzia_after_e_joins_the_number(self):
        # 100 + 6; 1000 + 6; 10^6 + 6; 10^6 / 2 + 6
        self.assertEqual(pt("cem e meia dúzia"), [("cem e meia dúzia", "106", C)])
        self.assertEqual(pt("mil e meia dúzia"), [("mil e meia dúzia", "1006", C)])
        self.assertEqual(pt("um milhão e meia dúzia"), [("um milhão e meia dúzia", "1000006", C)])
        self.assertEqual(pt("meio milhão e meia dúzia"), [("meio milhão e meia dúzia", "500006", C)])
        # 10^6 + 6; 2 x 12 = 24
        self.assertEqual(pt("um milhão e meia dúzia e duas dúzias"),
                         [("um milhão e meia dúzia", "1000006", C), ("duas dúzias", "24", C)])
        # a decimal ends its number, as before a half
        self.assertEqual(pt("dois vírgula cinco e meia dúzia"),
                         [("dois vírgula cinco", "2.5", D), ("meia dúzia", "6", C)])

    def test_a_half_before_a_unit_noun_is_half_the_unit(self):
        # "meio quilo" is half a kilo, so the million stays whole
        self.assertEqual(pt("um milhão e meio quilo"), [("um milhão", "1000000", C), ("meio", "0.5", F)])
        # 10^6 + 10^6 / 2 = 1500000
        self.assertEqual(pt("um milhão e meio foram gastos"), [("um milhão e meio", "1500000", C)])

    def test_a_half_alone_is_a_fraction_marked_ambiguous(self):
        # "meio" is also "middle", so a lone half gets a weak score
        mentions = tag_numbers("comprou meio quilo", "pt-PT")
        self.assertEqual([(m.text, m.value, m.kind.value) for m in mentions], [("meio", "0.5", F)])
        self.assertLess(mentions[0].confidence, 0.5)


class TestCollectivesAndScaleNouns(unittest.TestCase):
    def test_mil_is_a_numeral_and_needs_no_count(self):
        self.assertEqual(pt("mil"), [("mil", "1000", C)])

    def test_a_scale_noun_needs_a_count(self):
        self.assertEqual(pt("o milhão"), [])

    def test_milhar_is_a_scale_noun_of_a_thousand(self):
        # 2 x 1000 = 2000; 1000 + 500 = 1500
        self.assertEqual(pt("dois milhares"), [("dois milhares", "2000", C)])
        self.assertEqual(pt("um milhar e meio"), [("um milhar e meio", "1500", C)])

    def test_partitive_dos_does_not_multiply(self):
        self.assertEqual(pt("uma dezena dos milhares de manifestantes"), [("uma dezena", "10", C)])

    def test_a_collective_takes_de_and_a_plural_scale_noun(self):
        # 3 x 100 x 1000000 = 300000000
        self.assertEqual(pt("três centenas de milhões"), [("três centenas de milhões", "300000000", C)])

    def test_de_milhar_after_a_collective_names_the_thousands(self):
        # Priberam, "milhar", sense 3: the class of the thousands.
        # 2 x 10 x 1000; 3 x 100 x 1000; 6 x 1000; 2 x 100 x 1000 + 500
        self.assertEqual(pt("duas dezenas de milhar"), [("duas dezenas de milhar", "20000", C)])
        self.assertEqual(pt("três centenas de milhar de euros"), [("três centenas de milhar", "300000", C)])
        self.assertEqual(pt("meia dúzia de milhar"), [("meia dúzia de milhar", "6000", C)])
        self.assertEqual(pt("duas centenas de milhar e quinhentos"),
                         [("duas centenas de milhar e quinhentos", "200500", C)])
        # a count of a scale word starts a new number: 200000; 3 x 10^6
        self.assertEqual(pt("duas centenas de milhar e três milhões"),
                         [("duas centenas de milhar", "200000", C), ("três milhões", "3000000", C)])

    def test_dozens_after_de_milhar_count_as_after_a_scale_noun(self):
        # 2 x 10 x 1000 x 12 = 240000; 2 x 10 x 1000 + 3 x 12 = 20036
        self.assertEqual(pt("duas dezenas de milhar de dúzias"),
                         [("duas dezenas de milhar de dúzias", "240000", C)])
        self.assertEqual(pt("duas dezenas de milhar e três dúzias"),
                         [("duas dezenas de milhar e três dúzias", "20036", C)])

    def test_de_and_a_plural_collective_multiply_a_collective(self):
        # 12 x 12 = 144; 3 x 10 x 12 = 360
        self.assertEqual(pt("uma dúzia de dúzias"), [("uma dúzia de dúzias", "144", C)])
        self.assertEqual(pt("três dezenas de dúzias"), [("três dezenas de dúzias", "360", C)])

    def test_de_duzias_after_a_smaller_scale_noun_counts_only_its_group(self):
        # 10^12 + 2 x 10^6 x 12 = 1000024000000
        self.assertEqual(pt("um bilião e dois milhões de dúzias"),
                         [("um bilião e dois milhões de dúzias", "1000024000000", C)])
        # pt-BR short scale: 10^9 + 2 x 10^6 x 12 = 1024000000
        self.assertEqual(read("um bilhão e dois milhões de dúzias", "pt-BR"),
                         [("um bilhão e dois milhões de dúzias", "1024000000", C)])
        # 10^12 + (2 x 10^6 + 10^6 / 2) x 12 = 1000030000000
        self.assertEqual(pt("um bilião e dois milhões e meio de dúzias"),
                         [("um bilião e dois milhões e meio de dúzias", "1000030000000", C)])

    def test_a_singular_scale_noun_before_de_counts_one(self):
        self.assertEqual(pt("milhão de pessoas"), [("milhão", "1000000", C)])
        # only at the start of a number: 10^12; 10^6
        self.assertEqual(pt("um bilião e milhão de pessoas"),
                         [("um bilião", "1" + "0" * 12, C), ("milhão", "1000000", C)])

    def test_a_plural_with_no_count_is_no_number(self):
        for text in ("dúzias de ovos", "milhões de pessoas", "milhares de pessoas",
                     "centenas de pessoas"):
            with self.subTest(text=text):
                self.assertEqual(pt(text), [])

    def test_a_decimal_count_before_a_collective(self):
        # 2.5 x 12 = 30
        self.assertEqual(pt("2,5 dúzias"), [("2,5 dúzias", "30", C)])


    def test_a_plural_scale_noun_takes_no_count_of_one_or_a_half(self):
        # Squarisi: "O numeral ou o adjetivo que o modifica deve concordar com ele"
        self.assertEqual(pt("meio milhões de pessoas"), [("meio", "0.5", F)])
        # the lone "meio" keeps its own reading, as in "no meio da sala"
        self.assertEqual([m.confidence for m in tag_numbers("meio milhões de pessoas", "pt-PT")],
                         [m.confidence for m in tag_numbers("no meio da sala", "pt-PT")])
        self.assertEqual([m.confidence for m in tag_numbers("meio milhões de pessoas", "pt-PT")], [0.4])
        self.assertEqual(pt("um milhões de pessoas"), [])
        self.assertEqual(pt("meio milhão de pessoas"), [("meio milhão", "500000", C)])
        self.assertEqual(pt("mil e um milhões"), [("mil e um milhões", "1001000000", C)])
        # digits do not agree in number
        self.assertEqual(pt("1 milhões"), [("1 milhões", "1000000", C)])


class TestFractionOfAScale(unittest.TestCase):
    def test_a_fraction_of_a_scale_noun_is_that_part_of_it(self):
        # 1/4 x 10^6 = 250000; 3/4 x 10^6 = 750000; 1/4 x 10^3 = 250
        self.assertEqual(pt("um quarto de milhão"), [("um quarto de milhão", "250000", C)])
        self.assertEqual(pt("três quartos de milhão"), [("três quartos de milhão", "750000", C)])
        self.assertEqual(pt("um quarto de milhar"), [("um quarto de milhar", "250", C)])

    def test_the_article_of_the_scale_noun_is_part_of_it(self):
        # 2/3 x 10^6 and 1/3 x 10^6
        self.assertEqual(pt("dois terços de um milhão"), [("dois terços de um milhão", "2000000/3", F)])
        self.assertEqual(pt("um terço de milhão"), [("um terço de milhão", "1000000/3", F)])

    def test_the_number_ends_at_the_scale_noun(self):
        self.assertEqual(pt("um quarto de milhão de euros"), [("um quarto de milhão", "250000", C)])

    def test_the_quarter_is_sure_before_a_scale_noun(self):
        # "um quarto" alone is a room or a quarter, so it is not sure
        self.assertEqual(sure("um quarto de milhão", "pt-PT"), [("um quarto de milhão", "250000", 1.0)])
        self.assertEqual(sure("um quarto de hora", "pt-PT"), [("um quarto", "0.25", 0.4)])

    def test_pt_br_reads_the_short_scale(self):
        # 1/4 x 10^9 = 250000000; 1/4 x 10^6
        self.assertEqual(read("um quarto de bilhão", "pt-BR"), [("um quarto de bilhão", "250000000", C)])
        self.assertEqual(read("um quarto de milhão", "pt-BR"), [("um quarto de milhão", "250000", C)])
        self.assertEqual(read("dois terços de um milhão", "pt-BR"), [("dois terços de um milhão", "2000000/3", F)])

    def test_pt_pt_reads_the_long_scale(self):
        # 1/4 x 10^12 = 250000000000
        self.assertEqual(pt("um quarto de bilião"), [("um quarto de bilião", "250000000000", C)])

    def test_meio_milhao_is_unchanged(self):
        self.assertEqual(pt("meio milhão"), [("meio milhão", "500000", C)])

    def test_a_half_word_before_de_and_a_scale_noun_is_no_part_of_it(self):
        # "no meio de um milhão de pessoas": in the middle of a million people
        self.assertEqual(pt("no meio de um milhão de pessoas"), [("meio", "0.5", F), ("um milhão", "1000000", C)])

    def test_a_scale_noun_that_starts_a_longer_number_is_not_the_whole_part(self):
        # The grammar has no reading for a fraction of a compound number, so each
        # of these keeps the reading of two numbers: 1/3 and 1500; 1/4 and 1200; 3/4 and 10^9.
        self.assertEqual(pt("um terço de mil e quinhentos"), [("um terço", "1/3", F), ("mil e quinhentos", "1500", C)])
        self.assertEqual(pt("um quarto de mil e duzentos euros"),
                         [("um quarto", "0.25", F), ("mil e duzentos", "1200", C)])
        self.assertEqual(pt("três quartos de mil milhões"), [("três quartos", "0.75", F), ("mil milhões", "1000000000", C)])
        # constructed short phrases: a longer number after "de" keeps the two
        # readings of dev; 1/4 and 10^9, 1/4 and 10^12, 1/4 and 1500000
        self.assertEqual(pt("um quarto de milhar de milhões"),
                         [("um quarto", "0.25", F), ("milhar de milhões", "1000000000", C)])
        self.assertEqual(pt("um quarto de milhão de milhões"),
                         [("um quarto", "0.25", F), ("milhão de milhões", "1000000000000", C)])
        self.assertEqual(pt("um quarto de um milhão e meio"),
                         [("um quarto", "0.25", F), ("um milhão e meio", "1500000", C)])

    def test_mil_is_a_numeral_and_joins_no_fraction(self):
        # "mil" is no scale noun: a quarter, then 1000 euros; two quarters (2/4 = 0.5), then 1000
        self.assertEqual(pt("Reservou um quarto de mil euros por noite."), [("um quarto", "0.25", F), ("mil", "1000", C)])
        self.assertEqual(read("Reservou um quarto de mil reais por noite.", "pt-BR"),
                         [("um quarto", "0.25", F), ("mil", "1000", C)])
        self.assertEqual(pt("dois quartos de mil euros"), [("dois quartos", "0.5", F), ("mil", "1000", C)])

    def test_only_de_joins_a_fraction_to_a_scale_noun(self):
        self.assertEqual(pt("um quarto e um milhão"), [("um quarto", "0.25", F), ("um milhão", "1000000", C)])

    def test_a_plural_or_a_count_after_de_stays_apart(self):
        self.assertEqual(pt("um quarto de milhões de pessoas"), [("um quarto", "0.25", F)])
        self.assertEqual(pt("um quarto de dois milhões"), [("um quarto", "0.25", F), ("dois milhões", "2000000", C)])


class TestCardinals(unittest.TestCase):
    def test_tens_and_units_need_the_conjunction(self):
        self.assertEqual(pt("vinte e um"), [("vinte e um", "21", C)])
        self.assertEqual(pt("vinte um"), [("vinte", "20", C), ("um", "1", C)])

    def test_hundreds_join_the_rest_with_the_conjunction(self):
        # 100 + 20 + 3 = 123; 200 + 2 = 202
        self.assertEqual(pt("cento e vinte e três"), [("cento e vinte e três", "123", C)])
        self.assertEqual(pt("duzentas e duas"), [("duzentas e duas", "202", C)])

    def test_cento_stands_only_before_the_rest(self):
        self.assertEqual(pt("cento e um"), [("cento e um", "101", C)])
        self.assertEqual(pt("noventa por cento"), [("noventa", "90", C)])

    def test_the_conjunction_between_classes_is_optional(self):
        # 1000 + 800 + 90 + 2 = 1892; 1000 + 800 = 1800
        self.assertEqual(pt("mil oitocentos e noventa e dois"),
                         [("mil oitocentos e noventa e dois", "1892", C)])
        self.assertEqual(pt("mil e oitocentos"), [("mil e oitocentos", "1800", C)])

    def test_scales_must_descend(self):
        self.assertEqual(pt("mil mil"), [("mil", "1000", C), ("mil", "1000", C)])
        self.assertEqual(pt("dez mil mil"), [("dez mil", "10000", C), ("mil", "1000", C)])
        # a second group of the same scale starts a new number, also after "e"
        self.assertEqual(pt("dez mil e mil"), [("dez mil", "10000", C), ("mil", "1000", C)])
        self.assertEqual(pt("duzentos mil e mil"), [("duzentos mil", "200000", C), ("mil", "1000", C)])

    def test_a_count_belongs_to_the_scale_word_after_it(self):
        self.assertEqual(pt("dois mil e três mil"), [("dois mil", "2000", C), ("três mil", "3000", C)])
        self.assertEqual(pt("entre dois milhões e três milhões"),
                         [("dois milhões", "2000000", C), ("três milhões", "3000000", C)])

    def test_a_cardinal_counts_a_larger_scale_noun(self):
        # (1000 + 500) x 10^6; (2000 + 500) x 10^6; (1000 + 1) x 10^6
        self.assertEqual(pt("mil e quinhentos milhões de euros"),
                         [("mil e quinhentos milhões", "1500000000", C)])
        self.assertEqual(pt("dois mil e quinhentos milhões"),
                         [("dois mil e quinhentos milhões", "2500000000", C)])
        # 1500 x 10^6 + 300 x 10^3 + 1 = 1500300001
        self.assertEqual(pt("mil e quinhentos milhões trezentos mil e um"),
                         [("mil e quinhentos milhões trezentos mil e um", "1500300001", C)])

    def test_a_half_scale_noun_sums_with_the_groups_after_it(self):
        # 10^6 / 2 + 200 x 10^3 = 700000, as "um milhão e duzentos mil"
        self.assertEqual(pt("meio milhão e duzentos mil"), [("meio milhão e duzentos mil", "700000", C)])

    def test_only_a_cardinal_with_mil_counts_a_larger_scale_noun(self):
        # 10^6; 2 x 10^9 (short scale)
        self.assertEqual(read("entre um milhão e dois bilhões", "pt-BR"),
                         [("um milhão", "1000000", C), ("dois bilhões", "2000000000", C)])
        # 2 x 10^6; 3 x 10^12 (long scale)
        self.assertEqual(pt("dois milhões e três biliões"),
                         [("dois milhões", "2000000", C), ("três biliões", "3" + "0" * 12, C)])
        self.assertEqual(pt("um milhão e um bilião"),
                         [("um milhão", "1000000", C), ("um bilião", "1" + "0" * 12, C)])
        # "milhão" closes its group: 10^6; 100 x 10^9 (short scale)
        self.assertEqual(read("um milhão e cem bilhões", "pt-BR"),
                         [("um milhão", "1000000", C), ("cem bilhões", "1" + "0" * 11, C)])
        self.assertEqual(read("um milhão bilhões", "pt-BR"), [("um milhão", "1000000", C)])
        # 3 x 10^12 + 500 x 10^3 x 10^6 = 3500000000000
        self.assertEqual(pt("três biliões e quinhentos mil milhões"),
                         [("três biliões e quinhentos mil milhões", "35" + "0" * 11, C)])

    def test_a_group_fits_below_the_digits_of_the_count_before_it(self):
        # 1100 x 10^6 leaves eight zeros; 100 x 10^6 has nine digits
        self.assertEqual(pt("mil e cem milhões e cem milhões"),
                         [("mil e cem milhões", "1100000000", C), ("cem milhões", "100000000", C)])
        # 1500 x 10^6 leaves eight zeros; 600 x 10^6 has nine digits
        self.assertEqual(pt("mil e quinhentos milhões e seiscentos milhões"),
                         [("mil e quinhentos milhões", "1500000000", C), ("seiscentos milhões", "600000000", C)])
        # pt-BR short scale: 1100 x 10^9 leaves eleven zeros; 100 x 10^9 has twelve digits
        self.assertEqual(read("mil e cem bilhões e cem bilhões", "pt-BR"),
                         [("mil e cem bilhões", "11" + "0" * 11, C), ("cem bilhões", "1" + "0" * 11, C)])
        # 2000 x 10^6 leaves nine zeros: 2 x 10^9 + 500 x 10^6 = 2500000000
        self.assertEqual(pt("dois mil milhões e quinhentos milhões"),
                         [("dois mil milhões e quinhentos milhões", "2500000000", C)])
        # a half of 10^6 leaves the place of 10^6: 500000 + 700000 = 1200000
        self.assertEqual(pt("meio milhão e setecentos mil"), [("meio milhão e setecentos mil", "1200000", C)])

    def test_a_count_of_several_words_after_a_group_starts_a_new_number(self):
        # 10^9; 1500 x 10^6
        self.assertEqual(pt("entre mil milhões e mil e quinhentos milhões"),
                         [("mil milhões", "1" + "0" * 9, C), ("mil e quinhentos milhões", "15" + "0" * 8, C)])
        # 2 x 10^6; 1500 x 10^6
        self.assertEqual(pt("entre dois milhões e mil e quinhentos milhões"),
                         [("dois milhões", "2000000", C), ("mil e quinhentos milhões", "15" + "0" * 8, C)])
        # 10^12 + 1500 x 10^6 = 1001500000000; 3 x 10^6 + 1000 + 200 = 3001200
        self.assertEqual(pt("um bilião e mil e quinhentos milhões"),
                         [("um bilião e mil e quinhentos milhões", "1001500000000", C)])
        self.assertEqual(pt("três milhões e mil e duzentos"), [("três milhões e mil e duzentos", "3001200", C)])

    def test_a_count_below_a_thousand_belongs_to_the_scale_word_after_it(self):
        # 10^6; 25 x 10^6
        self.assertEqual(pt("entre um milhão e vinte e cinco milhões de euros"),
                         [("um milhão", "1000000", C), ("vinte e cinco milhões", "25000000", C)])
        # 20 x 1000; 25 x 1000
        self.assertEqual(pt("entre vinte mil e vinte e cinco mil euros"),
                         [("vinte mil", "20000", C), ("vinte e cinco mil", "25000", C)])
        # pt-BR short scale: 10^9; 23 x 10^9
        self.assertEqual(read("entre um bilhão e vinte e três bilhões", "pt-BR"),
                         [("um bilhão", "1" + "0" * 9, C), ("vinte e três bilhões", "23" + "0" * 9, C)])
        # 2 x 10^6 + 25 x 1000 = 2025000; 10^6 + 25 = 1000025
        self.assertEqual(pt("dois milhões e vinte e cinco mil"), [("dois milhões e vinte e cinco mil", "2025000", C)])
        self.assertEqual(pt("um milhão e vinte e cinco"), [("um milhão e vinte e cinco", "1000025", C)])
        # with no range cue too: 10^6; 25 x 10^6, and 2 x 1000; 25 x 1000
        self.assertEqual(pt("um milhão e vinte e cinco milhões"),
                         [("um milhão", "1000000", C), ("vinte e cinco milhões", "25000000", C)])
        self.assertEqual(pt("dois mil e vinte e cinco mil"),
                         [("dois mil", "2000", C), ("vinte e cinco mil", "25000", C)])

    def test_a_well_formed_count_with_mil_e_counts_a_larger_noun(self):
        # Cunha & Cintra, p. 372, and Ciberdúvidas 34389: "e" follows "mil"
        # before a round hundred or a class that begins with a zero.
        # (2000 + 300) x 10^6 = 2300000000; (5000 + 67) x 10^6 = 5067000000
        self.assertEqual(pt("dois mil e trezentos milhões"),
                         [("dois mil e trezentos milhões", "2300000000", C)])
        self.assertEqual(pt("cinco mil e sessenta e sete milhões"),
                         [("cinco mil e sessenta e sete milhões", "5067000000", C)])
        # (500000 + 3) x 10^6 = 500003000000
        self.assertEqual(pt("quinhentos mil e três milhões"),
                         [("quinhentos mil e três milhões", "500003000000", C)])
        # the whole part 500 is a round hundred: 1500.5 x 10^6 = 1500500000
        self.assertEqual(pt("mil e quinhentos vírgula cinco milhões"),
                         [("mil e quinhentos vírgula cinco milhões", "1500500000", C)])
        # "mil e cento e vinte" is not well formed: 1000; 120 x 10^6
        self.assertEqual(pt("mil e cento e vinte milhões"),
                         [("mil", "1000", C), ("cento e vinte milhões", "120000000", C)])

    def test_a_group_after_a_compound_count_needs_room(self):
        # 1001 x 10^6 leaves six digits; "um milhão" has seven: 1001000000; 1000000
        self.assertEqual(pt("mil e um milhões e um milhão"),
                         [("mil e um milhões", "1001000000", C), ("um milhão", "1000000", C)])
        # "mil e quinhentos e dois" is not well formed, so the number ends at
        # the round hundred; 1500 leaves two digits, "dois mil" has four
        self.assertEqual(pt("mil e quinhentos e dois mil"),
                         [("mil e quinhentos", "1500", C), ("dois mil", "2000", C)])

    def test_a_singular_scale_noun_takes_only_the_count_one(self):
        # a scale noun agrees in number with its count: 100000; 10^6
        self.assertEqual(pt("cem mil e um milhão"),
                         [("cem mil", "100000", C), ("um milhão", "1000000", C)])
        self.assertEqual(pt("mil e um milhão"), [("mil", "1000", C), ("um milhão", "1000000", C)])
        self.assertEqual(pt("passou de oitocentos mil e um milhão para dois milhões"),
                         [("oitocentos mil", "800000", C), ("um milhão", "1000000", C),
                          ("dois milhões", "2000000", C)])
        self.assertEqual(read("cem mil e um bilhão", "pt-BR"),
                         [("cem mil", "100000", C), ("um bilhão", "1000000000", C)])
        # (1000 + 1) x 10^6, plural
        self.assertEqual(pt("mil e um milhões"), [("mil e um milhões", "1001000000", C)])
        # a count that the noun does not take stays a number
        self.assertEqual(pt("dois milhão"), [("dois", "2", C)])
        self.assertEqual(pt("meio milhão"), [("meio milhão", "500000", C)])

    def test_the_first_number_takes_a_plain_group_before_a_compound_count(self):
        # 10^6 + 500 x 1000 = 1500000; 2 x 10^6
        self.assertEqual(pt("um milhão e quinhentos mil e dois milhões"),
                         [("um milhão e quinhentos mil", "1500000", C), ("dois milhões", "2000000", C)])
        # with nothing before it, the compound count reads: (200000 + 2) x 10^6
        self.assertEqual(pt("duzentos mil e dois milhões"),
                         [("duzentos mil e dois milhões", "200002000000", C)])

    def test_a_range_cue_never_reads_worse_than_no_cue(self):
        # with no cue: 1500 and 2000, which has fewer significant digits
        # than the split after "mil", 1000 and 502000
        self.assertEqual(pt("entre mil e quinhentos e dois mil"),
                         [("mil e quinhentos", "1500", C), ("dois mil", "2000", C)])

    def test_a_range_joiner_after_the_hundred_splits_before_a_scale_noun(self):
        # "cem e um milhão" is no number (a singular scale noun counts only
        # one), so the range is 100 and 10^6, not 101 and a lone "milhão"
        self.assertEqual(pt("entre cem e um milhão de pessoas"),
                         [("cem", "100", C), ("um milhão", "1000000", C)])
        self.assertEqual(read("entre cien y un millón de personas", "es"),
                         [("cien", "100", C), ("un millón", "1000000", C)])
        # a number inside the hundreds still reads whole: 60 + 7 = 67, x 10^6
        self.assertEqual(pt("entre cinco mil e sessenta e sete milhões"),
                         [("cinco mil", "5000", C), ("sessenta e sete milhões", "67000000", C)])

    def test_a_range_cue_ends_the_first_number_at_the_range_joiner(self):
        # 100 x 1000 = 100000; 10^6
        self.assertEqual(pt("entre cem mil e um milhão de euros"),
                         [("cem mil", "100000", C), ("um milhão", "1000000", C)])
        self.assertEqual(read("entre cem mil e um milhão de reais", "pt-BR"),
                         [("cem mil", "100000", C), ("um milhão", "1000000", C)])
        # 2 x 10^6 + 500 x 1000 = 2500000; 3 x 10^6
        self.assertEqual(pt("entre dois milhões e quinhentos mil e três milhões"),
                         [("dois milhões e quinhentos mil", "2500000", C), ("três milhões", "3000000", C)])
        # 200 x 1000 = 200000; 100 x 10^6
        self.assertEqual(pt("entre duzentos mil e cem milhões"),
                         [("duzentos mil", "200000", C), ("cem milhões", "100000000", C)])
        # the joiner of "sessenta e sete" splits nothing: 5000; 67 x 10^6
        self.assertEqual(pt("entre cinco mil e sessenta e sete milhões"),
                         [("cinco mil", "5000", C), ("sessenta e sete milhões", "67000000", C)])
        # 10^9 is less than 1500 x 10^6; 1000001000 is not less than 500 x 10^6
        self.assertEqual(pt("entre mil milhões e mil e quinhentos milhões"),
                         [("mil milhões", "1" + "0" * 9, C), ("mil e quinhentos milhões", "15" + "0" * 8, C)])
        self.assertEqual(pt("entre dez e vinte"), [("dez", "10", C), ("vinte", "20", C)])
        # the joiners of "cento e vinte e cinco" split nothing: 125 x 1000; 200 x 1000
        self.assertEqual(pt("entre cento e vinte e cinco mil e duzentos mil"),
                         [("cento e vinte e cinco mil", "125000", C), ("duzentos mil", "200000", C)])

    def test_the_range_limits_with_the_fewest_digits_win(self):
        # 2000000 and 1500000000 (3 significant digits), not 2001000 and
        # 500000000 (5): both left values are less than their right values
        self.assertEqual(pt("entre dois milhões e mil e quinhentos milhões"),
                         [("dois milhões", "2000000", C), ("mil e quinhentos milhões", "15" + "0" * 8, C)])

    def test_two_numbers_split_where_the_fewest_digits_are(self):
        # 1000 x 10^6 = 1000000000 and 1500 x 10^6 = 1500000000: 1 + 2 = 3
        # significant digits, against 1000001000 and 500000000: 7 + 1 = 8
        self.assertEqual(pt("mil milhões e mil e quinhentos milhões"),
                         [("mil milhões", "1" + "0" * 9, C), ("mil e quinhentos milhões", "15" + "0" * 8, C)])
        # "mil quinhentos" is no count: a round hundred needs "e"
        self.assertEqual(pt("mil milhões e mil quinhentos milhões"),
                         [("mil milhões e mil", "1000001000", C), ("quinhentos milhões", "5" + "0" * 8, C)])
        # 1500000 and 2000000: 2 + 1 = 3, against 1000000 and 500002000000: 1 + 6 = 7
        self.assertEqual(pt("um milhão e quinhentos mil e dois milhões"),
                         [("um milhão e quinhentos mil", "1500000", C), ("dois milhões", "2000000", C)])
        # 2001000 and 3000000 (4 + 1 = 5) tie with 2000000 and 1003000000
        # (1 + 4 = 5): the longer first number wins
        self.assertEqual(pt("dois milhões e mil e três milhões"),
                         [("dois milhões e mil", "2001000", C), ("três milhões", "3000000", C)])
        # One number beats two: (200000 + 2) x 10^6
        self.assertEqual(pt("duzentos mil e dois milhões"),
                         [("duzentos mil e dois milhões", "200002000000", C)])

    def test_a_scale_word_counts_no_group_with_a_larger_scale_word(self):
        # 10^12 + 50 x 10^9 + 1000 + 40: "mil" counts no billions
        self.assertEqual(read("um trilhão cinquenta bilhões mil e quarenta", "pt-BR"),
                         [("um trilhão cinquenta bilhões mil e quarenta", "1050000001040", C)])
        # 10^18 + 50 x 10^12 + 1000
        self.assertEqual(pt("um trilião cinquenta biliões e mil"),
                         [("um trilião cinquenta biliões e mil", "1000050000000001000", C)])

    def test_a_joiner_at_the_end_of_the_words_splits_nothing(self):
        self.assertEqual(pt("entre dois e"), [("dois", "2", C)])
        self.assertEqual(pt("dois milhões e"), [("dois milhões", "2000000", C)])
        self.assertEqual(pt("entre -1 e"), [("-1", "-1", C)])
        self.assertEqual(pt("entre 5 e"), [("5", "5", C)])
        # digits glued to a word are dropped, so "e20" leaves a final joiner
        self.assertEqual(pt("entre 15 e20"), [("15", "15", C)])

    def test_with_no_smaller_left_side_a_range_cue_keeps_one_number(self):
        # 1000 is not less than 500: 1500
        self.assertEqual(pt("entre mil e quinhentos euros"), [("mil e quinhentos", "1500", C)])

    def test_mil_and_a_count_with_no_e_count_a_larger_noun(self):
        # (2000 + 350) x 10^6. A round hundred needs "e", so "mil
        # quinhentos" counts no noun.
        self.assertEqual(pt("mil quinhentos milhões"),
                         [("mil", "1000", C), ("quinhentos milhões", "500000000", C)])
        self.assertEqual(pt("dois mil trezentos e cinquenta milhões"),
                         [("dois mil trezentos e cinquenta milhões", "2350000000", C)])

    def test_a_scale_noun_after_a_group_starts_a_new_number(self):
        # 10^9; 2 x 10^9
        self.assertEqual(pt("entre mil milhões e dois mil milhões de euros"),
                         [("mil milhões", "1" + "0" * 9, C), ("dois mil milhões", "2" + "0" * 9, C)])
        self.assertEqual(pt("mil milhões e mil milhões"),
                         [("mil milhões", "1" + "0" * 9, C), ("mil milhões", "1" + "0" * 9, C)])
        # 2 x 10^12; 1000 x 10^12
        self.assertEqual(pt("dois biliões e mil biliões"),
                         [("dois biliões", "2" + "0" * 12, C), ("mil biliões", "1" + "0" * 15, C)])
        # pt-BR short scale: 10^9; 2000 x 10^6
        self.assertEqual(read("um bilhão e dois mil milhões", "pt-BR"),
                         [("um bilhão", "1000000000", C), ("dois mil milhões", "2000000000", C)])

    def test_two_units_are_two_numbers(self):
        self.assertEqual(pt("dois três"), [("dois", "2", C), ("três", "3", C)])

    def test_a_long_number(self):
        # 2 x 10^9 + 300 x 10^3 + 45 = 2000300045
        self.assertEqual(pt("dois mil milhões trezentos mil e quarenta e cinco"),
                         [("dois mil milhões trezentos mil e quarenta e cinco", "2000300045", C)])

    def test_punctuation_ends_a_number(self):
        self.assertEqual(pt("mil, duzentos"), [("mil", "1000", C), ("duzentos", "200", C)])


class TestJoinerBeforeTheLastGroup(unittest.TestCase):
    """A last group below a hundred or a round hundred takes "e"; without it
    the group starts a new number (Miro; Cunha & Cintra, p. 372: "1800 = mil
    e oitocentos"; Teyssier, pp. 181-182: "1.030: mil e trinta"). An "e"
    before any other group is optional."""

    def test_a_last_round_group_with_no_e_starts_a_new_number(self):
        for lang in ("pt-PT", "pt-BR"):
            with self.subTest(lang=lang):
                self.assertEqual(read("mil duzentos", lang), [("mil", "1000", C), ("duzentos", "200", C)])
                self.assertEqual(read("mil trinta", lang), [("mil", "1000", C), ("trinta", "30", C)])
                self.assertEqual(read("dois mil cem", lang), [("dois mil", "2000", C), ("cem", "100", C)])
                self.assertEqual(read("cem mil um", lang), [("cem mil", "100000", C), ("um", "1", C)])
                self.assertEqual(read("dois milhões quinhentos mil", lang),
                                 [("dois milhões", "2000000", C), ("quinhentos mil", "500000", C)])

    def test_a_last_round_group_after_e_joins(self):
        for lang in ("pt-PT", "pt-BR"):
            with self.subTest(lang=lang):
                self.assertEqual(read("mil e duzentos", lang), [("mil e duzentos", "1200", C)])
                self.assertEqual(read("mil e trinta", lang), [("mil e trinta", "1030", C)])
                self.assertEqual(read("dois mil e cem", lang), [("dois mil e cem", "2100", C)])
                self.assertEqual(read("cem mil e um", lang), [("cem mil e um", "100001", C)])
                self.assertEqual(read("dois milhões e quinhentos mil", lang),
                                 [("dois milhões e quinhentos mil", "2500000", C)])
                # the sources' own examples: 1892, 1800, 4226, 1400
                self.assertEqual(read("mil oitocentos e noventa e dois", lang),
                                 [("mil oitocentos e noventa e dois", "1892", C)])
                self.assertEqual(read("mil e oitocentos", lang), [("mil e oitocentos", "1800", C)])
                self.assertEqual(read("quatro mil duzentos e vinte e seis", lang),
                                 [("quatro mil duzentos e vinte e seis", "4226", C)])
                self.assertEqual(read("mil e quatrocentos", lang), [("mil e quatrocentos", "1400", C)])

    def test_an_e_before_any_other_group_is_optional(self):
        # 1000 + 204, with or without "e"
        self.assertEqual(pt("mil duzentos e quatro"), [("mil duzentos e quatro", "1204", C)])
        self.assertEqual(pt("mil e duzentos e quatro"), [("mil e duzentos e quatro", "1204", C)])
        # 2000000 + 500000 + 4: the round group is not the last
        self.assertEqual(pt("dois milhões quinhentos mil e quatro"),
                         [("dois milhões quinhentos mil e quatro", "2500004", C)])

    def test_the_gulbenkian_examples(self):
        # Gramática do Português (Gulbenkian), pp. 932-933: "e" joins the two
        # rightmost classes that are not zero when the second ends in two
        # zeros or begins with a zero; elsewhere it is left out.
        for lang in ("pt-PT", "pt-BR"):
            with self.subTest(lang=lang):
                # 2000000 + 300 x 1000; 2000000 + 7 x 1000; 2000000 + 500
                self.assertEqual(read("dois milhões e trezentos mil", lang),
                                 [("dois milhões e trezentos mil", "2300000", C)])
                self.assertEqual(read("dois milhões e sete mil", lang), [("dois milhões e sete mil", "2007000", C)])
                self.assertEqual(read("dois milhões e quinhentos", lang), [("dois milhões e quinhentos", "2000500", C)])
                # 2000000 + 236 x 1000 + 321
                text = "dois milhões duzentos e trinta e seis mil trezentos e vinte e um"
                self.assertEqual(read(text, lang), [(text, "2236321", C)])
                # 1000000 + 200 x 1000 + 300, with or without the first "e"
                self.assertEqual(read("um milhão duzentos mil e trezentos", lang),
                                 [("um milhão duzentos mil e trezentos", "1200300", C)])
                self.assertEqual(read("um milhão e duzentos mil e trezentos", lang),
                                 [("um milhão e duzentos mil e trezentos", "1200300", C)])

    def test_a_comma_links_only_a_smaller_class(self):
        # Ciberdúvidas 8981: every example puts the larger class before the
        # comma ("noventa e dois milhões, quinhentos e vinte e um mil")
        self.assertEqual(pt("2 mil, milhões de pessoas"), [("2 mil", "2000", C)])
        self.assertEqual(pt("dois mil, milhões de pessoas"), [("dois mil", "2000", C)])
        self.assertEqual(pt("três mil, mil e quinhentos"), [("três mil", "3000", C), ("mil e quinhentos", "1500", C)])
        self.assertEqual(pt("dois milhões, mil e quinhentos"), [("dois milhões, mil e quinhentos", "2001500", C)])

    def test_a_comma_after_a_scale_word_stands_between_two_classes(self):
        # Gulbenkian, pp. 932-933: "2 236 321 – dois milhões, duzentos e
        # trinta e seis mil trezentos e vinte e um"
        text = "dois milhões, duzentos e trinta e seis mil trezentos e vinte e um"
        for lang in ("pt-PT", "pt-BR"):
            with self.subTest(lang=lang):
                self.assertEqual(read(text, lang), [(text, "2236321", C)])
        # 1000 + 250
        self.assertEqual(pt("mil, duzentos e cinquenta"), [("mil, duzentos e cinquenta", "1250", C)])
        # the last group needs "e" all the same, and a comma after a word
        # that is no scale word, or before "e", still ends the number
        self.assertEqual(pt("dois milhões, trezentos mil"),
                         [("dois milhões", "2000000", C), ("trezentos mil", "300000", C)])
        self.assertEqual(pt("dois milhões, três"), [("dois milhões", "2000000", C), ("três", "3", C)])
        self.assertEqual(pt("dois mil, três mil"), [("dois mil", "2000", C), ("três mil", "3000", C)])
        self.assertEqual(pt("vinte, trinta e um"), [("vinte", "20", C), ("trinta e um", "31", C)])
        self.assertEqual(pt("dois, mil"), [("dois", "2", C), ("mil", "1000", C)])
        self.assertEqual(pt("vigésimo, primeiro"), [("vigésimo", "20", O), ("primeiro", "1", O)])
        # a comma with no space after it is no class separator
        self.assertEqual(pt("dois milhões,duzentos e trinta e seis mil"),
                         [("dois milhões", "2000000", C), ("duzentos e trinta e seis mil", "236000", C)])
        self.assertEqual(pt("dois milhões, e trezentos mil"),
                         [("dois milhões", "2000000", C), ("trezentos mil", "300000", C)])

    def test_a_last_count_of_a_thousand_or_more_joins_with_no_e(self):
        # 10^12 + 1500 x 10^6: the count 1500 is neither below a hundred
        # nor a round hundred
        self.assertEqual(pt("um bilião mil e quinhentos milhões"),
                         [("um bilião mil e quinhentos milhões", "1001500000000", C)])
        # 10^12 + 2000 x 10^6
        self.assertEqual(pt("um bilião dois mil milhões"), [("um bilião dois mil milhões", "1002000000000", C)])

    def test_a_collective_after_a_last_group_with_no_e(self):
        # 1000; 200 x 12
        self.assertEqual(pt("mil duzentas dúzias"), [("mil", "1000", C), ("duzentas dúzias", "2400", C)])

    def test_a_range_cue_takes_the_joiner_rule(self):
        # 1200 < 2000
        self.assertEqual(pt("entre mil e duzentos e dois mil"),
                         [("mil e duzentos", "1200", C), ("dois mil", "2000", C)])
        # "mil duzentos" is no number, so the first number is 1000, and
        # "duzentos e dois" counts "mil": 202000
        self.assertEqual(pt("entre mil duzentos e dois mil"),
                         [("mil", "1000", C), ("duzentos e dois mil", "202000", C)])
        # 2500000 < 3000000
        self.assertEqual(pt("entre dois milhões e quinhentos mil e três milhões"),
                         [("dois milhões e quinhentos mil", "2500000", C), ("três milhões", "3000000", C)])
        # no "e" before "quinhentos mil": the first number is 2000000, and
        # the well-formed "quinhentos mil e três" counts "milhões"
        self.assertEqual(pt("entre dois milhões quinhentos mil e três milhões"),
                         [("dois milhões", "2000000", C), ("quinhentos mil e três milhões", "500003000000", C)])


class TestScale(unittest.TestCase):
    def test_pt_pt_reads_the_long_scale(self):
        self.assertEqual(pt("um bilião"), [("um bilião", "1" + "0" * 12, C)])
        self.assertEqual(pt("um bilhão"), [("um bilhão", "1" + "0" * 12, C)])
        self.assertEqual(pt("mil milhões"), [("mil milhões", "1" + "0" * 9, C)])

    def test_pt_br_reads_the_short_scale(self):
        self.assertEqual(read("um bilhão", "pt-BR"), [("um bilhão", "1" + "0" * 9, C)])
        self.assertEqual(read("um bilião", "pt-BR"), [("um bilião", "1" + "0" * 9, C)])

    def test_the_scale_option_overrides_the_language(self):
        self.assertEqual(pt("um bilião", scale="short"), [("um bilião", "1" + "0" * 9, C)])

    def test_the_tenth_illion(self):
        # long scale 10^(6 x 10); short scale 10^(3 x 10 + 3)
        self.assertEqual(pt("um decilião")[0][1], "1" + "0" * 60)
        self.assertEqual(read("um decilhão", "pt-BR")[0][1], "1" + "0" * 33)

    def test_illions_past_the_tenth(self):
        # long scale 10^(6 x 19) and 10^(6 x 100); short scale 10^(3 x 11 + 3)
        self.assertEqual(pt("um novendecilião")[0][1], "1" + "0" * 114)
        self.assertEqual(pt("dois centiliões")[0][1], "2" + "0" * 600)
        self.assertEqual(read("um undecilhão", "pt-BR")[0][1], "1" + "0" * 36)

    def test_a_bare_pt_tag_reads_pt_pt(self):
        self.assertEqual(read("um bilião", "pt")[0][1], "1" + "0" * 12)
        self.assertEqual(read("um bilião", "pt_br")[0][1], "1" + "0" * 9)


class TestNumberScale(unittest.TestCase):
    def scales(self, text, lang="pt-PT", **options):
        return [(m.text, m.value, m.number_scale) for m in tag_numbers(text, lang, **options)]

    def test_a_billion_class_word_names_the_scale_of_its_value(self):
        self.assertEqual(self.scales("um bilião"), [("um bilião", "1" + "0" * 12, Scale.LONG)])
        self.assertEqual(self.scales("um bilhão"), [("um bilhão", "1" + "0" * 12, Scale.LONG)])
        self.assertEqual(self.scales("um bilhão", "pt-BR"), [("um bilhão", "1" + "0" * 9, Scale.SHORT)])
        self.assertEqual(self.scales("2 biliões"), [("2 biliões", "2" + "0" * 12, Scale.LONG)])
        # 3 x 10^12 + 500 x 10^9 = 3500000000000
        self.assertEqual(self.scales("três biliões e quinhentos mil milhões"),
                         [("três biliões e quinhentos mil milhões", "35" + "0" * 11, Scale.LONG)])

    def test_an_ordinal_scale_word_names_the_scale(self):
        mentions = tag_numbers("o bilionésimo visitante", "pt-PT")
        self.assertEqual([(m.value, m.kind.value, m.number_scale) for m in mentions],
                         [("1" + "0" * 12, O, Scale.LONG)])

    def test_the_scale_option_shows_in_the_mention(self):
        self.assertEqual(self.scales("um bilião", scale=Scale.SHORT),
                         [("um bilião", "1" + "0" * 9, Scale.SHORT)])

    def test_a_value_that_is_the_same_in_both_scales_has_no_scale(self):
        for text in ("um milhão", "mil milhões", "dois mil", "1000000000", "vinte e um",
                     "dois terços", "vigésimo primeiro", "duas dúzias"):
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.number_scale) for m in tag_numbers(text, "pt-PT")],
                                 [(text, None)])


class TestDecimals(unittest.TestCase):
    def test_a_decimal_after_a_scale_noun_needs_the_marker(self):
        self.assertEqual(pt("um milhão vírgula cinco"), [("um milhão vírgula cinco", "1000000.5", D)])

    def test_each_word_after_the_marker_gives_its_digits(self):
        self.assertEqual(pt("zero vírgula zero cinco"), [("zero vírgula zero cinco", "0.05", D)])
        self.assertEqual(pt("dois vírgula vinte e cinco"), [("dois vírgula vinte e cinco", "2.25", D)])
        self.assertEqual(pt("zero vírgula dois cinco"), [("zero vírgula dois cinco", "0.25", D)])

    def test_the_fractional_part_follows_the_grammar_of_the_whole_part(self):
        # "cem" never follows units in a cardinal, so the decimal ends
        # before it: 0.25 and 100, not 0.251
        self.assertEqual(pt("zero vírgula vinte e cinco cem"),
                         [("zero vírgula vinte e cinco", "0.25", D), ("cem", "100", C)])
        self.assertEqual(pt("dois vírgula cinco cem"), [("dois vírgula cinco", "2.5", D), ("cem", "100", C)])
        # a hundreds word may start the fractional part: 1 + 125/1000
        self.assertEqual(pt("um vírgula cento e vinte e cinco"), [("um vírgula cento e vinte e cinco", "1.125", D)])

    def test_a_decimal_counts_the_scale_after_it(self):
        # 2.5 x 10^6 = 2500000
        self.assertEqual(pt("dois vírgula cinco milhões"), [("dois vírgula cinco milhões", "2500000", C)])
        # 1.2 x 1000
        self.assertEqual(pt("um vírgula dois mil"), [("um vírgula dois mil", "1200", C)])


class TestDigits(unittest.TestCase):
    def test_digit_strings_use_the_locale_marks(self):
        self.assertEqual(pt("1.000.000"), [("1.000.000", "1000000", C)])
        self.assertEqual(pt("2,5"), [("2,5", "2.5", D)])
        self.assertEqual(pt("1.234,50 euros"), [("1.234,50", "1234.5", D)])

    def test_a_point_that_cannot_group_digits_marks_decimals(self):
        # SI Brochure 5.4.4: the decimal marker "shall be either the point on
        # the line or the comma on the line", and a number between -1 and 1
        # starts with "0"; a group has three digits (the group_mark source)
        for text, value in (("1.5", "1.5"), ("3.14159", "3.14159"), ("0.500", "0.5"), ("-0.500", "-0.5"),
                            ("0.050", "0.05"), ("1234.567", "1234.567")):
            with self.subTest(text=text):
                self.assertEqual(pt(text), [(text, value, D)])
                self.assertEqual(read(text, "pt-BR"), [(text, value, D)])
        self.assertEqual(pt("custa 3.5 milhões"), [("3.5 milhões", "3500000", C)])
        # three digits after a first group of one to three digits are a group
        self.assertEqual(pt("1.500"), [("1.500", "1500", C)])
        self.assertEqual(pt("1.5.2"), [])
        # SI 5.4.4 writes "43 279.168 29": a space group before a point decimal is one number
        for text, value in (("1 234.5", "1234.5"), ("-1 234.5", "-1234.5"), ("12 345.67", "12345.67"),
                            ("1 234.567", "1234.567"), ("1 234 567.5", "1234567.5")):
            with self.subTest(text=text):
                self.assertEqual(pt(text), [(text, value, D)])
        # without a space group the point and three digits are a thousands mark
        self.assertEqual(pt("234.567"), [("234.567", "234567", C)])
        # no space group: two digits, a hyphen, or four digits before the space
        self.assertEqual(pt("1 23.5"), [("1", "1", C), ("23.5", "23.5", D)])
        self.assertEqual(pt("entre 10-123.5 kg"), [("10", "10", C), ("123.5", "123.5", D)])
        self.assertEqual(pt("em 2024 123.45 euros"), [("2024", "2024", C), ("123.45", "123.45", D)])
        # a signed number continues no group: 12, -123.5 and 4
        self.assertEqual(pt("valores 12 -123.5 e 4"), [("12", "12", C), ("-123.5", "-123.5", D), ("4", "4", C)])
        # a hyphen joins no group: 10 and 123, as FLORES de "120-160 Kubikmeter" is 120 and 160
        self.assertEqual(pt("entre 10-123 kg"), [("10", "10", C), ("123", "123", C)])
        self.assertEqual(read("120-160 Kubikmeter", "de"), [("120", "120", C), ("160", "160", C)])
        # de reads a space group before a point decimal the same way, and "1.500" as 1500
        self.assertEqual(read("1 234.5", "de"), [("1 234.5", "1234.5", D)])
        # fr groups with a narrow space, not a point: the space group still comes before the decimal
        self.assertEqual(read("1 234.5", "fr-FR"), [("1 234.5", "1234.5", D)])
        self.assertEqual(read("1.500", "de"), [("1.500", "1500", C)])
        self.assertEqual(read("am 24.12.", "de"), [])
        self.assertEqual(read("11.29 Uhr", "de"), [])
        self.assertEqual(read("The rate is 2.5.", "en"), [("2.5", "2.5", D)])

    def test_a_native_group_mark_before_a_point_decimal(self):
        # SI 5.4.4 "43 279.168 29" with the locale's own group mark (CLDR numbers,
        # symbols-numberSystem-latn group): 1 x 1000 + 234 = 1234, 12 x 1000 + 345 = 12345,
        # 10 x 1000 + 123 = 10123
        marks = {"plain space": (" ", "et fi hu nb nn sv"), "no-break space": ("\u00a0", "bg kab pl ru sk uk"),
                 "narrow no-break space": ("\u202f", "fr-FR fr-BE"), "apostrophe": ("'", "fr-CH")}
        for name, (mark, langs) in marks.items():
            for lang in langs.split():
                for whole, fraction, value in (("1", "234.5", "1234.5"), ("12", "345.67", "12345.67"),
                                               ("10", "123.5", "10123.5")):
                    text = f"{whole}{mark}{fraction}"
                    with self.subTest(lang=lang, mark=name, text=text):
                        self.assertEqual(read(text, lang), [(text, value, D)])
        # in a sentence, signed, with a second group, and with the comma
        self.assertEqual(read("Hinta on 1 234.5 euroa.", "fi"), [("1 234.5", "1234.5", D)])
        self.assertEqual(read("Цена 10\u00a0123.5 рублей", "ru"), [("10\u00a0123.5", "10123.5", D)])
        self.assertEqual(read("-1\u00a0234.5", "pl"), [("-1\u00a0234.5", "-1234.5", D)])
        self.assertEqual(read("1'234'567.5", "fr-CH"), [("1'234'567.5", "1234567.5", D)])
        self.assertEqual(read("1 234,5", "fi"), [("1 234,5", "1234.5", D)])
        self.assertEqual(read("1\u00a0234,5", "ru"), [("1\u00a0234,5", "1234.5", D)])
        self.assertEqual(read("1'234,5", "fr-CH"), [("1'234,5", "1234.5", D)])
        # a point after one or two digits, or a hyphen, is no group
        self.assertEqual(read("12 3.5", "ru"), [("12", "12", C), ("3.5", "3.5", D)])
        # the native-mark path takes only a first group of 1 to 9 then groups of three
        self.assertEqual(read("12\u00a03.5", "fi"), [])
        self.assertEqual(read("12 3.5", "fi"), [("12", "12", C), ("3.5", "3.5", D)])
        # an apostrophe joins only a group of three, so the runs are two numbers, as "12 3.5" is
        self.assertEqual(read("12'3.5", "fr-CH"), [("12", "12", C), ("3.5", "3.5", D)])
        self.assertEqual(read("0\u00a0234.5", "ru"), [])
        self.assertEqual(read("1\u00a02345.6", "fi"), [])
        self.assertEqual(read("1 2345.6", "fi"), [("1", "1", C), ("2345.6", "2345.6", D)])
        self.assertEqual(read("120-160", "ru"), [("120", "120", C), ("160", "160", C)])
        # point group marks and the English comma keep their reading
        self.assertEqual(read("1.500", "de"), [("1.500", "1500", C)])
        self.assertEqual(read("234.567", "de"), [("234.567", "234567", C)])
        for lang in ("pt-PT", "de"):
            self.assertEqual(read("1.234.5", lang), [])
            self.assertEqual(read("12.345.67", lang), [])
        self.assertEqual(read("1,234.5", "en"), [("1,234.5", "1234.5", D)])

    def test_zero_led_digits_before_a_space_group_point_decimal(self):
        self.assertEqual(pt("0 234.5"), [("0", "0", C), ("234.5", "234.5", D)])
        self.assertEqual(pt("nota 0 234.5 kg"), [("0", "0", C), ("234.5", "234.5", D)])
        self.assertEqual(pt("007 234.5"), [("007", "7", C), ("234.5", "234.5", D)])

    def test_pt_pt_also_groups_digits_with_a_space(self):
        # 1 x 10^6 + 234 x 10^3 + 567 = 1234567
        self.assertEqual(pt("vivem 1 234 567 pessoas"), [("1 234 567", "1234567", C)])
        self.assertEqual(pt("custa 2 500,75 euros"), [("2 500,75", "2500.75", D)])
        self.assertEqual(pt("os números 12 e 345"), [("12", "12", C), ("345", "345", C)])

    def test_pt_br_does_not_group_digits_with_a_space(self):
        self.assertEqual(read("vivem 1 234 pessoas", "pt-BR"), [("1", "1", C), ("234", "234", C)])

    def test_a_lone_decimal_mark_before_digits(self):
        # a group mark stands only between digits, so either mark is decimal
        self.assertEqual(pt("(.5) e 3"), [(".5", "0.5", D), ("3", "3", C)])
        self.assertEqual(pt(",5 litros e 3 copos"), [(",5", "0.5", D), ("3", "3", C)])
        self.assertEqual(pt("custa .99 euros"), [(".99", "0.99", D)])
        self.assertEqual(pt("menos .5 graus"), [("menos .5", "-0.5", D)])
        # an ellipsis is no decimal mark, and a mark before grouped digits
        # is no decimal mark either
        self.assertEqual(pt("...5"), [("5", "5", C)])
        self.assertEqual(pt("custa .5.000"), [("5.000", "5000", C)])

    def test_a_lone_decimal_mark_after_a_sign(self):
        self.assertEqual(pt("estão -.5 graus"), [("-.5", "-0.5", D)])
        self.assertEqual(pt("estão -,5 graus"), [("-,5", "-0.5", D)])

    def test_no_digit_group_follows_a_leading_zero(self):
        # "." groups digits in pt, and a group never follows a leading zero:
        # in "0.500" the point marks decimals, and "01.500" is no number
        self.assertEqual(pt("pesa 0.500 kg"), [("0.500", "0.5", D)])
        self.assertEqual(pt("pesa 01.500 kg"), [])
        self.assertEqual(read("pesa 0.500 kg", "pt-BR"), [("0.500", "0.5", D)])
        self.assertEqual(pt("os números 0 500"), [("0", "0", C), ("500", "500", C)])
        self.assertEqual(pt("pesa 1.500 kg"), [("1.500", "1500", C)])

    def test_a_whole_value_is_cardinal_even_with_a_decimal_mark(self):
        self.assertEqual(pt("dois vírgula zero"), [("dois vírgula zero", "2", C)])
        self.assertEqual(pt("3,00 euros"), [("3,00", "3", C)])

    def test_marks_that_do_not_fit_the_locale_are_no_number(self):
        self.assertEqual(pt("versão 3.11"), [])

    def test_leading_zeros_stay_in_the_text_only(self):
        self.assertEqual(pt("agente 007"), [("007", "7", C)])

    def test_digits_count_a_scale_word(self):
        mentions = tag_numbers("2,5 mil milhões", "pt-PT")
        # 2.5 x 10^9 = 2500000000
        self.assertEqual([(m.value, m.form) for m in mentions], [("2500000000", Form.MIXED)])

    def test_a_minus_sign_belongs_to_the_digits(self):
        self.assertEqual(pt("estão -5 graus"), [("-5", "-5", C)])
        self.assertEqual(pt("páginas 5-7"), [("5", "5", C), ("7", "7", C)])

    def test_a_minus_sign_negates_the_whole_number(self):
        # Wikipedia, "Fraction": "Subtraction or negation is applied to the
        # entire mixed numeral". Each value is minus the unsigned reading.
        for text, lang, value in (
                ("-2 milhões e meio", "pt-PT", "-2500000"),
                ("-1 milhão e meio", "pt-BR", "-1500000"),
                ("-2 mil e quinhentos", "pt-PT", "-2500"),
                ("-2 dúzias e meia", "pt-PT", "-30"),
                ("−2 e meio", "pt-PT", "-2.5"),
                ("-2 and a half", "en", "-2.5"),
                ("-2 million and a half", "en", "-2500000"),
                ("-3 and three quarters", "en", "-3.75"),
                ("-2 millones y medio", "es", "-2500000"),
                ("-2 millions et demi", "fr-FR", "-2500000"),
                ("-2 milioni e mezzo", "it", "-2500000"),
                ("-2 Millionen einhalb", "de", "-2500000"),
                ("-2 buçuk", "tr", "-2.5")):
            with self.subTest(text=text, lang=lang):
                self.assertEqual([m.value for m in tag_numbers(text, lang)], [value])

    def test_a_signed_digit_string_starts_a_number(self):
        # a sign never stands inside a number: "2 milhões e -500 mil" is two
        self.assertEqual(pt("2 milhões e -500 mil"), [("2 milhões", "2000000", C), ("-500 mil", "-500000", C)])
        self.assertEqual(pt("menos -5"), [("menos -5", "5", C)])

    def test_a_signed_lower_limit_splits_a_range(self):
        # after a range cue the first limit is the smaller one: -1000000 < 500000
        self.assertEqual(pt("entre -1 milhão e quinhentos mil"),
                         [("-1 milhão", "-1000000", C), ("quinhentos mil", "500000", C)])
        self.assertEqual(read("between -1 million and 500 thousand dollars", "en"),
                         [("-1 million", "-1000000", C), ("500 thousand", "500000", C)])
        self.assertEqual(read("entre -1 million et cinq cent mille", "fr-FR"),
                         [("-1 million", "-1000000", C), ("cinq cent mille", "500000", C)])
        # a joiner inside the signed first limit does not split the range:
        # -2500000 and 3000000, -2500 and 3000
        self.assertEqual([m.value for m in tag_numbers("entre -2 milhões e meio e 3 milhões", "pt-PT")],
                         ["-2500000", "3000000"])
        self.assertEqual([m.value for m in tag_numbers("between -2 thousand and five hundred and 3 thousand", "en")],
                         ["-2500", "3000"])
        self.assertEqual(read("o 3.º e o -3.º", "pt-PT"), [("3.º", "3", O)])

    def test_digits_inside_a_name_are_no_number(self):
        self.assertEqual(pt("um ficheiro mp3"), [("um", "1", C)])


class TestOrdinals(unittest.TestCase):
    def test_an_article_before_a_hyphenated_noun_is_weak(self):
        # "guarda-chuva" and "quinta-feira" are one noun each, so "um" and
        # "uma" are the article
        self.assertEqual(sure("Devo levar um guarda-chuva comigo?", "pt-PT"), [("um", "1", 0.3)])
        self.assertEqual(sure("O dia 1 de janeiro calha a uma quinta-feira.", "pt-PT"),
                         [("1", "1", 1.0), ("uma", "1", 0.3)])
        self.assertEqual(sure("Preciso de um guarda-chuva e de dois casacos.", "pt-BR"),
                         [("um", "1", 0.3), ("dois", "2", 1.0)])
        # a number word joined to a number word by a hyphen keeps its value
        self.assertEqual(sure("Tenho um-dois.", "pt-PT"), [("um", "1", 1.0), ("dois", "2", 1.0)])

    def test_every_word_of_an_ordinal_is_ordinal(self):
        # 20 + 1 = 21; 100 + 20 + 3 = 123
        self.assertEqual(pt("vigésimo primeiro"), [("vigésimo primeiro", "21", O)])
        self.assertEqual(pt("centésimo vigésimo terceiro"), [("centésimo vigésimo terceiro", "123", O)])

    def test_both_spellings_of_the_three_hundredth(self):
        self.assertEqual(pt("trecentésimo"), [("trecentésimo", "300", O)])
        self.assertEqual(pt("tricentésima"), [("tricentésima", "300", O)])

    def test_ordinal_parts_must_descend_by_class(self):
        self.assertEqual(pt("vigésimo décimo"), [("vigésimo", "20", O), ("décimo", "10", O)])

    def test_the_count_before_milesimo_is_cardinal(self):
        # 2 x 1000 = 2000; 1000 + 1 = 1001
        self.assertEqual(pt("dois milésimo"), [("dois milésimo", "2000", O)])
        self.assertEqual(pt("milésimo primeiro"), [("milésimo primeiro", "1001", O)])

    def test_ordinal_gender(self):
        mentions = tag_numbers("a vigésima primeira vez", "pt-PT")
        self.assertEqual([(m.value, m.gender) for m in mentions], [("21", "feminine")])

    def test_digit_ordinals(self):
        mentions = tag_numbers("o 1.º lugar e a 2ª volta", "pt-PT")
        self.assertEqual([(m.text, m.value, m.kind.value, m.gender) for m in mentions],
                         [("1.º", "1", O, "masculine"), ("2ª", "2", O, "feminine")])

    def test_an_ordinal_that_is_also_a_common_word_is_weak(self):
        mentions = tag_numbers("o segundo lugar", "pt-PT")
        self.assertEqual([m.value for m in mentions], ["2"])
        self.assertLess(mentions[0].confidence, 0.5)


    def test_an_ordinal_scale_word_multiplies_only_the_last_group(self):
        # 2000000 + 300 x 1000 = 2300000; 1000000 + 200 x 1000 = 1200000
        self.assertEqual(pt("dois milhões e trezentos milésimo"),
                         [("dois milhões e trezentos milésimo", "2300000", O)])
        self.assertEqual(pt("um milhão e duzentos milésimo"), [("um milhão e duzentos milésimo", "1200000", O)])
        # 3 x 10^90 + 400 x 1000 (long scale: quindecilião = 10^90)
        self.assertEqual(pt("três quindecilhões e quatrocentos milésimo"),
                         [("três quindecilhões e quatrocentos milésimo", "3" + "0" * 84 + "400000", O)])
        # pt-BR: 200 x 10^12 + 17 x 1000 = 200000000017000
        self.assertEqual(read("duzentos trilhões e dezessete milésimo", "pt-BR"),
                         [("duzentos trilhões e dezessete milésimo", "200000000017000", O)])
        # every word ordinal (CLDR): 2 x 1000 + 200 = 2200
        self.assertEqual(pt("dois milésimo ducentésimo"), [("dois milésimo ducentésimo", "2200", O)])
        # a plural is a fraction: 2/1000
        self.assertEqual(pt("duas milésimas"), [("duas milésimas", "0.002", F)])

class TestFractions(unittest.TestCase):
    def test_the_word_after_um_quinto_decides_fraction_or_ordinal(self):
        # 1/5 of the inheritance; 1/5 of them; 1/5 at the end; the fifth
        # floor; 10 + 2 = 12th
        self.assertEqual(pt("recebeu um quinto da herança"), [("um quinto", "0.2", F)])
        self.assertEqual(pt("só um quinto deles chegou"), [("um quinto", "0.2", F)])
        self.assertEqual(pt("comeu um quinto"), [("um quinto", "0.2", F)])
        self.assertEqual(pt("comeu um quinto, e saiu"), [("um quinto", "0.2", F)])
        self.assertEqual(pt("comprou um quinto andar"), [("um", "1", C), ("quinto", "5", O)])
        self.assertEqual(pt("um décimo segundo lugar"), [("um", "1", C), ("décimo segundo", "12", O)])

    def test_an_ordinal_read_from_the_word_after_it_is_not_sure(self):
        # a verb after "um décimo" also gives the ordinal, so the ordinal 10
        # has the score of a word with a second meaning; 12th stays sure
        self.assertEqual(sure("Um décimo sobreviveu.", "pt-PT"), [("Um", "1", 0.3), ("décimo", "10", 0.4)])
        self.assertEqual(sure("Um décimo segundo lugar.", "pt-PT"), [("Um", "1", 0.3), ("décimo segundo", "12", 1.0)])
        self.assertEqual(sure("O décimo andar.", "pt-PT"), [("décimo", "10", 1.0)])

    def test_an_ordinal_before_parte_names_the_part(self):
        # 1/10; 1/5; 2/5
        self.assertEqual(pt("a décima parte do valor"), [("décima parte", "0.1", F)])
        self.assertEqual(pt("uma quinta parte"), [("uma quinta parte", "0.2", F)])
        self.assertEqual(pt("duas quintas partes"), [("duas quintas partes", "0.4", F)])

    def test_a_count_and_a_denominator(self):
        self.assertEqual(pt("um terço"), [("um terço", "1/3", F)])
        self.assertEqual(pt("dois terços"), [("dois terços", "2/3", F)])
        self.assertEqual(pt("três quartos"), [("três quartos", "0.75", F)])
        self.assertEqual(pt("um sétimo"), [("um sétimo", "1/7", F)])

    def test_meios_is_the_common_noun(self):
        self.assertEqual(pt("dois meios de pagamento"), [("dois", "2", C)])
        self.assertEqual(pt("tem três meios de transporte"), [("três", "3", C)])

    def test_the_avos_denominator(self):
        # 12 / 25 = 0.48
        self.assertEqual(pt("doze vinte e cinco avos"), [("doze vinte e cinco avos", "0.48", F)])

    def test_avos_after_a_denominator_above_ten(self):
        # Priberam, "avo": only a denominator above ten
        self.assertEqual(pt("doze avos"), [("doze avos", "1/12", F)])
        self.assertEqual(pt("onze avos"), [("onze avos", "1/11", F)])
        self.assertEqual(pt("cento e vinte avos"), [("cento e vinte avos", "1/120", F)])
        self.assertEqual(pt("três dois avos"), [("três", "3", C), ("dois", "2", C)])
        self.assertEqual(pt("dez avos"), [("dez", "10", C)])
        self.assertEqual(pt("visitei os meus dois avos"), [("dois", "2", C)])

    def test_a_fraction_word_with_no_count_after_e(self):
        # 2000 + 1/3 = 6001/3; 2000000 + 1/4 = 2000000.25
        self.assertEqual(pt("dois mil e terço"), [("dois mil e terço", "6001/3", F)])
        self.assertEqual(pt("dois milhões e quarto"), [("dois milhões e quarto", "2000000.25", F)])
        # a plural fraction word needs a count
        self.assertEqual(pt("dois e terços"), [("dois", "2", C)])

    def test_a_whole_and_a_fraction(self):
        # 2 + 1/3 = 7/3
        self.assertEqual(pt("dois e um terço"), [("dois e um terço", "7/3", F)])

    def test_a_fraction_of_a_collective_is_that_part_of_it(self):
        # 12 / 3 = 4; 2 x 12 / 3 = 8; 3 x 12 / 4 = 9
        self.assertEqual(pt("um terço de dúzia"), [("um terço de dúzia", "4", C)])
        self.assertEqual(pt("dois terços de dúzia"), [("dois terços de dúzia", "8", C)])
        self.assertEqual(pt("três quartos de uma dúzia"), [("três quartos de uma dúzia", "9", C)])
        self.assertEqual(pt("dois terços de dúzias"), [("dois terços", "2/3", F)])

    def test_a_count_and_a_singular_denominator_is_no_fraction(self):
        self.assertEqual(pt("dois terço"), [("dois", "2", C)])


class TestNonAsciiDigits(unittest.TestCase):
    def test_digits_of_other_scripts_are_no_number(self):
        for text in ("٣", "３", "१२", "1٣", "١٢٣٤"):
            with self.subTest(text=text):
                self.assertEqual(pt(f"tenho {text} maçãs"), [])


class TestMinus(unittest.TestCase):
    def test_minus_word(self):
        self.assertEqual(pt("menos dois graus"), [("menos dois", "-2", C)])

    def test_minus_idioms_are_no_sign(self):
        self.assertEqual(pt("pelo menos dois"), [("dois", "2", C)])
        self.assertEqual(pt("mais ou menos cinco"), [("cinco", "5", C)])
        self.assertEqual(pt("ao menos um"), [("um", "1", C)])

    def test_a_menos_before_a_number_compares(self):
        # CETEMPúblico: 33 of 60 "a menos" + number hits compare, 16 are the sign
        self.assertEqual(pt("o que corresponde a menos 2243 empresas"), [("2243", "2243", C)])
        self.assertEqual(pt("a menos que venhas"), [])
        self.assertEqual(pt("ficou a menos de três metros"), [("três", "3", C)])
        # the cost: the sign after "a menos" is lost
        self.assertEqual(pt("o termómetro desceu já a menos 15 graus"), [("15", "15", C)])

    def test_minus_between_numbers_is_no_sign(self):
        self.assertEqual(pt("cinco menos dois"), [("cinco", "5", C), ("dois", "2", C)])

    def test_a_minus_word_with_no_number_after_it_is_no_number(self):
        for text in ("Quero menos.", "Custa menos, mas é pior.", "Ele ganha menos", "menos"):
            with self.subTest(text=text):
                self.assertEqual(pt(text), [])
        self.assertEqual(read("Ele ganha menos", "pt-BR"), [])


class TestArticleAndGender(unittest.TestCase):
    def test_an_article_alone_before_a_noun_is_weak(self):
        mentions = tag_numbers("comprei uma casa", "pt-PT")
        self.assertEqual([m.value for m in mentions], ["1"])
        self.assertLess(mentions[0].confidence, 0.5)

    def test_an_article_before_an_ordinal_is_weak(self):
        # the ordinal is part of the noun phrase: "um segundo facto"
        for text, lang in (("dá-me um segundo facto", "pt-PT"), ("me dá um segundo fato", "pt-BR"),
                           ("dime una segunda curiosidad", "es"), ("dammi una seconda curiosità", "it"),
                           ("donne-moi un deuxième fait", "fr"), ("dime un segundo dato", "gl"),
                           ("digues-me un segon fet", "ca"), ("nenn mir eine zweite Tatsache", "de")):
            with self.subTest(lang=lang):
                article, ordinal = tag_numbers(text, lang)
                self.assertEqual((article.value, ordinal.value, ordinal.kind.value), ("1", "2", "ordinal"))
                self.assertLess(article.confidence, 0.5)

    def test_an_article_that_starts_a_fraction_is_part_of_it(self):
        mentions = tag_numbers("comeu um terço do bolo", "pt-PT")
        self.assertEqual([(m.text, m.value, m.confidence) for m in mentions], [("um terço", "1/3", 1.0)])

    def test_an_article_inside_a_number_is_part_of_it(self):
        mentions = tag_numbers("comprei uma dúzia", "pt-PT")
        self.assertEqual([(m.value, m.confidence) for m in mentions], [("12", 1.0)])

    def test_gender_of_the_count(self):
        self.assertEqual([m.gender for m in tag_numbers("duas mil pessoas", "pt-PT")], ["feminine"])
        self.assertEqual([m.gender for m in tag_numbers("dois milhões", "pt-PT")], ["masculine"])
        self.assertEqual([m.gender for m in tag_numbers("três milhões", "pt-PT")], [None])

    def test_offsets_in_a_sentence(self):
        text = "Vendeu 3 casas por dois milhões e meio."
        mentions = tag_numbers(text, "pt-PT")
        self.assertEqual([m.char_span for m in mentions], [(7, 8), (19, 38)])
        self.assertEqual([m.value for m in mentions], ["3", "2500000"])


class TestOpenIssues(unittest.TestCase):
    # Rows each open issue lists. The expected value is the issue's, worked out by hand.

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/163")
    def test_minus_word_before_a_number_after_a_verb(self):
        self.assertEqual(read("desceu a menos três graus", "pt"), [("menos três", "-3", C)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/227")
    def test_digit_group_after_the_decimal_point_pt_pt(self):
        self.assertEqual(read("43 279.168 29", "pt-PT"), [("43 279.168 29", "43279.16829", D)])


@pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/161")
@pytest.mark.parametrize("text, expected", [
    ('dois mil milhões trezentos mil', [('dois mil milhões trezentos mil', '2000300000', C)]),
])
def test_pt_a_group_after_a_scale_word_adds(text, expected):
    # 2 x 1000 x 1000000 + 300 x 1000 = 2000300000
    assert read(text, "pt") == expected



if __name__ == "__main__":
    unittest.main()


class TestHyphenatedCompounds(unittest.TestCase):
    def test_a_numeral_inside_a_compound_noun_is_no_number(self):
        # Priberam lists "segunda-feira" as one noun
        for day in ("segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira"):
            with self.subTest(day=day):
                self.assertEqual(pt(f"na {day} chegam vinte e duas pessoas"), [("vinte e duas", "22", C)])
        self.assertEqual(pt("ao meio-dia"), [])

    def test_a_compound_noun_breaks_the_link_between_numbers(self):
        self.assertEqual(pt("dois sexta-feira mil"), [("dois", "2", C), ("mil", "1000", C)])

    def test_a_compound_of_number_words_is_a_number(self):
        self.assertEqual(pt("vinte-e-dois"), [("vinte-e-dois", "22", C)])


class TestAbbreviations(unittest.TestCase):
    def test_dez_and_a_period_before_lower_case_or_digits_is_december(self):
        self.assertEqual(pt("a reunião é a 3 dez. 2025"), [("3", "3", C), ("2025", "2025", C)])
        self.assertEqual(pt("a reunião é a 3 dez., disse"), [("3", "3", C)])
        self.assertEqual(pt("no dia vinte e cinco dez. de dois mil"),
                         [("vinte e cinco", "25", C), ("dois mil", "2000", C)])

    def test_dez_and_a_period_at_a_sentence_end_is_ten(self):
        self.assertEqual(pt("ganhou dez. Ele ganhou cinco."), [("dez", "10", C), ("cinco", "5", C)])
        self.assertEqual(pt("ganhou dez."), [("dez", "10", C)])
