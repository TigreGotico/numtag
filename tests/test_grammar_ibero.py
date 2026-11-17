"""Grammar rules of Spanish, Galician, Catalan, Asturian, Aragonese, Occitan
and Mirandese. Each expected value is worked out by hand in the comment
beside it; sources are in numtag/lexicon/<lang>.json."""
import unittest

from helpers import read, sure
from numtag import Scale, tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


class TestSpanish(unittest.TestCase):
    def test_an_article_before_a_number_in_digits_is_weak(self):
        # the number in digits is the article's noun
        self.assertEqual(sure("baja el brillo a un 20 por ciento", "es"), [("un", "1", 0.3), ("20", "20", 1.0)])
        self.assertEqual(sure("hay un 29 de febrero este año", "es"), [("un", "1", 0.3), ("29", "29", 1.0)])

    def test_a_lone_un_or_una_at_the_clause_end_is_weak(self):
        self.assertEqual(sure("muéstrame una", "es"), [("una", "1", 0.3)])
        self.assertEqual(sure("un", "es"), [("un", "1", 0.3)])
        # the counting form "uno" is a numeral there
        self.assertEqual(sure("quedó uno", "es"), [("uno", "1", 1.0)])

    def test_veintiuno_is_one_word_in_its_three_forms(self):
        for text in ("veintiuno", "veintiún", "veintiuna"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "es"), [(text, "21", C)])

    def test_the_feminine_hundreds_and_the_apocope_count(self):
        # 200 + 50 + 1 = 251; 21 x 1000 = 21000
        self.assertEqual(read("doscientas cincuenta y una personas", "es"),
                         [("doscientas cincuenta y una", "251", C)])
        self.assertEqual(read("veintiún mil euros", "es"), [("veintiún mil", "21000", C)])

    def test_y_joins_only_tens_and_units(self):
        # 1000 + 900 + 80 + 4 = 1984; 100 + 1 = 101
        self.assertEqual(read("mil novecientos ochenta y cuatro", "es"),
                         [("mil novecientos ochenta y cuatro", "1984", C)])
        self.assertEqual(read("ciento uno", "es"), [("ciento uno", "101", C)])

    def test_a_lone_ciento_is_the_noun_for_a_hundred(self):
        # DPD "ciento" §2: "Quien hace un cesto hace ciento"; the noun gets the homograph score
        self.assertEqual(sure("ciento", "es"), [("ciento", "100", 0.4)])
        self.assertEqual(sure("Éramos ciento y la madre.", "es"), [("ciento", "100", 0.4)])
        self.assertEqual(read("cien", "es"), [("cien", "100", C)])

    def test_un_ciento_is_a_hundred(self):
        # es.wikipedia "Puentedeume": 9, 100 and the year 2011
        self.assertEqual(read("Nueve restaurantes y casi un ciento de bares y cafeterías (datos de 2011).", "es"),
                         [("Nueve", "9", C), ("un ciento", "100", C), ("2011", "2011", C)])
        self.assertEqual(read("un ciento de platos", "es"), [("un ciento", "100", C)])

    def test_ciento_por_ciento_is_one_hundred_and_por_ciento_after_a_number_is_the_sign(self):
        # DPD "ciento" §3: totality is "ciento por ciento": 100, sure; "cinco por ciento" is 5
        self.assertEqual(sure("ciento por ciento", "es"), [("ciento", "100", 1.0)])
        self.assertEqual(sure("cinco por ciento", "es"), [("cinco", "5", 1.0)])
        self.assertEqual(sure("el noventa por ciento", "es"), [("noventa", "90", 1.0)])

    def test_cien_por_cien_is_one_hundred_once(self):
        # DPD "ciento" §3: totality is also "cien por cien": 100, sure, and "por cien" is the sign
        self.assertEqual(sure("cien por cien", "es"), [("cien", "100", 1.0)])
        self.assertEqual(sure("Al cien por cien.", "es"), [("cien", "100", 1.0)])
        self.assertEqual(sure("El calor es pegajoso, la humedad del cien por cien", "es"), [("cien", "100", 1.0)])
        # es.wikipedia "Nanobatería": 80, the article "un", 100 and 10
        text = ("Los prototipos fueron capaces de recobrar el ochenta por ciento de capacidad en un minuto "
                "y estaban recargadas al cien por cien después de 10 minutos.")
        ochenta, un, diez = text.index("ochenta"), text.index(" un ") + 1, text.index("10")
        cien = text.index("cien por cien")
        self.assertEqual([(m.char_span, m.value, round(m.confidence, 1)) for m in tag_numbers(text, "es")],
                         [((ochenta, ochenta + 7), "80", 1.0), ((un, un + 2), "1", 0.3),
                          ((cien, cien + 4), "100", 1.0), ((diez, diez + 2), "10", 1.0)])

    def test_por_cien_after_another_number_keeps_its_hundred(self):
        # DPD "ciento" §3 rejects "el noventa por cien": "por cien" is the sign only after "cien"
        self.assertEqual(read("el noventa por cien", "es"), [("noventa", "90", C), ("cien", "100", C)])
        self.assertEqual(read("cinco por cien", "es"), [("cinco", "5", C), ("cien", "100", C)])
        self.assertEqual(read("el 20 por cien", "es"), [("20", "20", C), ("cien", "100", C)])
        # with no number before it, "por cien" is a price: 100
        self.assertEqual(read("Lo vendió por cien euros.", "es"), [("cien", "100", C)])
        self.assertEqual(read("por ciento veinte votos", "es"), [("ciento veinte", "120", C)])
        self.assertEqual(read("cien por ciento", "es"), [("cien", "100", C)])

    def test_y_between_mil_and_a_one_is_one_number(self):
        # 1000 + 1 = 1001, es.wikipedia "Las mil y una noches" and "Los mil y un días"
        self.assertEqual(read("Las mil y una noches", "es"), [("mil y una", "1001", C)])
        self.assertEqual(read("dentro de mil y un días", "es"), [("mil y un", "1001", C)])
        self.assertEqual(read("mil y uno", "es"), [("mil y uno", "1001", C)])
        # without "y" the same number stays whole
        self.assertEqual(read("mil uno", "es"), [("mil uno", "1001", C)])

    def test_other_y_after_mil_stays_two_numbers_a_known_gap(self):
        # Older texts join these; numtag reads the unjoined form, and the gap is open
        self.assertEqual(read("mil y quinientos", "es"), [("mil", "1000", C), ("quinientos", "500", C)])
        self.assertEqual(read("mil y veinte", "es"), [("mil", "1000", C), ("veinte", "20", C)])
        self.assertEqual(read("mil y dos", "es"), [("mil", "1000", C), ("dos", "2", C)])
        self.assertEqual(read("dos mil y uno", "es"), [("dos mil", "2000", C), ("uno", "1", C)])
        self.assertEqual(read("doscientos mil y uno", "es"), [("doscientos mil", "200000", C), ("uno", "1", C)])

    def test_no_y_joins_a_group_after_a_larger_scale(self):
        self.assertEqual(read("un millón y dos", "es"), [("un millón", "1000000", C), ("dos", "2", C)])
        self.assertEqual(read("dos millones y quinientos mil", "es"),
                         [("dos millones", "2000000", C), ("quinientos mil", "500000", C)])

    def test_por_ciento_with_no_number_before_it_holds_no_hundred(self):
        # "tanto por ciento" is a percentage (es.wiktionary "ciento", sense 5)
        self.assertEqual(sure("el tanto por ciento", "es"), [])
        self.assertEqual(sure("¿qué tanto por ciento?", "es"), [])
        self.assertEqual(sure("un tanto por ciento elevado", "es"), [("un", "1", 0.3)])

    def test_an_ordinal_before_por_ciento_keeps_its_score(self):
        self.assertEqual(sure("segundo por ciento", "es"), [("segundo", "2", 0.4)])

    def test_the_old_spelling_diez_y_seis_to_nueve_is_one_number(self):
        # 10 + 6 = 16; 10 + 7 = 17; 10 + 9 = 19
        self.assertEqual(read("diez y seis", "es"), [("diez y seis", "16", C)])
        self.assertEqual(read("con diez y siete años", "es"), [("diez y siete", "17", C)])
        self.assertEqual(read("diez y nueve", "es"), [("diez y nueve", "19", C)])
        self.assertEqual(read("veinte y dos", "es"), [("veinte y dos", "22", C)])

    def test_lists_joined_with_y_stay_two_numbers(self):
        for text, first, second in (("uno y dos", "1", "2"), ("cinco y seis", "5", "6"), ("diez y uno", "10", "1"),
                                    ("diez y cinco", "10", "5"), ("diez y veinte", "10", "20"),
                                    ("once y doce", "11", "12"), ("quince y dieciséis", "15", "16")):
            with self.subTest(text=text):
                self.assertEqual([m[1] for m in read(text, "es")], [first, second])

    def test_the_one_word_tens_are_valid(self):
        # 30 + 1 = 31; 40 + 3 = 43
        self.assertEqual(read("treintaiuno", "es"), [("treintaiuno", "31", C)])
        self.assertEqual(read("cuarentaitrés", "es"), [("cuarentaitrés", "43", C)])

    def test_a_written_y_after_ciento_keeps_the_hundred(self):
        # 100 + 20 = 120 with or without "y"; -(100 + 2) = -102
        self.assertEqual(read("ciento y veinte personas", "es"), [("ciento y veinte", "120", C)])
        self.assertEqual(read("ciento veinte personas", "es"), [("ciento veinte", "120", C)])
        self.assertEqual(read("menos ciento y dos grados", "es"), [("menos ciento y dos", "-102", C)])
        # "y" after a round ten still joins only a unit: 120 and 30, never 150
        self.assertEqual(read("ciento veinte y treinta", "es"),
                         [("ciento veinte", "120", C), ("treinta", "30", C)])

    def test_billon_is_a_million_millions(self):
        # 2 x 10^12; short scale on request: 2 x 10^9
        self.assertEqual(read("dos billones", "es"), [("dos billones", "2000000000000", C)])
        self.assertEqual(read("dos billones", "es", scale=Scale.SHORT), [("dos billones", "2000000000", C)])

    def test_mil_millones_and_millardo_are_ten_to_the_ninth(self):
        self.assertEqual(read("mil millones", "es"), [("mil millones", "1000000000", C)])
        self.assertEqual(read("un millardo", "es"), [("un millardo", "1000000000", C)])

    def test_ordinals_in_one_or_two_words_and_their_abbreviations(self):
        self.assertEqual(read("vigesimoprimero", "es"), [("vigesimoprimero", "21", O)])
        self.assertEqual(read("la vigésima primera", "es"), [("vigésima primera", "21", O)])
        self.assertEqual(read("el 3.er piso", "es"), [("3.er", "3", O)])

    def test_the_avo_fractions(self):
        # 5 / 13
        self.assertEqual(read("cinco treceavos", "es"), [("cinco treceavos", "5/13", F)])

    def test_menos_in_an_idiom_holds_no_sign(self):
        self.assertEqual(read("al menos dos", "es"), [("dos", "2", C)])
        self.assertEqual(read("menos cinco grados", "es"), [("menos cinco", "-5", C)])

    def test_a_preposition_before_menos_keeps_the_sign(self):
        self.assertEqual(read("la temperatura es de menos tres grados", "es"), [("menos tres", "-3", C)])
        self.assertEqual(read("bajó a menos tres grados", "es"), [("menos tres", "-3", C)])

    def test_the_digit_marks(self):
        self.assertEqual(read("1.234,5 kilos", "es"), [("1.234,5", "1234.5", D)])


