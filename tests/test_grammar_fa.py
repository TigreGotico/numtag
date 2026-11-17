"""Persian grammar rules. Each expected value is worked out by hand in the
comment beside it; sources are in numtag/lexicon/fa.json."""
import unittest

from helpers import read, sure
from numtag import Scale, tag_numbers

C, O, F, D = "cardinal", "ordinal", "fraction", "decimal"


def fa(text: str) -> list[tuple[str, str, str]]:
    return read(text, "fa")


class TestPersian(unittest.TestCase):
    def test_a_weekday_name_written_with_a_space_holds_no_number(self):
        # "سه شنبه" is Tuesday, "پنج شنبه" Thursday: no 3 or 5
        for name in ("یک شنبه", "دو شنبه", "سه شنبه", "چهار شنبه", "پنج شنبه"):
            with self.subTest(name=name):
                self.assertEqual(fa(name), [])
        self.assertEqual(fa("هر سه شنبه در ساعت 10 30"), [("10", "10", C), ("30", "30", C)])
        self.assertEqual(fa("سه شنبه ساعت پنج"), [("پنج", "5", C)])
        # a number before another noun keeps its value
        self.assertEqual(fa("سه کتاب"), [("سه", "3", C)])

    def test_every_part_takes_the_joiner(self):
        # 20 + 5 = 25; 1000 + 900 + 80 + 4 = 1984
        self.assertEqual(fa("بیست و پنج"), [("بیست و پنج", "25", C)])
        self.assertEqual(fa("هزار و نهصد و هشتاد و چهار"), [("هزار و نهصد و هشتاد و چهار", "1984", C)])

    def test_a_thousand_counts_a_milliard(self):
        # هزار میلیارد = 10^3 x 10^9 = 10^12
        self.assertEqual(fa("هزار میلیارد"), [("هزار میلیارد", "1000000000000", C)])

    def test_a_trillion_is_a_thousand_milliards(self):
        # تریلیون = هزار میلیارد = 10^3 x 10^9 = 10^12, written as 1 and 12 zeros
        self.assertEqual(fa("یک تریلیون"), [("یک تریلیون", "1000000000000", C)])
        # 2 x 10^12
        self.assertEqual(fa("دو تریلیون"), [("دو تریلیون", "2000000000000", C)])

    def test_a_trillion_is_a_million_million_in_the_long_scale(self):
        # the word is the third -illion: short scale 10^(3 x 3 + 3) = 10^12, long scale 10^(6 x 3) = 10^18
        for scale, value in ((None, "1000000000000"), (Scale.SHORT, "1000000000000"), (Scale.LONG, "1000000000000000000")):
            with self.subTest(scale=scale):
                found = tag_numbers("یک تریلیون", "fa", **({} if scale is None else {"scale": scale}))
                self.assertEqual([(m.value, m.number_scale) for m in found], [(value, scale or Scale.SHORT)])

    def test_persian_and_arabic_digits(self):
        # ۱۲٬۳۴۵٫۶۷ = 12345.67
        self.assertEqual(fa("۱۲٬۳۴۵٫۶۷ تومان"), [("۱۲٬۳۴۵٫۶۷", "12345.67", D)])
        self.assertEqual(fa("٣٤٥"), [("٣٤٥", "345", C)])
        self.assertEqual(fa("۳4"), [])

    def test_the_fraction_takes_the_ordinal(self):
        # دو سوم = 2/3; سه چهارم = 3/4
        self.assertEqual(fa("دو سوم"), [("دو سوم", "2/3", F)])
        self.assertEqual(fa("سه چهارم"), [("سه چهارم", "0.75", F)])

    def test_the_ordinal_suffix_goes_on_the_last_word(self):
        # 20 + 1 = 21; سی‌ام with the zero-width non-joiner is 30
        self.assertEqual(fa("قرن بیست و یکم"), [("بیست و یکم", "21", O)])
        self.assertEqual(fa("روز سی‌ام"), [("سی‌ام", "30", O)])
        # the same word typed without the non-joiner
        self.assertEqual(fa("روز سیام"), [("سیام", "30", O)])

    def test_arabic_letters_read_as_persian(self):
        # Arabic yeh in يک reads as Persian ی; یک before a noun is weak
        self.assertEqual(fa("يک کتاب"), [("يک", "1", C)])

    def test_nine_alone_is_also_no(self):
        # 9 alone at low confidence; 9 x 1000
        self.assertEqual(sure("نه", "fa"), [("نه", "9", 0.4)])
        self.assertEqual(sure("نه هزار", "fa"), [("نه هزار", "9000", 1.0)])
        self.assertEqual(sure("هشت", "fa"), [("هشت", "8", 1.0)])

    def test_hifdah_is_seventeen(self):
        # "هیفده" is "هفده": 17; 100 + 17 = 117
        self.assertEqual(read("صد و هیفده", "fa"), [("صد و هیفده", "117", "cardinal")])
        self.assertEqual(read("هیفده", "fa"), [("هیفده", "17", "cardinal")])


if __name__ == "__main__":
    unittest.main()
