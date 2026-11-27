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
            ("Queen Elizabeth I. Then she died.", "en", "I", "1"),
            ("Pope John Paul I", "en", "I", "1"),
            ("el rey Juan Carlos I abdicó", "es", "I", "1"),
            ("Dom Pedro I proclamou a independência.", "pt-BR", "I", "1"),
            ("Papa Giovanni Paolo I", "it", "I", "1"),
            ("il re Umberto I fu ucciso", "it", "I", "1"),
            ("Dona Maria I morreu no Rio.", "pt-PT", "I", "1"),
            ("no século I", "pt-PT", "I", "1"),
            ("en el siglo V", "es", "V", "5"),
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
            ("I told Mary Jane I would come", "en"),
            ("We went to New York I think", "en"),
            ("Hi. Tell John I am late.", "en"),
            ("It was Tom. Henry I died.", "en"),
            ("Give IV fluids", "en"),
            ("Henry IV of France was king.", "en"),
            ("I met the King. Then I left.", "en"),
            ("God save the Queen. Now I can sleep.", "en"),
            ("the king\nMary I am late", "en"),
            ("The king, John I think, was weak.", "en"),
            ("Ask the king if I can go", "en"),
            ("Pope john Paul I", "en"),
            ("King Henry I K Smith", "en"),
            ("I met King Charles. Then I left.", "en"),
            ("Dear Queen Elizabeth\nI am writing to you", "en"),
        ]
        for text, lang in rows:
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [])


