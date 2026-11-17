"""A word of the vague_quantifier list right before a scale word takes the place
of its count, so the scale word reads no number. Each row is a sentence of a
pt.wikipedia or en.wikipedia article, named in the comment beside it, or a
short phrase where the comment says so; the values of the numbers that stay
are worked out by hand there."""
import unittest

from numtag import tag_numbers


def numbers(text: str, lang: str) -> list[tuple[str, str]]:
    return [(m.text, m.value) for m in tag_numbers(text, lang)]


class TestScaleWordAfterVagueWord(unittest.TestCase):
    def test_mil_after_a_vague_word_reads_no_number(self):
        # pt.wikipedia, "Religião na Áustria": 200 x 1000 = 200000; 2/3
        text = ("A significante população judaica (cerca de 200 000 em 1938), residindo principalmente em Viena, foi "
                "reduzida a somente alguns mil através da emigração em massa em 1938 (mais de dois terços da população "
                "judaica emigrou de 1938 a 1941), e o Holocausto que se seguiu durante regime nazista.")
        self.assertEqual(numbers(text, "pt-PT"), [("200 000", "200000"), ("1938", "1938"), ("1938", "1938"),
                                                  ("dois terços", "2/3"), ("1938", "1938"), ("1941", "1941")])
        # pt.wikipedia, "Fenghuang"
        text = ("sugerem que seja provavelmente baseado em parte - por exemplo o pescoço parecido de uma cobra - na "
                "memória folclórica do Avestruz Asiático que era comum na China pré-histórica mas se extinguiu há "
                "vários mil anos.")
        self.assertEqual(numbers(text, "pt-BR"), [("uma", "1")])
        # pt.wikipedia, "Ataque de força bruta"
        text = ("No caso das GPUs, algumas centenas, no caso das FPGAs, algumas mil unidades de processamento, "
                "tornando-as muito mais adequadas para quebrar senhas do que os processadores convencionais.")
        self.assertEqual(numbers(text, "pt-BR"), [])
        # pt.wikipedia, "Setife": a count before "mil" still reads. 45 x 1000 = 45000; "segundo" is a homograph of 2nd
        text = ("Essas manifestações custaram a vida de milhares de pessoas (entre 40 e 45 mil, segundo diversas "
                "fontes).")
        self.assertEqual(numbers(text, "pt-PT"), [("40", "40"), ("45 mil", "45000"), ("segundo", "2")])

    def test_the_guard_holds_through_a_chain_of_scale_words(self):
        # pt.wikipedia, "Ásia Central": "muitos mil milhões" is many thousand millions, no number
        text = ("Em 2022, especialistas avaliaram que as alterações climáticas globais deverão colocar múltiplos "
                "riscos económicos à Ásia Central e podem possivelmente resultar em muitos mil milhões de perdas, a "
                "menos que sejam desenvolvidas medidas de adaptação adequadas para contrariar o aumento das "
                "temperaturas em toda a região.")
        self.assertEqual(numbers(text, "pt-PT"), [("2022", "2022")])
        # en.wikipedia, "83D/Russell": English reads no "million" with no count, with or without the list
        text = ("The comet might come to perihelion in late November 2028, but the uncertainty in the comet's "
                "position is a few million km.")
        self.assertEqual(numbers(text, "en"), [("2028", "2028")])

    def test_a_joined_group_after_mil_keeps_the_whole_number(self):
        # short phrases: "e" joins a last group to "mil", so the scale word counts one and the number goes on
        # 1000 + 500 = 1500
        self.assertEqual(numbers("algumas mil e quinhentas pessoas", "pt-PT"), [("mil e quinhentas", "1500")])
        # 1000 + 200 = 1200
        self.assertEqual(numbers("alguns mil e duzentos euros", "pt-BR"), [("mil e duzentos", "1200")])
        self.assertEqual(numbers("muitos mil e duzentos", "pt-PT"), [("mil e duzentos", "1200")])
        # "umas" is no vague_quantifier entry: 1000 + 500 = 1500, as before the list
        self.assertEqual(numbers("umas mil e quinhentas pessoas", "pt-PT"), [("mil e quinhentas", "1500")])
        # English reads no "thousand" with no count; "five" alone is 5
        self.assertEqual(numbers("a few thousand and five", "en"), [("five", "5")])

    def test_a_joined_group_after_a_chain_of_scale_words_keeps_the_number(self):
        # short phrases: 1000 x 1000000 + 200 x 1000 = 1000200000
        self.assertEqual(numbers("muitos mil milhões e duzentos mil euros", "pt-PT"),
                         [("mil milhões e duzentos mil", "1000200000")])
        # 1000 x 1000000 + 500 x 1000000 = 1500000000
        self.assertEqual(numbers("alguns mil milhões e quinhentos milhões", "pt-PT"),
                         [("mil milhões e quinhentos milhões", "1500000000")])
        # pt-BR "bilhão" is 10^9: 1000 x 10^9 + 3 = 1000000000003
        self.assertEqual(numbers("alguns mil bilhões e três", "pt-BR"), [("mil bilhões e três", "1000000000003")])

    def test_a_joined_half_after_a_chain_of_scale_words_keeps_the_number(self):
        # short phrases: 1000 x 1000000 x 1.5 = 1500000000
        self.assertEqual(numbers("A obra custou alguns mil milhões e meio de euros.", "pt-PT"),
                         [("mil milhões e meio", "1500000000")])
        self.assertEqual(numbers("muitos mil milhões e meio", "pt-PT"), [("mil milhões e meio", "1500000000")])
        # pt-BR "bilhão" is 10^9: 1000 x 10^9 x 1.5 = 1500000000000
        self.assertEqual(numbers("alguns mil bilhões e meio", "pt-BR"), [("mil bilhões e meio", "1500000000000")])

    def test_no_number_after_the_joiner_keeps_the_guard(self):
        # short phrases: "e" with no number after it joins no group
        self.assertEqual(numbers("alguns mil e pessoas", "pt-PT"), [])
        self.assertEqual(numbers("alguns mil e", "pt-PT"), [])


