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

    def test_a_listed_compound_is_one_token_with_any_mark_of_its_class(self):
        compounds = frozenset({"dètz-e-sèt"})
        for text in ("dètz-e-sèt", "dètz e sèt", "Dètz-e sèt"):
            with self.subTest(text=text):
                tokens = tokenize(text, compounds=compounds)
                self.assertEqual([(t.text, t.start, t.end, t.norm) for t in tokens],
                                 [(text, 0, 10, "dètz-e-sèt")])

    def test_an_apostrophe_and_a_middle_dot_join_only_their_own_class(self):
        compounds = frozenset({"bint'i un", "mil·lèsim"})
        self.assertEqual([t.norm for t in tokenize("bint’i un", compounds=compounds)], ["bint'i un"])
        self.assertEqual([t.norm for t in tokenize("mil.lèsim", compounds=compounds)], ["mil·lèsim"])
        self.assertEqual([t.norm for t in tokenize("bint-i un", compounds=compounds)], ["bint", "i", "un"])

    def test_a_space_after_an_apostrophe_and_each_apostrophe_sign(self):
        compounds = frozenset({"bint' uito", "bint'i un"})
        self.assertEqual([t.norm for t in tokenize("bint' uito", compounds=compounds)], ["bint' uito"])
        self.assertEqual([t.norm for t in tokenize("bint‘i un", compounds=compounds)], ["bint'i un"])
        self.assertEqual([t.norm for t in tokenize("bintʼi un", compounds=compounds)], ["bint'i un"])
        # a space next to a hyphen or a dot is no part of the mark
        self.assertEqual([t.norm for t in tokenize("dètz - e - sèt", compounds=frozenset({"dètz-e-sèt"}))],
                         ["dètz", "e", "sèt"])

    def test_a_dot_sign_between_letters_holds_one_word(self):
        words = frozenset({"tres", "mil"})
        for text in ("tres mil·límetres", "tres mil•límetres", "tres mil∙límetres"):
            with self.subTest(text=text):
                self.assertEqual([t.text for t in tokenize(text, number_words=words)], ["tres"])
        self.assertEqual([t.text for t in tokenize("tres mil", number_words=words)], ["tres", "mil"])

    def test_a_compound_keeps_the_gap_before_it(self):
        tokens = tokenize("a dètz e sèt", compounds=frozenset({"dètz-e-sèt"}))
        self.assertEqual([(t.text, t.gap) for t in tokens], [("a", ""), ("dètz e sèt", " ")])


if __name__ == "__main__":
    unittest.main()
