"""Portuguese grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/pt-PT.json."""
import unittest

from helpers import read
from numtag import Form, tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def pt(text: str, **options) -> list[tuple[str, str, str]]:
    return read(text, "pt-PT", **options)


class TestBindingRulings(unittest.TestCase):
    def test_mil_counts_the_whole_cardinal_before_a_collective(self):
        # (1000 + 2) x 12 = 12024
        self.assertEqual(pt("mil e duas dúzias"), [("mil e duas dúzias", "12024", C)])

    def test_after_milhao_the_collective_counts_only_the_cardinal_after_it(self):
        # 1000000 + 2 x 12 = 1000024
        self.assertEqual(pt("um milhão e duas dúzias"), [("um milhão e duas dúzias", "1000024", C)])

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

    def test_a_half_after_mil_is_half_of_one(self):
        self.assertEqual(pt("mil e meio"), [("mil e meio", "1000.5", F)])

    def test_a_half_after_a_cardinal_is_half_of_one(self):
        self.assertEqual(pt("dois e meio"), [("dois e meio", "2.5", F)])

    def test_meia_duzia_and_duzia_e_meia(self):
        # 12 / 2 = 6; 12 + 6 = 18
        self.assertEqual(pt("meia dúzia"), [("meia dúzia", "6", C)])
        self.assertEqual(pt("dúzia e meia"), [("dúzia e meia", "18", C)])

    def test_meia_duzia_is_a_group_of_its_own(self):
        self.assertEqual(pt("cem e meia dúzia"), [("cem", "100", C), ("meia dúzia", "6", C)])

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

    def test_a_plural_with_no_count_is_no_number(self):
        for text in ("dúzias de ovos", "milhões de pessoas", "milhares de pessoas",
                     "centenas de pessoas"):
            with self.subTest(text=text):
                self.assertEqual(pt(text), [])

    def test_a_decimal_count_before_a_collective(self):
        # 2.5 x 12 = 30
        self.assertEqual(pt("2,5 dúzias"), [("2,5 dúzias", "30", C)])


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

    def test_a_count_belongs_to_the_scale_word_after_it(self):
        self.assertEqual(pt("dois mil e três mil"), [("dois mil", "2000", C), ("três mil", "3000", C)])
        self.assertEqual(pt("entre dois milhões e três milhões"),
                         [("dois milhões", "2000000", C), ("três milhões", "3000000", C)])

    def test_two_units_are_two_numbers(self):
        self.assertEqual(pt("dois três"), [("dois", "2", C), ("três", "3", C)])

    def test_a_long_number(self):
        # 2 x 10^9 + 300 x 10^3 + 45 = 2000300045
        self.assertEqual(pt("dois mil milhões trezentos mil e quarenta e cinco"),
                         [("dois mil milhões trezentos mil e quarenta e cinco", "2000300045", C)])

    def test_punctuation_ends_a_number(self):
        self.assertEqual(pt("mil, duzentos"), [("mil", "1000", C), ("duzentos", "200", C)])


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


class TestDecimals(unittest.TestCase):
    def test_a_decimal_after_a_scale_noun_needs_the_marker(self):
        self.assertEqual(pt("um milhão vírgula cinco"), [("um milhão vírgula cinco", "1000000.5", D)])

    def test_each_word_after_the_marker_gives_its_digits(self):
        self.assertEqual(pt("zero vírgula zero cinco"), [("zero vírgula zero cinco", "0.05", D)])
        self.assertEqual(pt("dois vírgula vinte e cinco"), [("dois vírgula vinte e cinco", "2.25", D)])

    def test_a_decimal_counts_the_scale_after_it(self):
        # 2.5 x 10^6 = 2500000
        self.assertEqual(pt("dois vírgula cinco milhões"), [("dois vírgula cinco milhões", "2500000", C)])


class TestDigits(unittest.TestCase):
    def test_digit_strings_use_the_locale_marks(self):
        self.assertEqual(pt("1.000.000"), [("1.000.000", "1000000", C)])
        self.assertEqual(pt("2,5"), [("2,5", "2.5", D)])
        self.assertEqual(pt("1.234,50 euros"), [("1.234,50", "1234.5", D)])

    def test_pt_pt_also_groups_digits_with_a_space(self):
        # 1 x 10^6 + 234 x 10^3 + 567 = 1234567
        self.assertEqual(pt("vivem 1 234 567 pessoas"), [("1 234 567", "1234567", C)])
        self.assertEqual(pt("custa 2 500,75 euros"), [("2 500,75", "2500.75", D)])
        self.assertEqual(pt("os números 12 e 345"), [("12", "12", C), ("345", "345", C)])

    def test_pt_br_does_not_group_digits_with_a_space(self):
        self.assertEqual(read("vivem 1 234 pessoas", "pt-BR"), [("1", "1", C), ("234", "234", C)])

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

    def test_digits_inside_a_name_are_no_number(self):
        self.assertEqual(pt("um ficheiro mp3"), [("um", "1", C)])


class TestOrdinals(unittest.TestCase):
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


class TestFractions(unittest.TestCase):
    def test_a_count_and_a_denominator(self):
        self.assertEqual(pt("um terço"), [("um terço", "1/3", F)])
        self.assertEqual(pt("dois terços"), [("dois terços", "2/3", F)])
        self.assertEqual(pt("três quartos"), [("três quartos", "0.75", F)])
        self.assertEqual(pt("um sétimo"), [("um sétimo", "1/7", F)])

    def test_the_avos_denominator(self):
        # 12 / 25 = 0.48
        self.assertEqual(pt("doze vinte e cinco avos"), [("doze vinte e cinco avos", "0.48", F)])

    def test_a_whole_and_a_fraction(self):
        # 2 + 1/3 = 7/3
        self.assertEqual(pt("dois e um terço"), [("dois e um terço", "7/3", F)])

    def test_a_count_and_a_singular_denominator_is_no_fraction(self):
        self.assertEqual(pt("dois terço"), [("dois", "2", C)])


class TestMinus(unittest.TestCase):
    def test_minus_word(self):
        self.assertEqual(pt("menos dois graus"), [("menos dois", "-2", C)])

    def test_minus_idioms_are_no_sign(self):
        self.assertEqual(pt("pelo menos dois"), [("dois", "2", C)])
        self.assertEqual(pt("mais ou menos cinco"), [("cinco", "5", C)])

    def test_minus_between_numbers_is_no_sign(self):
        self.assertEqual(pt("cinco menos dois"), [("cinco", "5", C), ("dois", "2", C)])


class TestArticleAndGender(unittest.TestCase):
    def test_an_article_alone_before_a_noun_is_weak(self):
        mentions = tag_numbers("comprei uma casa", "pt-PT")
        self.assertEqual([m.value for m in mentions], ["1"])
        self.assertLess(mentions[0].confidence, 0.5)

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


if __name__ == "__main__":
    unittest.main()
