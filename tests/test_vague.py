"""tag_vague_quantities: words that state an amount but no exact number.

Each row is a sentence of an en.wikipedia or pt.wikipedia article, named in
the comment beside it. Each scale and lower bound is worked out by hand in
that comment. The sources of the words are in numtag/lexicon/en.json and
numtag/lexicon/pt-PT.json."""
import unittest

import pytest

from numtag import (Reason, UnsupportedLanguageError, VagueKind, VagueQuantity, tag_numbers,
                    tag_vague_quantities)
from numtag.lexicon import SCALE_ROLES, load
from numtag.tagger import AMBIGUOUS_CONFIDENCE

M, A = VagueKind.MAGNITUDE, VagueKind.AMOUNT


def at(text: str, words: str, kind: VagueKind, scale: str | None = None, bound: str | None = None,
       start: int = 0) -> VagueQuantity:
    """The vague quantity ``words`` at its first place in ``text`` from ``start``."""
    begin = text.index(words, start)
    return VagueQuantity((begin, begin + len(words)), words, kind, scale, bound)


def vague(text: str, lang: str) -> list[VagueQuantity]:
    """The vague quantities of ``text``; no number of ``tag_numbers`` overlaps one, so
    numbers_to_digits and extract_number never turn a vague word into digits."""
    found = tag_vague_quantities(text, lang)
    for m in tag_numbers(text, lang):
        for q in found:
            assert not (m.char_span[0] < q.char_span[1] and q.char_span[0] < m.char_span[1]), (m, q)
    return found


def numbers(text: str, lang: str) -> list[tuple[str, str]]:
    return [(m.text, m.value) for m in tag_numbers(text, lang)]


class TestMagnitudes(unittest.TestCase):
    def test_a_plural_scale_word_with_no_count(self):
        # en.wikipedia, "Ancón District": 10^6 = 1000000; 2 x 1000000 = 2000000
        text = "It is a popular beach resort destination of Lima, visited every summer by millions of people from Lima."
        self.assertEqual(vague(text, "en"), [at(text, "millions", M, "1000000", "2000000")])

    def test_two_magnitudes_in_reading_order(self):
        # en.wikipedia, "NetTraveler": 100, 2 x 100 = 200; 12, 2 x 12 = 24
        text = ("NetTraveler or TravNet is spyware that dates from 2004 and that has been actively used at least "
                "until 2016, infecting hundreds of often high-profile servers in dozens of countries.")
        self.assertEqual(vague(text, "en"),
                         [at(text, "hundreds", M, "100", "200"), at(text, "dozens", M, "12", "24")])
        self.assertEqual(numbers(text, "en"), [("2004", "2004"), ("2016", "2016")])

    def test_portuguese_magnitudes_between_numbers(self):
        # pt.wikipedia, "Galápagos": 10, 2 x 10 = 20, twice; 4 x 1000 + 588 = 4588; 8 x 1000 + 10 = 8010
        text = ("O arquipélago que compreende o conjunto das ilhas Galápagos, que são de origem vulcânica, é formado "
                "por dezenas de ilhas e rochedos, sendo treze ilhas maiores (entre 14 a 4 588 km²), seis ilhas "
                "menores, e dezenas de ilhotas e rochedos, que totalizam uma área terrestre de 8 010 km².")
        first = text.index("dezenas")
        self.assertEqual(vague(text, "pt-PT"),
                         [at(text, "dezenas", M, "10", "20"), at(text, "dezenas", M, "10", "20", first + 1)])
        self.assertEqual(numbers(text, "pt-PT"), [("treze", "13"), ("14", "14"), ("4 588", "4588"), ("seis", "6"),
                                                  ("uma", "1"), ("8 010", "8010")])

    def test_brazilian_portuguese_reads_the_same_words(self):
        # pt.wikipedia, "Artesão": 10, 2 x 10 = 20
        text = ("Artesão semi-industrial: é aquele que trabalhando a partir de moldes e/ ou de outros processos "
                "semi-industriais, reproduz dezenas de peças iguais.")
        self.assertEqual(vague(text, "pt-BR"), [at(text, "dezenas", M, "10", "20")])

    def test_each_plural_scale_word_of_a_phrase_is_its_own_magnitude(self):
        # pt.wikipedia, "Navio-tanque": 100, 2 x 100 = 200; 1000, 2 x 1000 = 2000. "centenas de
        # milhares" gives two magnitudes: the lexicon holds no product for a phrase with "de".
        text = "Navios-tanque podem carregar desde várias centenas de toneladas até centenas de milhares de toneladas."
        first = text.index("centenas")
        self.assertEqual(vague(text, "pt-PT"),
                         [at(text, "várias centenas", M, "100", "200"),
                          at(text, "centenas", M, "100", "200", first + 1), at(text, "milhares", M, "1000", "2000")])


