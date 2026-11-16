"""Romanian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/ro.json."""
import unittest

from helpers import read
from numtag import tag_numbers

C, O = "cardinal", "ordinal"


def ro(text: str) -> list[tuple[str, str, str]]:
    return read(text, "ro")


def confidence(text: str, lang: str) -> list[tuple[str, float]]:
    return [(m.text, m.confidence) for m in tag_numbers(text, lang)]


class TestCountOf(unittest.TestCase):
    def test_de_stands_between_a_count_from_twenty_and_its_scale_word(self):
        # 20 x 1000 = 20000; 200 x 1000 = 200000; 21 x 1000000 = 21000000
        self.assertEqual(ro("douăzeci de mii"), [("douăzeci de mii", "20000", C)])
        self.assertEqual(ro("două sute de mii"), [("două sute de mii", "200000", C)])
        self.assertEqual(ro("douăzeci și unu de milioane"), [("douăzeci și unu de milioane", "21000000", C)])


class TestScaleNouns(unittest.TestCase):
    def test_a_singular_scale_noun_takes_only_the_count_one(self):
        # 2 x 1000000 = 2000000; 2 x 1000 = 2000
        self.assertEqual(ro("două milioane"), [("două milioane", "2000000", C)])
        self.assertEqual(ro("două milion"), [("două", "2", C)])
        self.assertEqual(ro("două mii"), [("două mii", "2000", C)])


class TestLetters(unittest.TestCase):
    def test_a_cedilla_letter_reads_as_the_comma_letter(self):
        self.assertEqual(ro("şaisprezece"), [("şaisprezece", "16", C)])

    def test_spoken_and_variant_forms(self):
        self.assertEqual(ro("unșpe"), [("unșpe", "11", C)])
        self.assertEqual(ro("șasezeci"), [("șasezeci", "60", C)])
        for word, value in (("doișpe", "12"), ("douășpe", "12"), ("paișpe", "14"), ("șaișpe", "16"),
                            ("nouășpe", "19")):
            with self.subTest(word=word):
                self.assertEqual(ro(word), [(word, value, C)])


class TestOrdinals(unittest.TestCase):
    def test_lea_and_a_after_a_hyphen(self):
        self.assertEqual(ro("al 2-lea"), [("2-lea", "2", O)])
        self.assertEqual(ro("a 2-a"), [("2-a", "2", O)])

    def test_the_article_stays_outside_the_ordinal(self):
        self.assertEqual(ro("al doilea"), [("doilea", "2", O)])
        self.assertEqual(ro("a doua"), [("doua", "2", O)])



class TestOrdinalArticle(unittest.TestCase):
    def test_a_feminine_ordinal_needs_the_article(self):
        # "noua clădire" is "the new building"; "mia de lei" the 1000-lei note
        self.assertEqual(ro("noua clădire"), [])
        self.assertEqual(ro("mia de lei"), [])
        self.assertEqual(ro("a noua oară"), [("noua", "9", O)])
        self.assertEqual(ro("a mia oară"), [("mia", "1000", O)])
        # 20 + 9 = 29
        self.assertEqual(ro("a douăzeci și noua zi"), [("douăzeci și noua", "29", O)])
        # "de-a" is one hyphenated word that holds the article
        self.assertEqual(ro("cea de-a doua zi"), [("doua", "2", O)])

    def test_a_masculine_ordinal_needs_no_article(self):
        self.assertEqual(ro("doilea"), [("doilea", "2", O)])


class TestHomographs(unittest.TestCase):
    def test_noua_as_the_whole_text_is_nine(self):
        # a spoken answer: no clause ends after it
        self.assertEqual(confidence("nouă", "ro"), [("nouă", 1.0)])
        self.assertEqual(confidence("Nouă.", "ro"), [("Nouă", 0.4)])
        self.assertEqual(confidence("e nouă", "ro"), [("nouă", 0.4)])

    def test_noua_that_no_word_follows_may_be_new(self):
        self.assertEqual(confidence("tehnologie nouă", "ro"), [("nouă", 0.4)])
        self.assertEqual(confidence("tehnologie nouă și bună", "ro"), [("nouă", 0.4)])
        # an adjective goes before a joiner and a count as well
        self.assertEqual(confidence("o casă nouă și două mașini", "ro")[1], ("nouă", 0.4))
        self.assertEqual(confidence("o casă nouă și o mașină", "ro")[1], ("nouă", 0.4))
        self.assertEqual(confidence("nouă drumuri", "ro"), [("nouă", 1.0)])
        self.assertEqual(confidence("nouă sute", "ro"), [("nouă sute", 1.0)])


if __name__ == "__main__":
    unittest.main()