class TestGalician(unittest.TestCase):
    def test_e_joins_tens_and_units_and_cento_takes_no_e(self):
        # 200 + 30 + 4 = 234; 100 + 1 = 101
        self.assertEqual(read("douscentos trinta e catro", "gl"), [("douscentos trinta e catro", "234", C)])
        self.assertEqual(read("cento unha persoas", "gl"), [("cento unha", "101", C)])

    def test_a_written_e_after_cento_keeps_the_hundred_and_the_sign(self):
        # 100 + 20 = 120; 100 + 30 + 2 = 132; -(100 + 20 + 3 + 0.45) = -123.45
        self.assertEqual(read("cento e vinte persoas", "gl"), [("cento e vinte", "120", C)])
        self.assertEqual(read("cento e trinta e dous", "gl"), [("cento e trinta e dous", "132", C)])
        text = "menos cento e vinte e tres coma corenta e cinco"
        self.assertEqual(read(text, "gl"), [(text, "-123.45", D)])
        # "cen" stands alone: 100, then 20 from "vinte"
        self.assertEqual(read("cen persoas e vinte cans", "gl"), [("cen", "100", C), ("vinte", "20", C)])

    def test_the_feminine_forms(self):
        self.assertEqual(read("duascentas", "gl"), [("duascentas", "200", C)])
        self.assertEqual(read("vinte e unha", "gl"), [("vinte e unha", "21", C)])

    def test_billon_is_a_million_millions(self):
        self.assertEqual(read("dous billóns", "gl"), [("dous billóns", "2000000000000", C)])

    def test_gender_goes_on_the_last_word_of_an_ordinal(self):
        self.assertEqual(read("décimo primeira", "gl"), [("décimo primeira", "11", O)])

    def test_the_avo_partitive(self):
        # 1 / 16 = 0.0625
        self.assertEqual(read("un dezaseisavo", "gl"), [("un dezaseisavo", "0.0625", F)])

    def test_sexaxesimo_is_the_sixtieth(self):
        # 60 as the ordinal word; 60 + 4 = 64 with the feminine on the last word
        self.assertEqual(read("o sexaxésimo", "gl"), [("sexaxésimo", "60", O)])
        self.assertEqual(read("a sexaxésima cuarta vez", "gl"), [("sexaxésima cuarta", "64", O)])
        # the plural takes the same 60
        self.assertEqual(read("os sexaxésimos", "gl"), [("sexaxésimos", "60", O)])
        self.assertEqual(read("as sexaxésimas", "gl"), [("sexaxésimas", "60", O)])


