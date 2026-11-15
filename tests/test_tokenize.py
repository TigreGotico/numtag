import unittest

from numtag.tokenize import tokenize


def words(text: str, suffixes=frozenset()) -> list[tuple[str, int, int]]:
    return [(t.text, t.start, t.end) for t in tokenize(text, suffixes)]


class TestTokenize(unittest.TestCase):
    def test_offsets_slice_the_text(self):
        text = "Comprou duas dúzias, e mais 1.000,5!"
        tokens = tokenize(text)
        self.assertEqual([t.text for t in tokens], ["Comprou", "duas", "dúzias", "e", "mais", "1.000,5"])
        for token in tokens:
            self.assertEqual(text[token.start:token.end], token.text)

    def test_edge_punctuation_is_not_part_of_a_word(self):
        self.assertEqual(words("(dois)."), [("dois", 1, 5)])

    def test_digit_strings_keep_their_marks(self):
        self.assertEqual(words("1,000,000.5 e 2.5."), [("1,000,000.5", 0, 11), ("e", 12, 13), ("2.5", 14, 17)])

    def test_hyphenated_compounds_split_with_offsets(self):
        tokens = tokenize("twenty-one")
        self.assertEqual([(t.text, t.start, t.end, t.gap) for t in tokens],
                         [("twenty", 0, 6, ""), ("one", 7, 10, "-")])
        self.assertTrue(tokens[1].links_to_previous())

    def test_punctuation_breaks_the_link(self):
        tokens = tokenize("dois, três")
        self.assertFalse(tokens[1].links_to_previous())

    def test_ordinal_suffix_glues_to_digits(self):
        tokens = tokenize("o 1.º e 21st", frozenset({"º", "st"}))
        self.assertEqual([(t.text, t.suffix, t.digits) for t in tokens],
                         [("o", "", "o"), ("1.º", "º", "1"), ("e", "", "e"), ("21st", "st", "21")])

    def test_minus_sign_only_at_the_start_of_a_word(self):
        self.assertEqual([t.text for t in tokenize("-5 e 5-7")], ["-5", "e", "5", "7"])

    def test_only_ascii_digits_make_a_digit_string(self):
        # Arabic-Indic, fullwidth and Devanagari digits, alone or mixed with
        # ASCII digits, are no token and break the link between the words
        for text in ("٣", "３", "१२", "1٣", "٣1", "12３4"):
            with self.subTest(text=text):
                tokens = tokenize(f"tenho {text} maçãs")
                self.assertEqual([t.text for t in tokens], ["tenho", "maçãs"])
                self.assertFalse(tokens[1].links_to_previous())

    def test_digits_glued_to_a_word_are_dropped(self):
        self.assertEqual([t.text for t in tokenize("mp3 player")], ["mp", "player"])


if __name__ == "__main__":
    unittest.main()
