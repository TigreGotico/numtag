"""Each lexicon's group and decimal marks against the CLDR latn number symbols.

CLDR 49.0.0 (unicode-org/cldr-json, cldr-numbers-full/main/<locale>/numbers.json,
main.<locale>.numbers.symbols-numberSystem-latn) gives (group, decimal) below;
pt-BR reads the "pt" file and fr-FR the "fr" file.
"""
import unittest

from numtag.lexicon import load
from helpers import read

CLDR = {
    "ar": (",", "."), "ast": (".", ","), "az": (".", ","), "bg": (" ", ","), "ca": (".", ","),
    "cs": (" ", ","), "da": (".", ","), "de": (".", ","), "el": (".", ","), "en": (",", "."),
    "es": (".", ","), "et": (" ", ","), "eu": (".", ","), "fa": (",", "."), "fi": (" ", ","),
    "fr-BE": (" ", ","), "fr-CH": ("'", ","), "fr-FR": (" ", ","), "fy": (".", ","),
    "gl": (" ", ","), "he": (",", "."), "hr": (".", ","), "hu": (" ", ","), "id": (".", ","),
    "it": (".", ","), "kab": (" ", ","), "nb": (" ", ","), "nl": (".", ","),
    "nn": (" ", ","), "oc": (" ", ","), "pl": (" ", ","), "pt-BR": (".", ","),
    "pt-PT": (" ", ","), "ro": (".", ","), "ru": (" ", ","), "sk": (" ", ","),
    "sl": (".", ","), "sv": (" ", ","), "tr": (".", ","), "uk": (" ", ","),
}
#: Written pt and gl text groups digits with a dot ("1.500"), where CLDR gives a no-break space.
#: Each lexicon keeps the dot; the ruling is in docs/rulings.md.
DOT_EXCEPTIONS = {"cs": ".", "gl": ".", "oc": ".", "pt-PT": "."}
NO_BREAK_SPACE_LANGS = ("et", "fi", "hu", "nb", "nn", "sv")


class TestGroupMarks(unittest.TestCase):
    def test_group_mark_follows_cldr_except_the_named_dot_languages(self):
        for lang, (group, _) in CLDR.items():
            with self.subTest(lang=lang):
                self.assertEqual(load(lang).group_mark, DOT_EXCEPTIONS.get(lang, group))

    def test_each_exception_differs_from_cldr(self):
        for lang, mark in DOT_EXCEPTIONS.items():
            with self.subTest(lang=lang):
                self.assertNotEqual(CLDR[lang][0], mark)

    def test_decimal_mark_follows_cldr(self):
        for lang, (_, decimal) in CLDR.items():
            with self.subTest(lang=lang):
                self.assertEqual(load(lang).decimal_mark, decimal)

    def test_a_plain_space_and_a_no_break_space_both_group_digits(self):
        for lang in NO_BREAK_SPACE_LANGS:
            for mark in (" ", " "):
                with self.subTest(lang=lang, mark=mark):
                    text = f"Han fick 1{mark}234{mark}567 stk."
                    self.assertEqual(read(text, lang), [(f"1{mark}234{mark}567", "1234567", "cardinal")])


class TestGroupedDigitOrdinals(unittest.TestCase):
    """The suffix on the last group marks the whole number as an ordinal.
    Vikidia, "Vikidia:10 000e article", writes "c'est donc bien Fusée qui est
    le 10 000ème article": 10 000 + "ème" is the ten-thousandth. Each
    suffix is the lexicon's own, with its source there."""

    ROWS = (("fr-FR", "le 10{}000e visiteur", "10{}000e"), ("fr-FR", "le 10{}000ème article", "10{}000ème"),
            ("ru", "10{}000-й посетитель", "10{}000-й"), ("sv", "Han var den 10{}000:e besökaren.", "10{}000:e"),
            ("fi", "Hän oli museon 10{}000. kävijä.", "10{}000"), ("hu", "a 10{}000. látogató", "10{}000"),
            ("et", "10{}000. külastaja", "10{}000"))

    def test_a_space_or_the_group_mark_before_the_last_group(self):
        for lang, text, span in self.ROWS:
            for mark in (" ", " ", load(lang).group_mark):
                with self.subTest(lang=lang, mark=mark):
                    self.assertEqual(read(text.format(mark), lang), [(span.format(mark), "10000", "ordinal")])

    def test_every_group_before_the_suffix_counts(self):
        self.assertEqual(read("le 1 000 000e jour", "fr-FR"), [("1 000 000e", "1000000", "ordinal")])
        self.assertEqual(read("the 10,000th visitor", "en"), [("10,000th", "10000", "ordinal")])

    def test_a_group_of_other_than_three_digits_is_another_number(self):
        self.assertEqual(read("page 10 2e ligne", "fr-FR"), [("10", "10", "cardinal"), ("2e", "2", "ordinal")])

    def test_a_german_period_after_groups_needs_its_cue(self):
        # the cue counts from the first group: "der" makes the period an ordinal mark;
        # five digits with no cue end a sentence
        self.assertEqual(read("der 10 000. Besucher", "de"), [("10 000", "10000", "ordinal")])
        self.assertEqual(read("Es waren 10 000. Danach kam er.", "de"), [("10 000", "10000", "cardinal")])