class TestCatalan(unittest.TestCase):
    def test_cent_after_per_and_a_number_is_the_percent_sign(self):
        # "per cent" is the percent sign: 50, not 50 and 100
        self.assertEqual(read("posa el volum al cinquanta per cent", "ca"), [("cinquanta", "50", C)])
        self.assertEqual(read("20 per cent", "ca"), [("20", "20", C)])
        self.assertEqual(read("el cent per cent", "ca"), [("cent", "100", C)])
        # a slot holds the number, and a vocabulary line holds the phrase alone
        self.assertEqual(read("baixa la brillantor al {brightness} per cent", "ca"), [])
        self.assertEqual(read("canvia els ulls al {brightness} per cent de brillantor", "ca"), [])
        self.assertEqual(read("per cent", "ca"), [])

    def test_cent_after_per_with_no_number_before_is_a_hundred(self):
        # "per" is "for": for a hundred euros, for 100 + 20 = 120
        self.assertEqual(read("Ho he venut per cent euros.", "ca"), [("cent", "100", C)])
        self.assertEqual(read("Ho he venut per cent.", "ca"), [("cent", "100", C)])
        self.assertEqual(read("per cent vint euros", "ca"), [("cent vint", "120", C)])

    def test_per_cent_with_no_number_before_is_weak(self):
        # "per cent" alone is the price "for a hundred" or the percent sign
        # with its number missing: "atenua la llum al per cent", "Tant per cent"
        self.assertEqual(sure("atenua la llum al per cent", "ca"), [("cent", "100", 0.4)])
        self.assertEqual(sure("Tant per cent.", "ca"), [("cent", "100", 0.4)])
        self.assertEqual(sure("Ho he venut per cent.", "ca"), [("cent", "100", 0.4)])
        # before a noun it is the price
        self.assertEqual(sure("Ho he venut per cent euros.", "ca"), [("cent", "100", 1.0)])
        # a number before the phrase or after "cent" makes the reading clear
        self.assertEqual(sure("El deu per cent dels guanys.", "ca"), [("deu", "10", 1.0)])
        self.assertEqual(sure("per cent vint euros", "ca"), [("cent vint", "120", 1.0)])

    def test_per_cent_before_de_and_the_article_is_weak(self):
        # "del" and "dels" are "de" and the article, so they read like "de"
        for text, lang, word in (("Calcula el tant per cent dels guanys.", "ca", "cent"),
                                 ("el tant per cent del total", "ca", "cent"),
                                 ("lo tant per cent dels vots", "oc", "cent"),
                                 ("Calcule le pour cent des voix.", "fr-FR", "cent"),
                                 ("Le pour cent du total.", "fr-FR", "cent"),
                                 ("calcola il per cento degli utenti", "it", "cento"),
                                 ("il per cento delle vendite", "it", "cento"),
                                 ("il per cento dell'anno", "it", "cento")):
            with self.subTest(text=text):
                self.assertEqual(sure(text, lang), [(word, "100", 0.4)])

    def test_nou_and_u_alone_are_weak(self):
        # "nou" is also "new" and "u" the name of a letter
        self.assertEqual(sure("crea un esdeveniment nou", "ca"), [("un", "1", 0.3), ("nou", "9", 0.4)])
        self.assertEqual(sure("tens ge pe u", "ca"), [("u", "1", 0.4)])
        # inside a longer number the reading is clear
        self.assertEqual(sure("vint-i-nou", "ca"), [("vint-i-nou", "29", 1.0)])
        self.assertEqual(sure("nou mil", "ca"), [("nou mil", "9000", 1.0)])
        self.assertEqual(sure("cent u", "ca"), [("cent u", "101", 1.0)])

    def test_nou_after_els_or_les_is_the_number(self):
        # the adjective after "les" is "noves" and after "els" "nous", so
        # "nou" there is nine: "les nou" is nine o'clock
        self.assertEqual(sure("avisa'm a les nou del matí", "ca"), [("nou", "9", 1.0)])
        self.assertEqual(sure("Els nou anys de la guerra.", "ca"), [("nou", "9", 1.0)])
        # "el nou" is also "the new one"
        self.assertEqual(sure("Ha arribat el nou.", "ca"), [("nou", "9", 0.4)])

    def test_un_before_nou_is_the_article(self):
        # "un nou" is no number: "un" is the article of "nou" ("new") and its noun
        self.assertEqual(sure("inicia un nou enregistrament d'àudio", "ca"), [("un", "1", 0.3), ("nou", "9", 0.4)])
        self.assertEqual(sure("Ja hem fet un nou prosèlit.", "ca"), [("un", "1", 0.3), ("nou", "9", 0.4)])
        # "un" before a whole number keeps its reading
        self.assertEqual(sure("un milió", "ca"), [("un milió", "1000000", 1.0)])

    def test_the_twenties_take_i_and_the_rest_a_hyphen(self):
        for text, value in (("vint-i-u", "21"), ("vint-i-una", "21"), ("trenta-dos", "32"),
                            ("quaranta-un", "41")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "ca"), [(text, value, C)])

    def test_a_count_before_cents_multiplies_the_hundred(self):
        # 2 x 100 + 20 + 5 = 225; 9 x 100 = 900
        self.assertEqual(read("dos-cents vint-i-cinc", "ca"), [("dos-cents vint-i-cinc", "225", C)])
        self.assertEqual(read("nou-centes", "ca"), [("nou-centes", "900", C)])

    def test_mil_milions_is_ten_to_the_ninth_and_bilio_the_twelfth(self):
        self.assertEqual(read("mil milions", "ca"), [("mil milions", "1000000000", C)])
        self.assertEqual(read("dos bilions", "ca"), [("dos bilions", "2000000000000", C)])

    def test_mil_lesim_reads_with_the_middle_dot_or_a_period(self):
        # 3 / 1000 = 0.003
        self.assertEqual(read("tres mil·lèsims", "ca"), [("tres mil·lèsims", "0.003", F)])
        self.assertEqual(read("un mil.lèsim", "ca"), [("un mil.lèsim", "0.001", F)])

    def test_only_the_last_word_of_an_ordinal_is_ordinal(self):
        # 40 + 2 = 42; 2 x 100 = 200
        self.assertEqual(read("quaranta-dosè", "ca"), [("quaranta-dosè", "42", O)])
        self.assertEqual(read("el dos-centè", "ca"), [("dos-centè", "200", O)])

    def test_a_middle_dot_is_inside_its_word(self):
        # "mil·límetres" is one word with no count: 3 and nothing else
        for text in ("Fa tres mil·límetres de gruix.", "Fa tres mil•límetres de gruix.",
                     "Fa tres mil∙límetres de gruix."):
            with self.subTest(text=text):
                self.assertEqual(read(text, "ca"), [("tres", "3", C)])
        self.assertEqual(read("El mil·lenni", "ca"), [])
        # a "mil" with no dot is still a thousand: 3 x 1000
        self.assertEqual(read("tres mil límits", "ca"), [("tres mil", "3000", C)])

    def test_mil_lesim_is_an_ordinal_and_a_fraction(self):
        # DIEC2 sense 1 is the 1000th; 2/1000 = 0.002; 4/1000 = 0.004
        self.assertEqual(read("el mil·lèsim aniversari", "ca"), [("mil·lèsim", "1000", O)])
        self.assertEqual(read("dues mil·lèsimes parts", "ca"), [("dues mil·lèsimes", "0.002", F)])
        self.assertEqual(read("quatre mil•lèsims", "ca"), [("quatre mil•lèsims", "0.004", F)])

    def test_a_hundreds_ordinal_after_mil_adds(self):
        # 1000 + 100 = 1100; 1000 + 5 x 100 = 1500; 2 x 1000 + 2 x 100 = 2200
        for text, value in [("mil centè", "1100"), ("mil centena", "1100"), ("mil cinc-centè", "1500"),
                            ("dos mil dos-centè", "2200"), ("dos-centè", "200"), ("nou centena", "900"),
                            ("centè", "100"), ("cinc mil set-centè", "5700")]:
            with self.subTest(text=text):
                self.assertEqual(read(text, "ca"), [(text, value, O)])

    def test_the_ordinal_abbreviations(self):
        self.assertEqual(read("el 4t i la 1a", "ca"), [("4t", "4", O), ("1a", "1", O)])

    def test_a_unit_ordinal_after_a_ten_makes_no_teen(self):
        # 12th is "dotzè"; "deu segons" is 10 and "segons", never 12
        found = read("Va esperar deu segons.", "ca")
        self.assertEqual(found[0], ("deu", "10", C))
        self.assertNotIn("12", [value for _, value, _ in found])
        # 100 + 10 = 110 and "segon"; 112th is "cent dotzè"
        self.assertEqual(read("cent deu segons", "ca")[0], ("cent deu", "110", C))

    def test_menys_in_an_idiom_holds_no_sign(self):
        for text in ("al menys tres dies", "més o menys tres dies", "ni més ni menys tres dies"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "ca"), [("tres", "3", C)])
        self.assertEqual(read("menys tres graus", "ca"), [("menys tres", "-3", C)])

    def test_the_valencian_forms(self):
        self.assertEqual(read("dèsset", "ca"), [("dèsset", "17", C)])
        self.assertEqual(read("huitanta-huit", "ca"), [("huitanta-huit", "88", C)])