class TestVagueWordBeforeScaleWord(unittest.TestCase):
    def test_a_singular_scale_word_gives_a_scale_and_no_bound(self):
        # en.wikipedia, "Pacarana": 10^6 = 1000000
        text = ("Initially, the pacarana was regarded as a member of the superfamily Muroidea, that includes the "
                "true mice, but that view was abandoned in the face of evidence that suggests that the pacarana is "
                "in the family Dinomyidae together with extinct animals such as Phoberomys pattersoni and "
                "Josephoartigasia monesi, prehistoric giant rodents that lived in South America several million "
                "years ago.")
        self.assertEqual(vague(text, "en"), [at(text, "several million", M, "1000000")])
        # en.wikipedia, "Eranadan language": 10^2 = 100
        text = ("Eranadan  (IPA: [eːrɐnaːɖɐn], ISO: ēṟanāṭan) is a Dravidian language spoken by several hundred "
                "people, predominantly in the region of Eranad, Malappuram district, Kerala, India.")
        self.assertEqual(vague(text, "en"), [at(text, "several hundred", M, "100")])
        # en.wikipedia, "Shiqihe station": a dozen is 12
        text = "Only a few dozen people use the station daily."
        self.assertEqual(vague(text, "en"), [at(text, "a few dozen", M, "12")])

    def test_a_plural_scale_word_keeps_its_bound(self):
        # en.wikipedia, "BugGuide": 10^3 = 1000; 2 x 1000 = 2000
        text = ("The website consists of informational guide pages and many thousands of photographs of "
                "arthropods from the United States and Canada which are used for identification and research.")
        self.assertEqual(vague(text, "en"), [at(text, "many thousands", M, "1000", "2000")])

    def test_portuguese_vague_words_before_plural_scale_words(self):
        # pt.wikipedia, "Zona de fratura": 100, 2 x 100 = 200; 1000, 2 x 1000 = 2000
        text = ("Zona de fractura é a designação dada nos campos da tectónica de placas e da oceanografia física a "
                "estruturas tectónicas lineares existentes nos fundos oceânicos que em geral se estendem por muitas "
                "centenas de quilómetros, por vezes mesmo por alguns milhares de quilómetros, em direcção "
                "perpedicular ao eixo do rifte oceânico a que estão associadas.")
        self.assertEqual(vague(text, "pt-PT"),
                         [at(text, "muitas centenas", M, "100", "200"), at(text, "alguns milhares", M, "1000", "2000")])
        # pt.wikipedia, "Língua candoshi"
        text = ("Candoshi-Shapra (ou  Candoshi, Candoxi, Kandoshi, Murato) é uma língua ameríndia falada por alguns "
                "milhares de pessoas no Peru, ao longo dos rios Morona, Pastaza, Huitoyacu, Chapulan .")
        self.assertEqual(vague(text, "pt-BR"), [at(text, "alguns milhares", M, "1000", "2000")])


