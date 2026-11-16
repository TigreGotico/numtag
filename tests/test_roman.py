"""Roman numerals: the value of each numeral, and when a numeral is one.

The rules are in docs/api.md, "Roman numerals". The expected values come
from an encoder written here with Python integers, apart from the package.
"""
import itertools
import unittest

from numtag import Form, Kind, Part, Reason, Role, tag_numbers
from numtag.roman import roman_value

_LETTERS = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
            (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def _encode(n: int) -> str:
    """The standard form of n, written greedily from the largest letter group."""
    out = ""
    for value, letters in _LETTERS:
        while n >= value:
            out += letters
            n -= value
    return out


def _read(text: str, lang: str) -> list[tuple]:
    return [(m.text, m.value, m.kind, m.reasons) for m in tag_numbers(text, lang) if m.form == Form.ROMAN]


SURE = frozenset()
HOMOGRAPH = frozenset({Reason.HOMOGRAPH})


class TestValue(unittest.TestCase):

    def test_every_standard_numeral_in_both_cases(self):
        for n in range(1, 4000):
            with self.subTest(n=n):
                self.assertEqual(roman_value(_encode(n)), str(n))
                self.assertEqual(roman_value(_encode(n).lower()), str(n))

    def test_no_other_string_of_letters_is_a_numeral(self):
        standard = {_encode(n) for n in range(1, 4000)}
        for size in range(1, 6):
            for letters in map("".join, itertools.product("IVXLCDM", repeat=size)):
                if letters not in standard:
                    with self.subTest(letters=letters):
                        self.assertIsNone(roman_value(letters))

    def test_mixed_case_and_empty_are_no_numeral(self):
        for word in ("", "Xiv", "xIV", "Mix"):
            with self.subTest(word=word):
                self.assertIsNone(roman_value(word))

    def test_unicode_number_forms(self):
        # The Unicode Standard 18.0, chapter 22, Number Forms: U+2160 to U+217F decompose to
        # the Latin letters; U+2180 to U+2188 have only a numeric value.
        cases = {"Ⅻ": "12", "ⅩⅣ": "14", "ⅻ": "12", "Ⅿ": "1000", "ↀ": "1000", "ↁ": "5000", "ↂ": "10000",
                 "ↅ": "6", "ↆ": "50", "ↇ": "50000", "ↈ": "100000", "Ↄ": None, "ↄ": None}
        for word, value in cases.items():
            with self.subTest(word=word):
                self.assertEqual(roman_value(word), value)


class TestPlanTable(unittest.TestCase):
    """The table in plans/number-tagger.md, "Roman numerals"."""

    def test_rows(self):
        rows = [
            ("Luís XIV reinou em França.", "pt-PT", [("XIV", "14", Kind.ORDINAL, SURE)]),
            ("Henry VIII had six wives.", "en", [("VIII", "8", Kind.ORDINAL, SURE)]),
            ("O papa Pio XII morreu.", "pt-PT", [("XII", "12", Kind.ORDINAL, SURE)]),
            ("no século XIX", "pt-PT", [("XIX", "19", Kind.ORDINAL, SURE)]),
            ("in the XXI century", "en", [("XXI", "21", Kind.ORDINAL, SURE)]),
            ("Lisez le chapitre IV.", "fr", [("IV", "4", Kind.ORDINAL, SURE)]),
            ("after World War II", "en", [("II", "2", Kind.ORDINAL, SURE)]),
            ("o Concílio Vaticano II", "pt-PT", [("II", "2", Kind.ORDINAL, SURE)]),
            ("Ⅻ", "en", [("Ⅻ", "12", Kind.CARDINAL, SURE)]),
            ("Edition XIV is out.", "en", [("XIV", "14", Kind.ORDINAL, SURE)]),
            ("see page XXI", "en", [("XXI", "21", Kind.CARDINAL, HOMOGRAPH)]),
            ("see page xxi", "en", []),
            ("XIV", "en", [("XIV", "14", Kind.CARDINAL, HOMOGRAPH)]),
            ("in MMXXV", "en", [("MMXXV", "2025", Kind.CARDINAL, HOMOGRAPH)]),
        ]
        for text, lang, expected in rows:
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), expected)

    def test_words_and_abbreviations_give_no_mention(self):
        for text in ("I think so.", "I bought a CD", "flights to DC", "send me a CV", "size XL", "MIX",
                     "did", "mix it", "civil", "Did you mix the civil case?"):
            with self.subTest(text=text):
                self.assertEqual(_read(text, "en"), [])

    def test_malformed_numerals_give_no_mention(self):
        for text in ("IIII", "IC", "VX", "MMMM", "Luís IIII", "século IC"):
            with self.subTest(text=text):
                self.assertEqual(_read(text, "pt-PT"), [])


