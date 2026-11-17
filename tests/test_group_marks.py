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
