"""Time grows linearly with the length of the text. Each shape is read at n
and at 8n copies; a linear reader takes about 8 times as long, so the ratio
must stay below 12. A quadratic split search took 17 to 18 times as long on
250 and 2000 copies of one number word, and more than 80 times as long on a
run with joiners. Load on the machine only makes a ratio larger, so the
lowest of up to ATTEMPTS measures counts."""
import time
import unittest

from numtag import tag_numbers

THRESHOLD = 12
ATTEMPTS = 3


def best_time(text: str, lang: str) -> float:
    best = float("inf")
    for _ in range(3):
        started = time.perf_counter()
        tag_numbers(text, lang)
        best = min(best, time.perf_counter() - started)
    return best


class TestGrowth(unittest.TestCase):
    def assert_linear(self, unit: str, lang: str, n: int) -> None:
        ratios = []
        while len(ratios) < ATTEMPTS and min(ratios, default=THRESHOLD) >= THRESHOLD:
            ratios.append(best_time(unit * 8 * n, lang) / best_time(unit * n, lang))
        self.assertLess(min(ratios), THRESHOLD, f"{unit!r} x {n} in {lang}: {ratios} times as long at 8x")

    def test_a_run_of_one_number_word_is_a_list(self):
        # every word is a number of its own
        self.assertEqual(len(tag_numbers("um " * 50, "pt-PT")), 50)
        self.assertEqual(len(tag_numbers("one " * 50, "en")), 50)
        self.assertEqual(len(tag_numbers("dois três " * 25, "pt-BR")), 50)
        # a coarse guard: copying the run for each signed number grows past
        # the threshold only from about 2000 numbers
        self.assertEqual(len(tag_numbers("-5 " * 50, "pt-PT")), 50)
        for unit, lang in (("um ", "pt-PT"), ("one ", "en"), ("-5 ", "pt-PT")):
            with self.subTest(unit=unit, lang=lang):
                self.assert_linear(unit, lang, 250)

    def test_a_run_of_number_words_and_joiners(self):
        for unit, lang in (("mil e ", "pt-PT"), ("one and ", "en"), ("dois milhões e ", "pt-PT")):
            with self.subTest(unit=unit, lang=lang):
                self.assert_linear(unit, lang, 25)

    def test_a_run_of_one_scale_word(self):
        # a chain of scale words after a vague word must not recurse or rescan the run;
        # 200 words keep the base time well above the timer noise
        for unit, lang in (("million ", "en"), ("mil ", "pt-PT"), ("tisuća ", "hr")):
            with self.subTest(unit=unit, lang=lang):
                self.assert_linear(unit, lang, 200)
        self.assertEqual(len(tag_numbers("tisuća " * 1500, "hr")), 1500)
        self.assertEqual(len(tag_numbers("mil " * 1500, "pt-PT")), 1500)
        self.assertEqual(tag_numbers("million " * 1500, "en"), [])

    def test_ordinary_text(self):
        for unit, lang in (("dois dias e três horas ", "pt-PT"), ("two days and three hours ", "en")):
            with self.subTest(unit=unit, lang=lang):
                self.assert_linear(unit, lang, 50)


if __name__ == "__main__":
    unittest.main()