class TestWordLists(unittest.TestCase):
    """Units, sizes, pronouns and verb forms on a language's word list give
    no mention without a strong cue, in any case."""

    def test_listed_words_give_no_mention(self):
        rows = [("Tamanho XL", "pt-PT"), ("FILME DE 35 MM", "pt-PT"), ("O capítulo li ontem.", "pt-PT"),
                ("A parte di ao João.", "pt-PT"), ("Talla XL", "es"), ("Pon MI canción", "es"),
                ("el capítulo di ayer", "es"), ("Je veux la taille XL", "fr"), ("Il est MI temps", "fr"),
                ("Ich brauche Größe XL.", "de"), ("MIX", "de"), ("NELLA GIORNATA DI LUNEDÌ", "it"),
                ("CI SONO", "it"), ("Taglia XL", "it"), ("Essa parte vi ontem.", "pt-PT"),
                ("Esa parte vi ayer.", "es")]
        for text, lang in rows:
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [])

    def test_french_words_and_unit_symbols_give_no_mention(self):
        # "mix" a mixing, "MC" a rapper, "cc" a copy, "cl" and "dl" centilitre and decilitre
        for text in ("MIX de sons", "Le MIX de sons", "Le MC monte sur scène.", "En CC de ce courriel",
                     "UNE BOUTEILLE DE 75 CL", "Ajoutez 2 DL de lait."):
            with self.subTest(text=text):
                self.assertEqual([m for m in _read(text, "fr") if m[0] in ("MIX", "MC", "CC", "CL", "DL")], [])

    def test_french_numerals_still_read(self):
        # 1000 + 900 + 90 + 9 = 1999; 2000 + 20 + 4 = 2024; the regnal 14; the chapter 1100
        self.assertEqual(_read("MCMXCIX", "fr"), [("MCMXCIX", "1999", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("MMXXIV", "fr"), [("MMXXIV", "2024", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("Louis XIV", "fr"), [("XIV", "14", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("le chapitre MC", "fr"), [("MC", "1100", Kind.ORDINAL, SURE)])

    def test_a_lower_case_word_leaves_the_upper_case_numeral(self):
        for text, lang in (("Felipe VI", "es"), ("Alfonso VI conquistó Toledo.", "es"), ("Paolo VI", "it"),
                           ("Papa Paolo VI", "it"), ("D. João VI", "pt-PT")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [("VI", "6", Kind.ORDINAL, SURE)])
        for text, lang in (("EU VI UMA CENA", "pt-PT"), ("VI ASSICURIAMO", "it")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [("VI", "6", Kind.CARDINAL, HOMOGRAPH)])

    def test_plural_series_nouns(self):
        for text, lang in (("les actes II et III", "fr"), ("les parties II et III", "fr"), ("les scènes II et III", "fr"),
                           ("os atos II e III", "pt-PT"), ("as cenas II e III", "pt-PT"),
                           ("los actos II y III", "es"), ("las escenas II y III", "es")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [("II", "2", Kind.ORDINAL, SURE), ("III", "3", Kind.ORDINAL, SURE)])


class TestEnglishSeriesNouns(unittest.TestCase):
    """In English "I" is a pronoun, so a series noun before a single letter
    or a listed word counts only in title case."""

    def test_lower_case_series_noun_gives_no_mention(self):
        for text in ("the part I like", "Turn up the volume I can't hear it", "Which chapter I should read next?",
                     "What century I was born in", "THE BEST PART I THINK IS THIS"):
            with self.subTest(text=text):
                self.assertEqual(_read(text, "en"), [])

    def test_a_numeral_that_is_no_word_keeps_the_lower_case_noun(self):
        self.assertEqual(_read("in the XXI century", "en"), [("XXI", "21", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("read chapter XII", "en"), [("XII", "12", Kind.ORDINAL, SURE)])


class TestSingleLetters(unittest.TestCase):
    """A single letter is a numeral only as I, V or X."""

    def test_labels_give_no_mention(self):
        for text, lang in (("Medicare Part D covers drugs.", "en"), ("Fill in Part C of the form.", "en"),
                           ("Take Vitamin C", "en"), ("o Dia D", "pt-PT"), ("o século L", "pt-PT")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [])

    def test_a_list_does_not_lend_its_cue_to_a_letter(self):
        self.assertEqual(_read("D. João V e D. Maria I", "pt-PT"),
                         [("V", "5", Kind.ORDINAL, SURE), ("I", "1", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("After World War I, I moved to Paris.", "en"), [("I", "1", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("Henry VIII and I went to the shops.", "en"), [("VIII", "8", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("World War I, II and III", "en"),
                         [(n, v, Kind.ORDINAL, SURE) for n, v in (("I", "1"), ("II", "2"), ("III", "3"))])


class TestGerman(unittest.TestCase):
    """German writes every noun in title case, so only series nouns and
    regnal titles are cues."""

    def test_a_noun_is_no_cue(self):
        self.assertEqual(_read("Ich brauche Größe XIV.", "de"), [("XIV", "14", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("Ludwig XIV", "de"), [("XIV", "14", Kind.CARDINAL, HOMOGRAPH)])

    def test_series_nouns_and_titles(self):
        self.assertEqual(_read("im XIX. Jahrhundert", "de"), [("XIX", "19", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("das XIX Jahrhundert", "de"), [("XIX", "19", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("Papst Benedikt XVI", "de"), [("XVI", "16", Kind.ORDINAL, SURE)])
        self.assertEqual(_read("im Zweiten Weltkrieg Teil II", "de"), [("II", "2", Kind.ORDINAL, SURE)])


class TestCueRules(unittest.TestCase):

    def test_the_cue_word_stands_right_before_the_numeral(self):
        self.assertEqual(_read("(Louis) XIV", "en"), [("XIV", "14", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("Henry, VIII", "en"), [("VIII", "8", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("THE BEST XIV", "en"), [("XIV", "14", Kind.CARDINAL, HOMOGRAPH)])

    def test_a_list_item_opens_a_line(self):
        self.assertEqual(_read("Notas:\nii) a segunda", "pt-PT"), [("ii", "2", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("veja a nota ii) abaixo", "pt-PT"), [])

    def test_a_numeral_beside_digits_is_a_code(self):
        for text, lang in (("My Mazda CX5 is red", "en"), ("a Yamaha DX7 synth", "en"), ("Quero tamanho 3XL", "pt-PT"),
                           ("Ich brauche 2XL", "de")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [])

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



class TestTitleCaseBound(unittest.TestCase):
    """A title-case word is a cue only for a numeral below 100."""

    def test_a_large_numeral_after_a_name_is_a_weak_cardinal(self):
        # MDCC = 1700, DIV = 504, MMXXIV = 2024, MD = 1500
        for text, lang, numeral, value in (("Le PDG de Total MDCC", "fr-FR", "MDCC", "1700"),
                                           ("Ce DIV", "fr-FR", "DIV", "504"),
                                           ("In MMXXIV we moved.", "en", "MMXXIV", "2024"),
                                           ("Ce MD", "fr-FR", "MD", "1500")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [(numeral, value, Kind.CARDINAL, HOMOGRAPH)])

    def test_dc_is_a_french_word(self):
        self.assertEqual(_read("Il habite à Washington DC.", "fr-FR"), [])

    def test_names_and_series_nouns_keep_their_ordinal(self):
        # XIV = 14, IV = 4, III = 3, IX = 9, XXIII = 23, II = 2, LVIII = 58, LXXII = 72
        for text, lang, numeral, value in (
                ("Louis XIV", "fr-FR", "XIV", "14"), ("Henri IV", "fr-FR", "IV", "4"),
                ("Napoléon III", "fr-FR", "III", "3"), ("Pie IX", "fr-FR", "IX", "9"),
                ("Jean XXIII", "fr-FR", "XXIII", "23"), ("Chapitre IV", "fr-FR", "IV", "4"),
                ("acte III", "fr-FR", "III", "3"), ("Élisabeth II", "fr-FR", "II", "2"),
                ("Super Bowl LVIII", "en", "LVIII", "58"), ("Prince Henry LXXII", "en", "LXXII", "72"),
                ("le roi Louis MDCC", "fr-FR", "MDCC", "1700"), ("au chapitre CXX", "fr-FR", "CXX", "120")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [(numeral, value, Kind.ORDINAL, SURE)])


class TestPsalms(unittest.TestCase):
    def test_a_psalm_number_is_an_ordinal(self):
        # CXIX = 119, CL = 150
        for text, lang, numeral, value in (("Psaume CXIX", "fr-FR", "CXIX", "119"), ("le psaume CL", "fr-FR", "CL", "150"),
                                           ("Psalm CXIX", "en", "CXIX", "119"), ("the psalms CXX", "en", "CXX", "120")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [(numeral, value, Kind.ORDINAL, SURE)])


class TestHyphenatedNames(unittest.TestCase):
    """A hyphenated given name gives no token and is one title-case word."""

    def test_a_hyphenated_name_is_a_title_case_cue(self):
        # II = 2
        for text, lang in (("Jean-Paul II", "fr-FR"), ("le pape Jean-Paul II est mort", "fr-FR"),
                           ("(Jean-Paul II)", "fr-FR"), ("John-Paul II", "en")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [("II", "2", Kind.ORDINAL, SURE)])

    def test_a_regnal_title_before_a_hyphenated_name_reads_a_single_letter(self):
        # I = 1
        for text, lang in (("le pape Jean-Paul I", "fr-FR"), ("Pope John-Paul I", "en"),
                           ("le pape Jean-Paul Louis I", "fr-FR"), ("le pape Jean Paul I", "fr-FR")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, lang), [("I", "1", Kind.ORDINAL, SURE)])

    def test_a_hyphenated_word_that_is_no_name_is_no_cue(self):
        # a lower-case part is no name; a single letter needs a regnal title
        self.assertEqual(_read("les pays-Bas II", "fr-FR"), [("II", "2", Kind.CARDINAL, HOMOGRAPH)])
        self.assertEqual(_read("Marie-Thérèse I", "fr-FR"), [])


class TestFrenchOrdinalSuffix(unittest.TestCase):
    """fr writes the ordinal suffixes of digits after a Roman numeral ("XXe", "Ier")."""

    def test_the_numeral_and_its_suffix_are_one_ordinal(self):
        # XX = 20, XIX = 19, XVI = 16, V = 5, III = 3, I = 1, II = 2
        rows = [
            ("au XXe siècle", "XXe", "20", None), ("le XIXe", "XIXe", "19", None),
            ("au XIXème siècle", "XIXème", "19", None), ("au XIXᵉ siècle", "XIXᵉ", "19", None),
            ("le XVIe arrondissement", "XVIe", "16", None), ("la Ve République", "Ve", "5", None),
            ("le IIIe Reich", "IIIe", "3", None), ("François Ier", "Ier", "1", "masculine"),
            ("la Ire République", "Ire", "1", "feminine"), ("la IIde République", "IIde", "2", "feminine"),
            ("le Xe arrondissement", "Xe", "10", None), ("au Xe siècle", "Xe", "10", None),
            ("les IXe et Xe siècles", "Xe", "10", None), ("Jean-Paul Ier", "Ier", "1", "masculine"),
            ("le XLe chapitre", "XLe", "40", None),
            ("les XIXes siècles", "XIXes", "19", None), ("L’EUROPE AU XXe SIÈCLE", "XXe", "20", None),
        ]
        for text, numeral, value, gender in rows:
            with self.subTest(text=text):
                self.assertEqual([(m.text, m.value, m.kind, m.reasons, m.gender, m.confidence)
                                  for m in tag_numbers(text, "fr-FR") if m.form == Form.ROMAN][-1:],
                                 [(numeral, value, Kind.ORDINAL, SURE, gender, 1.0)])

    def test_a_single_letter_with_a_suffix_and_no_cue_is_weak(self):
        # "Ire" is also "ire" (anger); I = 1, V = 5
        for text, numeral, value in (("Ire et colère le saisirent.", "Ire", "1"), ("Ve", "Ve", "5")):
            with self.subTest(text=text):
                self.assertEqual(_read(text, "fr-FR"), [(numeral, value, Kind.ORDINAL, HOMOGRAPH)])

    def test_a_listed_word_with_a_suffix_needs_a_cue(self):
        # "Xe" is the symbol of xenon, "Cie" the abbreviation of compagnie
        for text in ("Le xénon (Xe) est un gaz noble.", "Xe, Ar et Kr", "Le symbole Xe désigne le xénon.", "CIe",
                     "MMe", "Les XLe"):
            with self.subTest(text=text):
                self.assertEqual(_read(text, "fr-FR"), [])

    def test_the_mention_spans_the_numeral_and_the_suffix(self):
        [mention] = tag_numbers("au XXe siècle", "fr-FR")
        self.assertEqual((mention.char_span, mention.form), ((3, 6), Form.ROMAN))

    def test_words_that_look_like_a_numeral_and_a_suffix_give_no_mention(self):
        # "er" follows only 1 ("Vers", "Ver"); L, C, D and M alone are no
        # numeral ("Le", "Ce", "De", "Me", "Mes"); "mm" is a word ("MMe");
        # the suffix is lower case ("XXE"), and a lower-case numeral takes none
        for text in ("Vers midi", "Ver de terre", "Le chat", "Ce soir", "De plus", "Me Durand", "Mes amis",
                     "MMe", "XXE", "xxe", "Vies", "Ides"):
            with self.subTest(text=text):
                self.assertEqual(_read(text, "fr-FR"), [])

    def test_a_language_without_the_setting_reads_no_suffix(self):
        # en lists "st" and "th" for digits, but "XXth" is no English form; tr
        # lists "inci", and "Vinci" is a name
        self.assertEqual(_read("the XXth century", "en"), [])
        self.assertEqual(_read("Leonardo da Vinci", "tr"), [])


if __name__ == "__main__":
    unittest.main()
