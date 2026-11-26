"""Basque grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/eu.json."""
import unittest

import pytest
from helpers import read
from numtag import tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def eu(text: str) -> list[tuple[str, str, str]]:
    return read(text, "eu")


def confidence(text: str, lang: str) -> list[tuple[str, float]]:
    return [(m.text, m.confidence) for m in tag_numbers(text, lang)]


class TestVigesimalTens(unittest.TestCase):
    def test_a_ten_with_ta_takes_the_teens(self):
        # 20 + 10 = 30; 3 x 20 + 10 = 70; 4 x 20 + 19 = 99
        self.assertEqual(eu("hogeita hamar"), [("hogeita hamar", "30", C)])
        self.assertEqual(eu("hirurogeita hamar"), [("hirurogeita hamar", "70", C)])
        self.assertEqual(eu("laurogeita hemeretzi"), [("laurogeita hemeretzi", "99", C)])

    def test_a_ten_with_ta_is_no_number_alone(self):
        self.assertEqual(eu("hogeita"), [])


class TestOneAfterNoun(unittest.TestCase):
    def test_bat_after_the_noun_is_the_count_one(self):
        self.assertEqual(eu("milioi bat"), [("milioi bat", "1000000", C)])
        self.assertEqual(eu("dozena bat"), [("dozena bat", "12", C)])
        self.assertEqual(eu("heren bat"), [("heren bat", "1/3", F)])
        self.assertEqual(eu("erdi bat"), [("erdi bat", "0.5", F)])


class TestFractionArticle(unittest.TestCase):
    def test_the_article_a_after_erdi(self):
        # the half of an hour, of a kilo and of a litre: 1/2 = 0.5
        self.assertEqual(eu("erdia"), [("erdia", "0.5", F)])
        self.assertEqual(eu("ordu erdia"), [("erdia", "0.5", F)])
        self.assertEqual(eu("kilo erdia"), [("erdia", "0.5", F)])
        self.assertEqual(eu("litro erdia"), [("erdia", "0.5", F)])

    def test_the_article_a_after_laurden_and_heren(self):
        # 1/4 = 0.25; 1/3 stays a ratio
        self.assertEqual(eu("laurdena"), [("laurdena", "0.25", F)])
        self.assertEqual(eu("herena"), [("herena", "1/3", F)])

    def test_a_count_does_not_join_the_singular_article_form(self):
        # a count of two or more takes the plural: "bi herenak", so "bi herena" is no fraction
        for text in ("bi herena", "hiru laurdena"):
            with self.subTest(text=text):
                self.assertNotIn(text, [words for words, _, _ in eu(text)])

    def test_a_count_before_the_half_with_the_article(self):
        # 1 + 1/2 = 1.5
        self.assertEqual(eu("bat eta erdia"), [("bat eta erdia", "1.5", F)])
        self.assertEqual(eu("kilo bat eta erdia"), [("bat eta erdia", "1.5", F)])

    def test_the_article_form_is_a_homograph_like_the_bare_noun(self):
        # "erdi" is also "middle", "laurden" the quarter-final: the score is 0.4
        self.assertEqual(confidence("erdi", "eu"), [("erdi", 0.4)])
        self.assertEqual(confidence("erdia", "eu"), [("erdia", 0.4)])
        self.assertEqual(confidence("laurdena", "eu"), [("laurdena", 0.4)])
        self.assertEqual(confidence("herena", "eu"), [("herena", 0.4)])

    def test_a_count_with_the_bare_noun_stays_sure(self):
        self.assertEqual(confidence("hiru laurden", "eu"), [("hiru laurden", 1.0)])
        self.assertEqual(eu("bi heren"), [("bi heren", "2/3", F)])
        self.assertEqual(eu("hiru laurden"), [("hiru laurden", "0.75", F)])

    def test_a_quarter_final_is_no_number(self):
        self.assertEqual(eu("final-laurdena"), [])