class TestAmounts(unittest.TestCase):
    def test_a_vague_word_alone_has_no_scale_and_no_bound(self):
        # en.wikipedia, "Benthic lander"
        text = ("Benthic landers have deployment durations from a few days (for biological studies) "
                "to several years (for physical oceanography studies).")
        self.assertEqual(vague(text, "en"), [at(text, "a few", A), at(text, "several", A)])

    def test_an_amount_beside_numbers(self):
        # en.wikipedia, "Ilir Kadia"
        text = "All the books are composed of 20 short stories on umpteen topics of Albanian life."
        self.assertEqual(vague(text, "en"), [at(text, "umpteen", A)])
        self.assertEqual(numbers(text, "en"), [("20", "20")])
        # en.wikipedia, "Ancón District"
        text = "Besides the beach, in 1913, there was a tennis court, one or two hotels, and many cottages."
        self.assertEqual(vague(text, "en"), [at(text, "many", A)])
        self.assertEqual(numbers(text, "en"), [("1913", "1913"), ("one", "1"), ("two", "2")])

    def test_the_same_word_twice(self):
        # en.wikipedia, "Machar Colony"
        text = ("Many people are undocumented because they have not been given citizenship by the government of "
                "Pakistan; therefore, many people are jobless.")
        self.assertEqual(vague(text, "en"), [at(text, "Many", A), at(text, "many", A)])

    def test_portuguese_amounts(self):
        # pt.wikipedia, "Álbum de estúdio"
        text = "O tempo necessário para gravar um álbum varia de algumas horas a vários anos."
        self.assertEqual(vague(text, "pt-BR"), [at(text, "algumas", A), at(text, "vários", A)])
        # pt.wikipedia, "Arado Flugzeugwerke"
        text = "Um de seus projetos, o Ar 96, continuou a ser fabricado por muitos anos após a guerra."
        self.assertEqual(vague(text, "pt-PT"), [at(text, "muitos", A)])
        self.assertEqual(numbers(text, "pt-PT"), [("Um", "1"), ("96", "96")])

    def test_a_chain_of_scale_words_multiplies(self):
        # pt.wikipedia, "Ásia Central": 1000 x 10^6 = 10^9 = 1000000000; "milhões" is plural
        # because "mil" counts it, so no bound
        text = ("Em 2022, especialistas avaliaram que as alterações climáticas globais deverão colocar múltiplos "
                "riscos económicos à Ásia Central e podem possivelmente resultar em muitos mil milhões de perdas, a "
                "menos que sejam desenvolvidas medidas de adaptação adequadas para contrariar o aumento das "
                "temperaturas em toda a região.")
        self.assertEqual(vague(text, "pt-PT"), [at(text, "muitos mil milhões", M, "1000000000")])
        # pt.wikipedia, "Ataque de força bruta": 100, 2 x 100 = 200; 1000
        text = ("No caso das GPUs, algumas centenas, no caso das FPGAs, algumas mil unidades de processamento, "
                "tornando-as muito mais adequadas para quebrar senhas do que os processadores convencionais.")
        self.assertEqual(vague(text, "pt-BR"), [at(text, "algumas centenas", M, "100", "200"),
                                                at(text, "algumas mil", M, "1000")])
        # en.wikipedia, "83D/Russell": 10^6 = 1000000
        text = ("The comet might come to perihelion in late November 2028, but the uncertainty in the comet's "
                "position is a few million km.")
        self.assertEqual(vague(text, "en"), [at(text, "a few million", M, "1000000")])

    def test_one_list_serves_both_jobs(self):
        # Hrvatski jezični portal, "više", sense 6: "više milijuna ljudi". The hr entry
        # stops "milijuna" from reading 1000000 and gives the vague quantity: 10^6
        text = "više milijuna ljudi"
        self.assertEqual(numbers(text, "hr"), [])
        self.assertEqual(vague(text, "hr"), [at(text, "više milijuna", M, "1000000")])
        # the hr entry is ambiguous; the scale word after it makes the quantity reading clear
        self.assertEqual(vague(text, "hr")[0].confidence, 1.0)