class TestAsturian(unittest.TestCase):
    def test_cientu_needs_the_rest_and_cien_stands_alone(self):
        # 100 + 1 = 101
        self.assertEqual(read("cientu un", "ast"), [("cientu un", "101", C)])
        self.assertEqual(read("cientu", "ast"), [])
        self.assertEqual(read("cien", "ast"), [("cien", "100", C)])

    def test_the_feminine_hundreds_end_in_es(self):
        # 200 x 1000 = 200000
        self.assertEqual(read("doscientes mil", "ast"), [("doscientes mil", "200000", C)])

    def test_mil_takes_no_joiner(self):
        # 1000 + 30 + 9 = 1039
        self.assertEqual(read("mil trenta y nueve", "ast"), [("mil trenta y nueve", "1039", C)])

    def test_the_local_forms_of_eight(self):
        for text in ("oito", "otso"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "ast"), [(text, "8", C)])

    def test_billon_is_a_million_millions(self):
        self.assertEqual(read("dos billones", "ast"), [("dos billones", "2000000000000", C)])


class TestAragonese(unittest.TestCase):
    def test_the_numbers_to_thirty_are_one_word(self):
        self.assertEqual(read("decinueu", "an"), [("decinueu", "19", C)])
        self.assertEqual(read("vintitrés", "an"), [("vintitrés", "23", C)])

    def test_the_hundreds_from_eleven_to_sixteen_are_one_word(self):
        self.assertEqual(read("oncecientos", "an"), [("oncecientos", "1100", C)])
        self.assertEqual(read("sececientos", "an"), [("sececientos", "1600", C)])

    def test_the_other_numbers_are_several_words(self):
        # 30 + 1 = 31; 100 + 10 = 110; 40 x 1000 = 40000
        self.assertEqual(read("trenta y uno", "an"), [("trenta y uno", "31", C)])
        self.assertEqual(read("ciento diez", "an"), [("ciento diez", "110", C)])
        self.assertEqual(read("cuaranta mil", "an"), [("cuaranta mil", "40000", C)])

    def test_quatre_and_its_academy_spelling(self):
        # 30 + 4 = 34; 4 x 100 = 400
        for text, value in (("quatre", "4"), ("cuatre", "4"), ("trenta y cuatre", "34"),
                            ("vintiquatre", "24"), ("cuatrecientos", "400")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "an"), [(text, value, C)])

    def test_the_other_omniglot_forms(self):
        for text, value in (("cinc", "5"), ("set", "7"), ("nou", "9"), ("deu", "10"), ("setze", "16"),
                            ("vente", "20"), ("vintinou", "29")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "an"), [(text, value, C)])

    def test_vintisiet_is_twenty_seven(self):
        # 20 + 7 = 27; 100 + 27 = 127
        self.assertEqual(read("vintisiet", "an"), [("vintisiet", "27", C)])
        self.assertEqual(read("ciento vintisiet", "an"), [("ciento vintisiet", "127", C)])

    def test_millons_is_the_plural(self):
        self.assertEqual(read("35 millons", "an"), [("35 millons", "35000000", C)])