class TestOrdinalEnding(unittest.TestCase):
    def test_garren_makes_the_cardinal_before_it_an_ordinal(self):
        # 20 + 1 = 21
        self.assertEqual(eu("bigarren"), [("bigarren", "2", O)])
        self.assertEqual(eu("hogeita batgarren"), [("hogeita batgarren", "21", O)])
        self.assertEqual(eu("ehungarren"), [("ehungarren", "100", O)])

    def test_the_article_a_after_an_ordinal(self):
        # the article joins the ordinal with no space: 1st to 10th
        expected = ["lehena", "bigarrena", "hirugarrena", "laugarrena", "bosgarrena", "seigarrena",
                    "zazpigarrena", "zortzigarrena", "bederatzigarrena", "hamargarrena"]
        for value, word in enumerate(expected, 1):
            with self.subTest(word=word):
                self.assertEqual(eu(word), [(word, str(value), O)])
        self.assertEqual(eu("hogeita batgarrena"), [("hogeita batgarrena", "21", O)])

    def test_bost_drops_its_last_letter_before_garren(self):
        self.assertEqual(eu("bosgarren"), [("bosgarren", "5", O)])
        self.assertEqual(eu("hamabosgarren"), [("hamabosgarren", "15", O)])


class TestGroups(unittest.TestCase):
    def test_eta_goes_before_the_last_part(self):
        # 1000 + 200 = 1200; 1000 + 200 + 1 = 1201
        self.assertEqual(eu("mila eta berrehun"), [("mila eta berrehun", "1200", C)])
        self.assertEqual(eu("mila berrehun eta bat"), [("mila berrehun eta bat", "1201", C)])

    def test_a_scale_noun_keeps_one_form_after_every_count(self):
        # 5 x 1000000 = 5000000
        self.assertEqual(eu("bost milioi"), [("bost milioi", "5000000", C)])

    def test_a_space_groups_digits(self):
        self.assertEqual(eu("1 000 000"), [("1 000 000", "1000000", C)])



class TestFractionAfterScale(unittest.TestCase):
    def test_a_fraction_after_a_scale_word_takes_a_part_of_it(self):
        # 1000000 / 2 = 500000; 1000000 / 3; 3 x 1000000 / 4 = 750000
        self.assertEqual(eu("milioi erdi bat"), [("milioi erdi bat", "500000", C)])
        self.assertEqual(eu("milioi-erdi bat"), [("milioi-erdi bat", "500000", C)])
        self.assertEqual(eu("milioi heren bat"), [("milioi heren bat", "1000000/3", F)])
        self.assertEqual(eu("hiru milioi laurden"), [("hiru milioi laurden", "750000", C)])


class TestHamazortzi(unittest.TestCase):
    def test_hamazortzi_is_the_second_form_of_eighteen(self):
        # 20 + 18 = 38
        self.assertEqual(eu("hamazortzi"), [("hamazortzi", "18", C)])
        self.assertEqual(eu("hogeita hamazortzi"), [("hogeita hamazortzi", "38", C)])
        self.assertEqual(eu("hamazortzigarren"), [("hamazortzigarren", "18", O)])


class TestArticleAfterNoun(unittest.TestCase):
    def test_bat_after_a_word_is_a_weak_number(self):
        self.assertEqual(confidence("Etxe bat.", "eu"), [("bat", 0.3)])
        self.assertEqual(confidence("Liburu bat erosi du.", "eu"), [("bat", 0.3)])

    def test_bat_after_a_hyphenated_noun_is_a_weak_number(self):
        self.assertEqual(confidence("Liburu-denda bat ireki dute.", "eu"), [("bat", 0.3)])

    def test_bat_with_no_word_before_it_is_a_number(self):
        self.assertEqual(confidence("Bat etorri da.", "eu"), [("Bat", 1.0)])


def reasons(text: str) -> list[tuple[str, str, float, list[str]]]:
    return [(m.text, m.value, m.confidence, [r.value for r in m.reasons]) for m in tag_numbers(text, "eu")]