class TestHomographs(unittest.TestCase):
    def test_a_word_with_another_common_sense_has_a_low_confidence(self):
        # en.wikipedia, "Diagnosis": "a lot" is also an adverb and a piece of land
        text = ("Diagnosis is used in a lot of different disciplines, with variations in the use of logic, "
                "analytics, and experience, to determine \"cause and effect\".")
        [quantity] = vague(text, "en")
        self.assertEqual(quantity, at(text, "a lot", A))
        self.assertEqual((quantity.confidence, quantity.reasons), (AMBIGUOUS_CONFIDENCE, frozenset({Reason.HOMOGRAPH})))

    def test_bastante_is_also_an_adverb(self):
        # pt.wikipedia, "Ciclismo de estrada": here "bastante" is the adverb, so the low confidence is right
        text = "O ciclismo de estrada é um esporte bastante popular no mundo inteiro, mas principalmente na Europa."
        [quantity] = vague(text, "pt-BR")
        self.assertEqual(quantity, at(text, "bastante", A))
        self.assertEqual((quantity.confidence, quantity.reasons), (AMBIGUOUS_CONFIDENCE, frozenset({Reason.HOMOGRAPH})))

    def test_a_word_with_no_other_sense_is_sure(self):
        text = "Only a few dozen people use the station daily."
        [quantity] = vague(text, "en")
        self.assertEqual((quantity.confidence, quantity.reasons), (1.0, frozenset()))


class TestNoVagueQuantity(unittest.TestCase):
    def test_a_count_before_the_scale_word_makes_a_number(self):
        # en.wikipedia, "Indore Police": 3 x 10^6 = 3000000
        text = "MP Police (District Indore) serves a region of three million people."
        self.assertEqual(vague(text, "en"), [])
        self.assertEqual(numbers(text, "en"), [("three million", "3000000")])

    def test_a_portuguese_count_before_the_plural(self):
        # pt.wikipedia, "Rio Ohio": 3 x 10^6 = 3000000
        text = "É a fonte de água potável para três milhões de pessoas."
        self.assertEqual(vague(text, "pt-PT"), [])
        self.assertEqual(numbers(text, "pt-PT"), [("três milhões", "3000000")])
        # pt.wikipedia, "Biblioteca Britânica": 150 x 10^6 = 150000000; 3 x 10^6 = 3000000
        text = ("Atualmente, o seu acervo possui aproximadamente 150 milhões de itens e a cada ano incorporam-se à "
                "coleção cerca de três milhões de itens novos.")
        self.assertEqual(vague(text, "pt-PT"), [])
        self.assertEqual(numbers(text, "pt-PT"), [("150 milhões", "150000000"), ("três milhões", "3000000")])

    def test_empty_and_plain_text(self):
        self.assertEqual(vague("", "en"), [])
        self.assertEqual(vague("The station opened in 2005.", "en"), [])

    def test_a_language_with_no_entries_gives_nothing(self):
        self.assertEqual(vague("Des millions de personnes", "fr"), [])

    def test_an_unknown_language_raises(self):
        with self.assertRaises(UnsupportedLanguageError):
            tag_vague_quantities("many people", "xx")