class TestOccitan(unittest.TestCase):
    def test_cent_after_per_and_a_number_is_the_percent_sign(self):
        self.assertEqual(read("vint per cent", "oc"), [("vint", "20", C)])

    def test_detz_e_set_reads_with_hyphens_or_spaces(self):
        for text, value in (("dètz-e-sèt", "17"), ("dètz e sèt", "17"), ("dètz-e-uèch", "18"),
                            ("dètz e nòu", "19")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "oc"), [(text, value, C)])

    def test_e_joins_only_the_twenties(self):
        # 20 + 1 = 21; 30 + 2 = 32
        self.assertEqual(read("vint e un", "oc"), [("vint e un", "21", C)])
        self.assertEqual(read("trenta doas", "oc"), [("trenta doas", "32", C)])

    def test_cent_and_cents_after_a_count(self):
        # 2 x 100 = 200; 2 x 100 + 20 = 220
        self.assertEqual(read("dos cents", "oc"), [("dos cents", "200", C)])
        self.assertEqual(read("dos cent vint", "oc"), [("dos cent vint", "220", C)])

    def test_the_forms_of_eight_from_the_occitan_reporter(self):
        for text, value in (("uòch", "8"), ("uechanta", "80"), ("uòchanta", "80")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "oc"), [(text, value, C)])
        for text in ("lo uechen jorn", "la ueitena", "los oitens", "lo uòchen"):
            with self.subTest(text=text):
                self.assertEqual([value for _, value, _ in read(text, "oc")], ["8"])

    def test_each_form_of_eight_makes_an_eighteen(self):
        # 10 + 8 = 18, as "dètz-e-sèt" is 10 + 7
        for text in ("dètz e ueiten", "dètz-e-oiten", "dètz e uòchen", "dètz e uechen", "dètz e ueitena",
                     "dètz-e-uòchenas"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "oc"), [(text, "18", O)])
        for text in ("dètz e uòch", "dètz-e-ueit"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "oc"), [(text, "18", C)])
        # a ten with no "e" and a unit stays two numbers: 10 and 8
        self.assertEqual(read("dètz, uòch", "oc"), [("dètz", "10", C), ("uòch", "8", C)])

    def test_mens_after_mai_o_holds_no_sign(self):
        self.assertEqual(read("mai o mens tres jorns", "oc"), [("tres", "3", C)])

    def test_mila_and_miliard(self):
        self.assertEqual(read("dos mila", "oc"), [("dos mila", "2000", C)])
        self.assertEqual(read("un miliard", "oc"), [("un miliard", "1000000000", C)])

    def test_only_the_last_word_of_an_ordinal_is_ordinal(self):
        self.assertEqual(read("la vint e unena", "oc"), [("vint e unena", "21", O)])
        self.assertEqual(read("la dètz-e-setena", "oc"), [("dètz-e-setena", "17", O)])