class TestLoneFractionWord(unittest.TestCase):
    def test_a_lone_laurden_is_a_quarter_as_weak_as_a_lone_erdi(self):
        # 1/4 = 0.25 and 1/2 = 0.5, each with the homograph score
        self.assertEqual(reasons("erdi"), [("erdi", "0.5", 0.4, ["homograph"])])
        self.assertEqual(reasons("laurden"), [("laurden", "0.25", 0.4, ["homograph"])])

    def test_the_noun_before_the_quarter_is_no_part_of_the_number(self):
        # "ordu erdi" reads "erdi"; "ordu laurden" reads "laurden" the same way
        self.assertEqual(reasons("ordu erdi"), [("erdi", "0.5", 0.4, ["homograph"])])
        self.assertEqual(reasons("ordu laurden"), [("laurden", "0.25", 0.4, ["homograph"])])
        self.assertEqual(reasons("final laurden"), [("laurden", "0.25", 0.4, ["homograph"])])

    def test_a_lone_heren_is_a_weak_third(self):
        # "heren" is also the old ordinal "third": 1/3 with the homograph score
        self.assertEqual(reasons("heren"), [("heren", "1/3", 0.4, ["homograph"])])

    def test_a_count_or_bat_keeps_the_fraction_sure(self):
        self.assertEqual(reasons("laurden bat"), [("laurden bat", "0.25", 1.0, [])])
        self.assertEqual(reasons("hiru laurden"), [("hiru laurden", "0.75", 1.0, [])])
        self.assertEqual(reasons("bi heren"), [("bi heren", "2/3", 1.0, [])])
        # 1 + 1/4 = 1.25; 2 + 1/4 = 2.25
        self.assertEqual(reasons("bat eta laurdena"), [("bat eta laurdena", "1.25", 1.0, [])])
        self.assertEqual(reasons("bi eta laurden"), [("bi eta laurden", "2.25", 1.0, [])])

    def test_a_joiner_at_the_end_of_the_text_ends_the_number(self):
        # no word follows "eta", so no part adds to the 2
        self.assertEqual(eu("bi eta"), [("bi", "2", C)])

    def test_a_quarter_after_an_hour_of_the_clock_is_no_number(self):
        # Araua 35: "hirurak eta laurden" is a time; the hour word is no number word
        for text in ("bostak eta laurden", "hirurak eta laurden", "ordu bata eta laurden", "eta laurden"):
            with self.subTest(text=text):
                self.assertEqual(eu(text), [])


class TestAraua203Fractions(unittest.TestCase):
    # Euskaltzaindia, 203. araua, section 6: the table on p. 27, the
    # examples on p. 28, footnote 22 and note 28. The value is the fraction
    # the norm writes beside each phrase, worked out by hand.
    ROWS = [
        ("erdi bat", "0.5", F),  # 1/2
        ("heren bat", "1/3", F),
        ("laurden bat", "0.25", F),  # 1/4
        ("bosten bat", "0.2", F),  # 1/5
        ("seiren bat", "1/6", F),
        ("zazpiren bat", "1/7", F),
        ("zortziren bat", "0.125", F),  # 1/8
        ("bederatziren bat", "1/9", F),
        ("hamarren bat", "0.1", F),  # 1/10
        ("hamaikaren bat", "1/11", F),
        ("hamabiren bat", "1/12", F),
        ("hogeiren bat", "0.05", F),  # 1/20
        ("ehunen bat", "0.01", F),  # 1/100
        ("milaren bat", "0.001", F),  # 1/1000
        ("milioiren bat", "0.000001", F),  # 1/1000000
        ("bi heren", "2/3", F),
        ("hiru laurden", "0.75", F),  # 3/4
        ("zazpi zortziren", "0.875", F),  # 7/8
        ("zortzi hamarren", "0.8", F),  # 8/10
        ("hiru milioi laurden", "750000", C),  # 3000000/4
        ("hiru erdi", "1.5", F),  # 3/2, footnote 22
        ("bost heren", "5/3", F),  # footnote 23
        ("zazpi laurden", "1.75", F),  # 7/4, footnote 24
        ("bost hogeiren", "0.25", F),  # 5/20
        ("zazpi hirurogeiren", "7/60", F),
        ("bi ehunen", "0.02", F),  # 2/100
        ("sei milaren", "0.006", F),  # 6/1000
        ("bederatzi milioiren", "0.000009", F),  # 9/1000000
        ("hiru zati lau", "0.75", F),  # 3/4
        ("hamahiru zati berrogeita zazpi", "13/47", F),
        ("bat zati hiru", "1/3", F),
        ("bi milioi zati ehun eta bi", "1000000/51", F),  # 2000000/102
        ("milioi erdi bat", "500000", C),  # 1000000/2, note 28
        ("milioi heren bat", "1000000/3", F),
        ("milioi laurden bat", "250000", C),  # 1000000/4
        ("milioi bosten bat", "200000", C),  # 1000000/5
        ("milioi-erdi bat", "500000", C),
        ("milioi erdi", "500000", C),  # note 28: one compound noun, as "ordu laurden"
        ("zazpi hamarren", "0.7", F),  # 7/10
        ("bi bosten", "0.4", F),  # 2/5
        ("hogeita zazpi ehunen", "0.27", F),  # 27/100
        ("berrogeita hiru milaren", "0.043", F),  # 43/1000
        ("hogeita hamarren bat", "1/30", F),  # table, p. 27
        ("hamar milaren bat", "0.0001", F),  # table, p. 27: 1/10000
        ("hogeita bosten bat", "0.04", F),  # 1/25
        ("berrogeita bosten bat", "1/45", F),
        ("hiru milaren bat", "1/3000", F),  # the same rule: bat after a denominator of 3000
        ("ehun eta hogeita hamarren bat", "1/130", F),
    ]

    def test_each_fraction_of_the_norm(self):
        for text, value, kind in self.ROWS:
            with self.subTest(text=text):
                self.assertEqual(eu(text), [(text, value, kind)])

    def test_a_noun_after_the_compound(self):
        self.assertEqual(eu("milioi erdi euro"), [("milioi erdi", "500000", C)])

    def test_a_denominator_of_several_words_is_one_part_of_the_whole_number(self):
        self.assertEqual(eu("berrogeita bosten bat urte"), [("berrogeita bosten bat", "1/45", F)])
        self.assertEqual(eu("Hamar milaren bat euro."), [("Hamar milaren bat", "0.0001", F)])

    def test_a_word_with_ren_and_bat_is_also_about_that_number(self):
        # "ehunen bat film" is "about a hundred films" as well as one hundredth: both readings are common
        for text in ("ehunen bat film", "milaren bat langile", "hogeita hamarren bat", "hamar milaren bat"):
            with self.subTest(text=text):
                self.assertEqual([m.confidence for m in tag_numbers(text, "eu")], [0.4])
        # the irregular forms have no such reading
        self.assertEqual([m.confidence for m in tag_numbers("heren bat", "eu")], [1.0])
        # a count with no "bat" is no homograph
        self.assertEqual([m.confidence for m in tag_numbers("bi ehunen", "eu")], [1.0])

    def test_the_genitive_ren_alone_is_no_number(self):
        # "bosten artean" is "among five": the -(r)en word reads only with a count or "bat"
        self.assertEqual(eu("bosten artean"), [])