class TestHundredWordAfterVagueWord(unittest.TestCase):
    """A Portuguese hundred word takes no count ("dois cem" is no number). When
    it goes on as a number, in a bound form or before a scale word, it reads as
    without the list. Short phrases; values by hand."""

    def test_cento_and_cem_after_a_vague_word(self):
        # 100 + 50 = 150; 150 x 1000 = 150000
        self.assertEqual(numbers("alguns cento e cinquenta mil euros", "pt-PT"),
                         [("cento e cinquenta mil", "150000")])
        # 100 + 20 = 120
        self.assertEqual(numbers("alguns cento e vinte reais", "pt-BR"), [("cento e vinte", "120")])
        # 100 x 1000 = 100000
        self.assertEqual(numbers("algumas cem mil pessoas", "pt-PT"), [("cem mil", "100000")])

    def test_a_hundred_word_after_a_count_and_a_plural_scale_word(self):
        # 3 x 1000000 + (100 + 20) x 1000 = 3120000
        self.assertEqual(numbers("3 milhões cento e vinte mil euros", "pt-PT"),
                         [("3 milhões cento e vinte mil", "3120000")])
        # 2 x 1000000 + (100 + 50) x 1000 = 2150000
        self.assertEqual(numbers("2 milhões cento e cinquenta mil reais", "pt-BR"),
                         [("2 milhões cento e cinquenta mil", "2150000")])
        # 1.5 x 1000000 = 1500000, then 100 x 1000 = 100000
        self.assertEqual(numbers("1,5 milhões cem mil", "pt-BR"), [("1,5 milhões", "1500000"), ("cem mil", "100000")])


class TestCountBeforeAPluralScaleWord(unittest.TestCase):
    def test_a_count_makes_the_plural_scale_word_a_number(self):
        # short phrase: "3 milhões" is 3 x 1000000 = 3000000, no vague word, so "mil" reads 1000
        self.assertEqual(numbers("3 milhões mil euros", "pt-PT"), [("3 milhões", "3000000"), ("mil", "1000")])


if __name__ == "__main__":
    unittest.main()