class TestMirandese(unittest.TestCase):
    def test_bint_i_is_one_word_with_its_apostrophe(self):
        for text, value in (("bint'i un", "21"), ("Bint'i ũa", "21"), ("bint’i dues", "22"),
                            ("bint'i nuôbe", "29")):
            with self.subTest(text=text):
                self.assertEqual(read(text, "mwl"), [(text, value, C)])

    def test_bint_uito_and_the_apostrophe_signs(self):
        # the Convenção writes 28 as "Bint' uito"; 20 + 1 = 21 with each apostrophe sign
        self.assertEqual(read("Tengo bint' uito anhos.", "mwl"), [("bint' uito", "28", C)])
        self.assertEqual(read("Tengo bint'uito anhos.", "mwl"), [("bint'uito", "28", C)])
        for text in ("bint‘i un", "bintʼi un", "bint’i un", "bint'i un"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "mwl"), [(text, "21", C)])
        # a space alone is no apostrophe: "bint uito" is 20 and 8
        self.assertEqual(read("bint uito", "mwl"), [("uito", "8", C)])

    def test_pul_menos_holds_no_sign(self):
        # "pul menos" is "at least": 8, never -8
        self.assertEqual(read("Ténen pul menos uito planetas.", "mwl"), [("uito", "8", C)])
        self.assertEqual(read("Fai menos dieç graus.", "mwl"), [("menos dieç", "-10", C)])

    def test_a_count_before_cientos_multiplies_the_hundred(self):
        # 2 x 100 + 30 + 4 = 234; 4 x 100 = 400
        self.assertEqual(read("dous cientos i trinta i quatro", "mwl"),
                         [("dous cientos i trinta i quatro", "234", C)])
        self.assertEqual(read("quatro ciêntos", "mwl"), [("quatro ciêntos", "400", C)])
        self.assertEqual(read("dues cientas", "mwl"), [("dues cientas", "200", C)])

    def test_i_joins_after_the_hundred_and_may_join_after_mil(self):
        # 100 + 1 = 101; 1000 + 200 + 30 + 4 = 1234
        self.assertEqual(read("ciento i un", "mwl"), [("ciento i un", "101", C)])
        for text in ("mil dous cientos i trinta i quatro", "mil i duzientos i trinta i quatro"):
            with self.subTest(text=text):
                self.assertEqual(read(text, "mwl"), [(text, "1234", C)])

    def test_the_long_scale(self):
        # 2 x 10^6 + 500 = 2000500; 10^12
        self.assertEqual(read("dous milhones i quinhentos", "mwl"),
                         [("dous milhones i quinhentos", "2000500", C)])
        self.assertEqual(read("un bilion", "mwl"), [("un bilion", "1000000000000", C)])

    def test_purmeiro_and_purmerio(self):
        self.assertEqual(read("purmeiro", "mwl"), [("purmeiro", "1", O)])
        self.assertEqual(read("bigésimo purmerio", "mwl"), [("bigésimo purmerio", "21", O)])

    def test_birgula_marks_the_decimals(self):
        self.assertEqual(read("un bírgula cinco", "mwl"), [("un bírgula cinco", "1.5", D)])


class TestRanges(unittest.TestCase):
    def test_the_two_limits_of_a_range_are_two_numbers(self):
        for lang, text, low, high in (("es", "entre veinte y treinta personas", "veinte", "treinta"),
                                      ("gl", "entre vinte e trinta persoas", "vinte", "trinta"),
                                      ("ca", "entre vint i trenta persones", "vint", "trenta"),
                                      ("ast", "ente venti y trenta persones", "venti", "trenta"),
                                      ("an", "entre vinte y trenta presonas", "vinte", "trenta"),
                                      ("oc", "entre vint e trenta personas", "vint", "trenta"),
                                      ("mwl", "antre binte i trinta pessonas", "binte", "trinta")):
            with self.subTest(lang=lang):
                # 20 and 30, not 20 + 30 = 50
                self.assertEqual(read(text, lang), [(low, "20", C), (high, "30", C)])


if __name__ == "__main__":
    unittest.main()
