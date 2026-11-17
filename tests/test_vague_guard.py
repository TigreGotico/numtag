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


if __name__ == "__main__":
    unittest.main()