class TestCoupleAndPaar(unittest.TestCase):
    """en "a couple (of)" is two at the homograph score; nl "een paar" and de "ein paar" are
    an amount, and their article is no count of one. Quotes in docs/rulings.md."""

    def test_a_couple_is_two_at_the_homograph_score(self):
        # Merriam-Webster, "couple", adjective: "two also : few"; Cambridge: "two or a few things"
        for text in ("take a picture in a couple of seconds", "roll a couple of dice",
                     "The doctor said my leg should be better in a couple of days.", "a couple drinks"):
            with self.subTest(text=text):
                [m] = tag_numbers(text, "en")
                self.assertEqual((m.text, m.value, m.confidence, m.reasons),
                                 ("a couple", "2", AMBIGUOUS_CONFIDENCE, frozenset({Reason.HOMOGRAPH})))
                self.assertEqual(vague(text, "en"), [])

    def test_a_couple_before_a_scale_word_is_a_magnitude(self):
        # Merriam-Webster, usage guide: "a couple hundred a couple dozen"; the phrase stands where
        # the count would, as "a few" does: 10^2 = 100, 12, 10^3 = 1000, 10^6 = 1000000
        for text, words, scale in (("It cost a couple hundred dollars.", "a couple hundred", "100"),
                                   ("a couple dozen eggs", "a couple dozen", "12"),
                                   ("a couple of thousand people", "a couple of thousand", "1000"),
                                   ("a couple of million years", "a couple of million", "1000000")):
            with self.subTest(text=text):
                self.assertEqual(numbers(text, "en"), [])
                self.assertEqual(vague(text, "en"), [at(text, words, M, scale)])

    def test_the_couple_with_no_count_is_no_number(self):
        # only the article makes "couple" a number; "the couple" names two persons and no count
        self.assertEqual(numbers("The couple walked in.", "en"), [])

    def test_a_count_before_couple_counts_couples(self):
        # Merriam-Webster, "couple", noun sense 1a: "two persons married, engaged, or otherwise
        # romantically paired"; the count counts couples, so the number is the count alone
        for text, count in (("One couple said they had waited for hours.", ("One", "1")),
                            ("three couple dances", ("three", "3")),
                            ("Two couple friends of ours came along.", ("Two", "2"))):
            with self.subTest(text=text):
                self.assertEqual(numbers(text, "en"), [count])

    def test_een_paar_is_an_amount_and_een_is_no_one(self):
        # Onze Taal 72: "een paar" with the sense "een klein aantal" is an indefinite numeral, like "enkele"
        for text in ("foto in een paar seconden", "Neem jij een paar appels mee?", "Een paar mensen zonder auto."):
            with self.subTest(text=text):
                self.assertEqual(numbers(text, "nl"), [])
                [quantity] = vague(text, "nl")
                self.assertEqual(quantity, at(text, text[text.casefold().index("een paar"):][:8], A))
                self.assertEqual((quantity.confidence, quantity.reasons),
                                 (AMBIGUOUS_CONFIDENCE, frozenset({Reason.HOMOGRAPH})))

    def test_ein_paar_is_an_amount_and_ein_is_no_one(self):
        # DWDS (eWDG), "ein paar": "bezeichnet eine unbestimmte Anzahl"
        for text in ("in ein paar Sekunden", "ein paar Schritte gehen"):
            with self.subTest(text=text):
                self.assertEqual(numbers(text, "de"), [])
                [quantity] = vague(text, "de")
                self.assertEqual(quantity.kind, A)
                self.assertEqual(quantity.text.casefold(), "ein paar")
                self.assertEqual(quantity.confidence, AMBIGUOUS_CONFIDENCE)

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/249")
    def test_ein_paar_with_a_capital_is_one_pair(self):
        # DWDS lists the noun "Paar" and the pronoun "paar" as two words; the article counts one pair
        self.assertEqual(numbers("Ein Paar Schuhe.", "de"), [("Ein", "1")])

    def test_een_paar_before_a_scale_word_is_a_magnitude(self):
        # 10^2 = 100 and 10^3 = 1000; a vague word before a singular scale word gives no lower bound
        text = "een paar honderd mensen"
        self.assertEqual(numbers(text, "nl"), [])
        self.assertEqual(vague(text, "nl"), [at(text, "een paar honderd", M, "100")])
        text = "ein paar tausend Menschen"
        self.assertEqual(numbers(text, "de"), [])
        self.assertEqual(vague(text, "de"), [at(text, "ein paar tausend", M, "1000")])

    def test_a_count_of_pairs_keeps_its_number(self):
        # "twee paar schoenen" is two pairs; "één" with accents is only the numeral, one pair
        self.assertEqual(numbers("twee paar schoenen", "nl"), [("twee", "2")])
        self.assertEqual(numbers("één paar schoenen", "nl"), [("één", "1")])
        self.assertEqual(numbers("zwei Paar Schuhe", "de"), [("zwei", "2")])


class TestLexicon(unittest.TestCase):
    def test_every_magnitude_word_is_a_plural_scale_word(self):
        # a one-word entry that is a plural scale word gives a magnitude; check the
        # en and pt entries that name a scale have that reading
        magnitudes = {"en": ["millions", "thousands", "hundreds", "dozens"],
                      "pt-PT": ["milhões", "milhares", "centenas", "dezenas", "dúzias"],
                      "pt-BR": ["milhões", "milhares", "centenas", "dezenas", "dúzias"]}
        for lang, words in magnitudes.items():
            lexicon = load(lang)
            for word in words:
                with self.subTest(lang=lang, word=word):
                    self.assertIn((word,), lexicon.vague_quantifiers)
                    self.assertTrue(any(e.plural and (e.role in SCALE_ROLES or e.role == "collective")
                                        for e in lexicon.readings[word]))


if __name__ == "__main__":
    unittest.main()
