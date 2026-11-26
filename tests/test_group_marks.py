"""Each lexicon's group and decimal marks against the CLDR latn number symbols.

CLDR 49.0.0 (unicode-org/cldr-json, cldr-numbers-full/main/<locale>/numbers.json,
main.<locale>.numbers.symbols-numberSystem-latn) gives (group, decimal) below;
pt-BR reads the "pt" file and fr-FR the "fr" file.
"""
import itertools
import unittest
from pathlib import Path

import numtag.lexicon
from numtag.lexicon import load
import pytest
from helpers import read

CLDR = {
    "ar": (",", "."), "ast": (".", ","), "az": (".", ","), "bg": (" ", ","), "ca": (".", ","), "ca-ES-valencia": (".", ","),
    "cs": (" ", ","), "da": (".", ","), "de": (".", ","), "el": (".", ","), "en": (",", "."),
    "es": (".", ","), "eo": ("\u202f", ","), "et": (" ", ","), "eu": (".", ","), "fa": (",", "."), "fi": (" ", ","),
    "fr-BE": (" ", ","), "fr-CH": ("'", ","), "fr-FR": (" ", ","), "fy": (".", ","),
    "gl": (" ", ","), "he": (",", "."), "hr": (".", ","), "hu": (" ", ","), "hi": (",", "."), "id": (".", ","),
    "it": (".", ","), "kab": (" ", ","), "lt": (" ", ","), "ms": (",", "."), "mt": (",", "."), "nb": (" ", ","),
    "nl": (".", ","), "nn": (" ", ","), "oc": (" ", ","), "pl": (" ", ","), "pt-BR": (".", ","),
    "pt-PT": (" ", ","), "ro": (".", ","), "ru": (" ", ","), "sk": (" ", ","),
    "sl": (".", ","), "sq": ("\xa0", ","), "sr": (".", ","), "sv": (" ", ","), "tr": (".", ","), "uk": (" ", ","),
}
#: Written pt and gl text groups digits with a dot ("1.500"), where CLDR gives a no-break space.
#: Each lexicon keeps the dot; the ruling is in docs/rulings.md.
DOT_EXCEPTIONS = {"cs": ".", "gl": ".", "oc": ".", "pt-PT": "."}
NO_BREAK_SPACE_LANGS = ("et", "fi", "hu", "lt", "nb", "nn", "sv")
#: CLDR 49.0.0 has no numbers file for Aragonese, and Mirandese has no CLDR locale.
NO_CLDR_DATA = ("an", "mwl")
#: A plain space, a no-break space and a narrow no-break space.
SPACES = (" ", "\u00a0", "\u202f")
LEXICONS = sorted(path.stem for path in Path(numtag.lexicon.__file__).parent.glob("*.json"))
SPACE_GROUP_LANGS = [lang for lang in LEXICONS if load(lang).space_groups]


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

    def test_every_lexicon_has_a_cldr_row_or_is_named_as_a_gap(self):
        self.assertEqual(sorted(set(LEXICONS) - set(CLDR)), list(NO_CLDR_DATA))
        self.assertEqual(sorted(set(CLDR) - set(LEXICONS)), [])

    def test_every_lexicon_that_groups_with_a_space_is_checked_for_mixed_marks(self):
        self.assertIn("sv", SPACE_GROUP_LANGS)
        self.assertEqual(sorted(set(NO_BREAK_SPACE_LANGS) - set(SPACE_GROUP_LANGS)), [])


class TestMixedMarks(unittest.TestCase):
    """One number may hold a plain space, a no-break space and a narrow no-break space,
    in any order. The value is the digits joined: 1 + 000 + 000 is 1000000."""

    def test_two_group_marks_in_any_order(self):
        for lang in SPACE_GROUP_LANGS:
            for first, second in itertools.product(SPACES, repeat=2):
                text = f"1{first}000{second}000"
                with self.subTest(lang=lang, first=first, second=second):
                    self.assertEqual(read(text, lang), [(text, "1000000", "cardinal")])

    def test_three_group_marks_in_any_order(self):
        for lang in SPACE_GROUP_LANGS:
            for marks in itertools.product(SPACES, repeat=3):
                text = "12" + "".join(f"{mark}{group}" for mark, group in zip(marks, ("345", "678", "901")))
                with self.subTest(lang=lang, marks=marks):
                    self.assertEqual(read(text, lang), [(text, "12345678901", "cardinal")])

    def test_mixed_marks_before_a_decimal(self):
        for lang in SPACE_GROUP_LANGS:
            if load(lang).decimal_mark != ",":
                continue
            for first, second in itertools.product(SPACES, repeat=2):
                text = f"1{first}000{second}000,5"
                with self.subTest(lang=lang, first=first, second=second):
                    self.assertEqual(read(text, lang), [(text, "1000000.5", "decimal")])


@pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/131")
@pytest.mark.parametrize("lang, text, expected", [
    ('fr-FR', 'le 10 000e visiteur', [('10 000e', "10000", "ordinal")]),
    ('fr-FR', 'le 10\u00a0000e visiteur', [('10\u00a0000e', "10000", "ordinal")]),
    ('ru', '10 000-й посетитель', [('10 000-й', "10000", "ordinal")]),
    ('ru', '10\u00a0000-й посетитель', [('10\u00a0000-й', "10000", "ordinal")]),
    ('sv', 'Han var den 10 000:e besökaren.', [('10 000:e', "10000", "ordinal")]),
    ('sv', 'Han var den 10\u00a0000:e besökaren.', [('10\u00a0000:e', "10000", "ordinal")]),
    ('fi', 'Hän oli museon 10 000. kävijä.', [('10 000', "10000", "ordinal")]),
    ('fi', 'Hän oli museon 10\u00a0000. kävijä.', [('10\u00a0000', "10000", "ordinal")]),
    ('hu', 'a 10 000. látogató', [('10 000', "10000", "ordinal")]),
    ('hu', 'a 10\u00a0000. látogató', [('10\u00a0000', "10000", "ordinal")]),
    ('et', '10 000. külastaja', [('10 000', "10000", "ordinal")]),
    ('et', '10\u00a0000. külastaja', [('10\u00a0000', "10000", "ordinal")]),
])
def test_a_grouped_digit_ordinal_is_one_ordinal(lang, text, expected):
    assert read(text, lang) == expected