class TestAraua203Gaps(unittest.TestCase):
    # Rows of 203. araua that numtag does not read yet. Each test fails until
    # its issue is fixed; the expected value is the norm's, worked out by hand.

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/94")
    def test_the_denominator_in_the_ablative_before_the_count(self):
        self.assertEqual(eu("hamarretik zazpi"), [("hamarretik zazpi", "0.7", F)])  # 7/10

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/94")
    def test_the_denominator_in_the_plain_ablative(self):
        self.assertEqual(eu("bostetik bi"), [("bostetik bi", "0.4", F)])  # 2/5

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/94")
    def test_the_denominator_with_ko_before_the_count(self):
        self.assertEqual(eu("bosteko bi"), [("bosteko bi", "0.4", F)])  # 2/5

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/95")
    def test_unitate_eta_joins_the_whole_part_and_the_fraction(self):
        text = "hogeita lau unitate eta bost hamarren"  # 24 + 5/10
        self.assertEqual(eu(text), [(text, "24.5", D)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/95")
    def test_unitate_eta_after_zero(self):
        text = "zero unitate eta hogeita zazpi ehunen"  # 0 + 27/100
        self.assertEqual(eu(text), [(text, "0.27", D)])


class TestOpenIssues(unittest.TestCase):
    # Rows each open issue lists. The expected value is the issue's, worked out by hand.

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/231")
    def test_plural_article_on_the_denominator_herenak(self):
        self.assertEqual(read("bi herenak", "eu"), [("bi herenak", "2/3", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/231")
    def test_plural_article_on_the_denominator_laurdenek(self):
        self.assertEqual(read("hiru laurdenek", "eu"), [("hiru laurdenek", "0.75", F)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/232")
    def test_clock_hour_in_the_plural_absolutive(self):
        self.assertEqual(read("bostak", "eu"), [("bostak", "5", C)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/232")
    def test_clock_hour_in_the_plural_absolutive_hirurak(self):
        self.assertEqual(read("hirurak", "eu"), [("hirurak", "3", C)])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/232")
    def test_clock_hour_in_the_inessive(self):
        self.assertEqual(read("hiruretan", "eu"), [("hiruretan", "3", C)])


if __name__ == "__main__":
    unittest.main()
