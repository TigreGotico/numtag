"""Greek grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/el.json."""
import unicodedata
import unittest

from helpers import read, sure

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def el(text: str) -> list[tuple[str, str, str]]:
    return read(text, "el")


class TestGreek(unittest.TestCase):
    def test_ekato_after_tois_and_a_number_is_the_percent_sign(self):
        for text in ("δύο τοις εκατό", "δύο τοις εκατόν", "δύο τα εκατό", "ΔΥΟ ΤΟΙΣ ΕΚΑΤΟ"):
            with self.subTest(text=text):
                self.assertEqual([v for _, v, _ in read(text, "el")], ["2"])

    def test_tens_and_units_take_no_joiner(self):
        # 20 + 3 = 23; 1000 + 900 + 80 + 4 = 1984
        self.assertEqual(el("είκοσι τρία"), [("είκοσι τρία", "23", C)])
        self.assertEqual(el("χίλια εννιακόσια ογδόντα τέσσερα"), [("χίλια εννιακόσια ογδόντα τέσσερα", "1984", C)])

    def test_gender_and_case_forms_read_the_same(self):
        # τρεις (m/f) and τρία (n) are 3; τριών is the genitive
        self.assertEqual(el("τρεις γυναίκες"), [("τρεις", "3", C)])
        self.assertEqual(el("τριών ετών"), [("τριών", "3", C)])
        # 3 x 1000 + 200 = 3200, with feminine hundreds before χιλιάδες
        self.assertEqual(el("τρεις χιλιάδες διακόσιες"), [("τρεις χιλιάδες διακόσιες", "3200", C)])

    def test_bound_hundred_needs_the_rest(self):
        # εκατόν stands only before the rest: 100 + 1 = 101
        self.assertEqual(el("εκατόν ένα"), [("εκατόν ένα", "101", C)])
        self.assertEqual(el("εκατό"), [("εκατό", "100", C)])

    def test_plural_thousands_need_a_count(self):
        # 2 x 1000 + 25 = 2025; χιλιάδες alone is no number
        self.assertEqual(el("δύο χιλιάδες είκοσι πέντε"), [("δύο χιλιάδες είκοσι πέντε", "2025", C)])
        self.assertEqual(el("χιλιάδες άνθρωποι"), [])

    def test_a_unit_and_a_half_in_one_word(self):
        # δυόμισι = 2 + 1/2; δυόμισι χιλιάδες = 2.5 x 1000 = 2500
        self.assertEqual(el("δυόμισι κιλά"), [("δυόμισι", "2.5", F)])
        self.assertEqual(el("δυόμισι χιλιάδες"), [("δυόμισι χιλιάδες", "2500", C)])

    def test_fractions_agree_with_the_numerator(self):
        # ένα τρίτο = 1/3; δύο τρίτα = 2/3
        self.assertEqual(el("ένα τρίτο"), [("ένα τρίτο", "1/3", F)])
        self.assertEqual(el("δύο τρίτα"), [("δύο τρίτα", "2/3", F)])

    def test_every_word_of_an_ordinal_is_ordinal(self):
        # 20 + 1 = 21
        self.assertEqual(el("ο εικοστός πρώτος αιώνας"), [("εικοστός πρώτος", "21", O)])
        self.assertEqual(el("η 3η θέση"), [("3η", "3", O)])

    def test_a_word_with_no_accent_reads_without_marks(self):
        # "εικοσι ενα" typed without accents is 20 + 1; "εκτός" (except),
        # written with its accent, is no "έκτος" (sixth)
        self.assertEqual(el("εικοσι ενα"), [("εικοσι ενα", "21", C)])
        self.assertEqual(el("ΤΡΙΑ ΒΙΒΛΙΑ"), [("ΤΡΙΑ", "3", C)])
        self.assertEqual(el("όλοι εκτός από μένα"), [])

    def test_decimal_comma(self):
        # 1234567 + 0.89
        self.assertEqual(el("1.234.567,89 ευρώ"), [("1.234.567,89", "1234567.89", D)])
        self.assertEqual(el("δύο κόμμα πέντε"), [("δύο κόμμα πέντε", "2.5", D)])

    def test_scale_words(self):
        # 3 x 10^6 = 3000000; 2 x 10^9
        self.assertEqual(el("τρία εκατομμύρια"), [("τρία εκατομμύρια", "3000000", C)])
        self.assertEqual(el("2 δις ευρώ"), [("2 δις", "2000000000", C)])

    def test_a_scale_noun_agrees_with_its_count(self):
        # one takes the singular, two the plural: 2 x 10^6; "δύο εκατομμύριο"
        # is no million
        self.assertEqual(el("ένα εκατομμύριο"), [("ένα εκατομμύριο", "1000000", C)])
        self.assertEqual(el("δύο εκατομμύρια"), [("δύο εκατομμύρια", "2000000", C)])
        self.assertEqual(el("δύο εκατομμύριο"), [("δύο", "2", C)])

    def test_the_abbreviated_scale_words_take_any_count(self):
        # el.wiktionary δις: "{{ακλ}}", indeclinable; 10^9, 10^9 / 2, 2 x 10^9, 10^12
        self.assertEqual(el("ένα δις ευρώ"), [("ένα δις", "1000000000", C)])
        self.assertEqual(el("μισό δις ευρώ"), [("μισό δις", "500000000", C)])
        self.assertEqual(el("δύο δις ευρώ"), [("δύο δις", "2000000000", C)])
        self.assertEqual(el("ένα τρις"), [("ένα τρις", "1000000000000", C)])


    def test_decomposed_accents_read_as_composed(self):
        # NFD text: "έ" as "ε" and a combining acute
        text = unicodedata.normalize("NFD", "ο έκτος όροφος")
        self.assertEqual(el(text), [(unicodedata.normalize("NFD", "έκτος"), "6", O)])
    def test_the_genitive_scale_nouns_shift_the_stress(self):
        # 2 x 10^6; 3 x 10^9; 1 x 10^6; Wiktionary also lists the unshifted form
        self.assertEqual(el("ύψους δύο εκατομμυρίων ευρώ"), [("δύο εκατομμυρίων", "2000000", C)])
        self.assertEqual(el("τριών δισεκατομμυρίων"), [("τριών δισεκατομμυρίων", "3000000000", C)])
        self.assertEqual(el("ενός εκατομμυρίου"), [("ενός εκατομμυρίου", "1000000", C)])
        self.assertEqual(el("δύο εκατομμύριων"), [("δύο εκατομμύριων", "2000000", C)])

    def test_weekdays_and_except_are_low_confidence(self):
        # Τρίτη is Tuesday or the 3rd; ΕΚΤΟΣ is "except" or the 6th; τρίτος is only the 3rd
        self.assertEqual(sure("την Τρίτη το πρωί", "el"), [("Τρίτη", "3", 0.4)])
        self.assertEqual(sure("ΕΚΤΟΣ ΑΠΟ ΑΥΤΟ", "el"), [("ΕΚΤΟΣ", "6", 0.4)])
        self.assertEqual(sure("ο τρίτος όροφος", "el"), [("τρίτος", "3", 1.0)])
        self.assertEqual(sure("η έκτη θέση", "el"), [("έκτη", "6", 1.0)])


if __name__ == "__main__":
    unittest.main()
