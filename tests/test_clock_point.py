import unittest

from numtag import tag_numbers

# (language, a price or measure, its number, a text with a clock word and 11.30)
PRICED = (
    ("es", "cuesta 3.50 pesos", "3.50", "3.5"),
    ("es", "pon el brillo a 0.25", "0.25", "0.25"),
    ("pt-PT", "custa 3.50 euros", "3.50", "3.5"),
    ("pt-PT", "põe o brilho a 0.25", "0.25", "0.25"),
    ("de", "das kostet 3.50 Euro", "3.50", "3.5"),
    ("de", "stell die Helligkeit auf 0.25", "0.25", "0.25"),
    ("fr-FR", "cela coûte 3.50 euros", "3.50", "3.5"),
    ("fr-FR", "mets la luminosité à 0.25", "0.25", "0.25"),
    ("it", "costa 3.50 euro", "3.50", "3.5"),
    ("it", "metti la luminosità a 0.25", "0.25", "0.25"),
    ("nl", "het kost 3.50 euro", "3.50", "3.5"),
    ("nl", "zet de helderheid op 0.25", "0.25", "0.25"),
    ("ca", "costa 3.50 euros", "3.50", "3.5"),
    ("ca", "posa la brillantor a 0.25", "0.25", "0.25"),
    ("gl", "custa 3.50 euros", "3.50", "3.5"),
    ("gl", "pon o brillo a 0.25", "0.25", "0.25"),
)
CLOCK = (
    ("es", "quedamos a las 11.30"), ("es", "a las 17.30 horas"), ("es", "llega a las 11.30 h"),
    ("pt-PT", "chegamos às 11.30"), ("pt-BR", "saio às 11.30 h"),
    ("de", "wir kommen um 11.30"), ("de", "gegen 11.30 Uhr"), ("de", "es ist 11.30 Uhr"),
    ("fr-FR", "départ 11.30 h"),
    ("it", "arriviamo alle 11.30"), ("it", "parte 11.30 h"),
    ("nl", "we komen om 11.30"), ("nl", "het is 11.30 uur"),
    ("ca", "arribem a les 11.30"), ("ca", "són les 11.30 h"),
    ("gl", "chegamos ás 11.30"), ("gl", "saio 11.30 h"),
    ("nb", "møtet er kl. 11.30"), ("nn", "møtet er kl. 11.30"), ("da", "mødet er kl. 11.30"),
)

# a plural count noun after the digits counts a length as well, so it marks no clock
DURATION = (
    ("es", "dura 1.25 horas", "1.25"), ("pt-PT", "dura 1.25 horas", "1.25"), ("gl", "dura 1.25 horas", "1.25"),
    ("fr-FR", "dure 1.5 heures", "1.5"), ("it", "dura 1.5 ore", "1.5"),
    ("fr-FR", "dure 1.25 heures", "1.25"), ("it", "dura 1.25 ore", "1.25"), ("ca", "dura 1.25 hores", "1.25"),
)


class TestClockShapedPoint(unittest.TestCase):
    def test_a_point_decimal_in_the_shape_of_a_time_reads_a_decimal_without_a_clock_word(self):
        for lang, text, span, value in PRICED:
            with self.subTest(lang=lang, text=text):
                self.assertEqual([(m.text, m.value) for m in tag_numbers(text, lang)], [(span, value)])

    def test_a_clock_word_before_or_after_the_shape_makes_it_a_time(self):
        for lang, text in CLOCK:
            with self.subTest(lang=lang, text=text):
                self.assertEqual(tag_numbers(text, lang), [])

    def test_24_00_is_a_time_without_a_clock_word(self):
        for lang in ("es", "de", "fr-FR", "nl"):
            with self.subTest(lang=lang):
                self.assertEqual(tag_numbers("24.00", lang), [])

    def test_a_plural_hour_noun_after_the_shape_is_a_duration(self):
        for lang, text, value in DURATION:
            with self.subTest(lang=lang, text=text):
                self.assertEqual([m.value for m in tag_numbers(text, lang)], [value])