class TestLettersThatAreWords(unittest.TestCase):
    """A single letter or a listed word reads only after a strong cue."""

    def test_strong_cues(self):
        rows = [
            ("King Henry I died in 1135.", "en", "I", "1"),
            ("Queen Elizabeth I never married.", "en", "I", "1"),
            ("the end of World War I", "en", "I", "1"),
            ("Read Part I first.", "en", "I", "1"),
            ("O rei D. Carlos I foi morto em Lisboa.", "pt-PT", "I", "1"),
            ("D. João I venceu em Aljubarrota.", "pt-PT", "I", "1"),
            ("O Papa Pio X morreu em 1914.", "pt-PT", "X", "10"),
        ]
        for text, lang, numeral, value in rows:
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [(numeral, value, Kind.ORDINAL, SURE)])

    def test_weak_cues_give_no_mention(self):
        rows = [
            ("Can I get a math fact", "en"),
            ("Play CD", "en"),
            ("Henry I died in 1135.", "en"),
            ("the reign of Henry I", "en"),
            ("Can you tell John I am late", "en"),
            ("Deputy Inspector General D K Arya said", "en"),
            ("turn it up, i can't hear", "en"),
            ("the war i fought", "en"),
            ("Pokaż mi swoją myślalkę", "pl"),
        ]
        for text, lang in rows:
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [])


class TestCueRules(unittest.TestCase):

    def test_lower_case_needs_a_series_noun_or_a_list_item(self):
        self.assertEqual(_read("no século xix", "pt-PT"), [("xix", "19", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("ii) a segunda alínea", "pt-PT"), [("ii", "2", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("(iv) quarto", "pt-PT"), [("iv", "4", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("Luís xiv", "pt-PT"), [])

    def test_a_list_of_numerals_shares_the_cue(self):
        self.assertEqual(_read("entre os séculos XI, XII e XIII", "pt-PT"),
                         [(n, v, Kind.ORDINAL, SURE) for n, v in (("XI", "11"), ("XII", "12"), ("XIII", "13"))])
        self.assertEqual(_read("durante los siglos XIX y XX", "es"),
                         [("XIX", "19", Kind.ORDINAL, SURE), ("XX", "20", Kind.ORDINAL, SURE)])

    def test_a_numeral_inside_a_word_is_none(self):
        self.assertEqual(_read("le grand palais de XI'an", "fr"), [])
        self.assertEqual(_read("Queen Elizabeth II's reign", "en"), [("II", "2", Kind.ORDINAL, SURE)])

    def test_a_number_word_keeps_its_word_reading(self):
        self.assertEqual([(m.value, m.form) for m in tag_numbers("MIL EUROS", "pt-PT")], [("1000", Form.WORDS)])
        self.assertEqual([(m.value, m.form) for m in tag_numbers("DIX EUROS", "fr")], [("10", Form.WORDS)])

    def test_the_numeral_is_one_part(self):
        [mention] = tag_numbers("Luís XIV", "pt-PT")
        self.assertEqual(mention.parts, (Part(Role.COUNT, (5, 8), "XIV", "14"),))


if __name__ == "__main__":
    unittest.main()
