import unittest

from numtag import tag_numbers


def values(text, lang):
    return [(m.text, m.value) for m in tag_numbers(text, lang)]


# Spanish reads an hour and minutes with a point as a decimal (RAE DPD "números" 1.1d)
ES_DECIMAL = (
    ("cuesta 3.50 pesos", "3.50", "3.5"), ("pesa 1.25 kilos", "1.25", "1.25"),
    ("dura 1.25 horas", "1.25", "1.25"), ("pon el brillo a 0.25", "0.25", "0.25"),
)
# an hour of "0" reads as a decimal in every locale
BARE_ZERO = (
    ("es", "pon el brillo a 0.25"), ("pt-PT", "põe o brilho a 0.25"), ("de", "stell die Helligkeit auf 0.25"),
    ("de", "Faktor 0.25"), ("fr-FR", "mets la luminosité à 0.25"), ("it", "metti la luminosità a 0.25"),
    ("nl", "zet de helderheid op 0.25"), ("ca", "posa la brillantor a 0.25"), ("gl", "pon o brillo a 0.25"),
    ("sv", "faktor 0.25"),
)
# a clock word beside the shape makes it a time
CLOCK = (
    ("es", "quedamos a las 11.30"), ("es", "llego a la 1.30"), ("es", "a las 17.30 horas"),
    ("es", "llega a las 11.30 h"), ("es", "llega 11.30h"), ("es", "a las 0.30"),
    ("de", "um 0.30 Uhr"), ("de", "es ist 0.12 Uhr"), ("de", "gegen 0.30"), ("de", "14.30Uhr"),
    ("pt-PT", "às 0.30"), ("pt-PT", "saio 0.30 h"), ("pt-BR", "saio às 0.30"),
    ("fr-FR", "départ 0.30 h"), ("it", "alle 0.30"), ("nl", "om 0.30"), ("nl", "het is 0.30 uur"),
    ("ca", "a les 0.30"), ("ca", "a la 1.30"), ("gl", "ás 0.30"), ("gl", "saio 0.30h"),
    ("nb", "møtet er kl. 0.30"), ("nn", "møtet er kl. 0.30"), ("da", "mødet er kl. 0.30"), ("fi", "klo 0.30"),
)
# every other H.MM shape reads no number, as before
TIME = (
    ("de", "Treffen 11.30"), ("de", "von 9.00 bis 17.00 Uhr"), ("de", "kostet 3.50 Euro"), ("de", "um 11.30 Uhr"),
    ("pt-PT", "custa 3.50 euros"), ("pt-PT", "das 9.00 às 17.00"),
    ("fr-FR", "à 14.30"), ("it", "costa 3.50 euro"), ("nl", "van 9.00 tot 17.00 uur"), ("ca", "costa 3.50 euros"),
    ("gl", "custa 3.50 euros"), ("sv", "kl. 14.30"), ("ru", "в 14.30"), ("pl", "o 14.30"),
    ("nb", "kl. 14.30"), ("da", "kl. 23.59"), ("fi", "klo 20.10"), ("de", "24.00"), ("es", "24.00"),
)


class TestClockShapedPoint(unittest.TestCase):
    def test_spanish_reads_an_hour_and_minutes_with_a_point_as_a_decimal(self):
        for text, span, value in ES_DECIMAL:
            with self.subTest(text=text):
                self.assertEqual(values(text, "es"), [(span, value)])

    def test_an_hour_of_zero_reads_as_a_decimal_in_every_locale(self):
        for lang, text in BARE_ZERO:
            with self.subTest(lang=lang, text=text):
                self.assertEqual(values(text, lang), [("0.25", "0.25")])

    def test_a_clock_word_beside_the_shape_makes_it_a_time(self):
        for lang, text in CLOCK:
            with self.subTest(lang=lang, text=text):
                self.assertEqual(values(text, lang), [])

    def test_other_shapes_read_no_number(self):
        for lang, text in TIME:
            with self.subTest(lang=lang, text=text):
                self.assertEqual(values(text, lang), [])

    def test_the_period_after_a_word_that_is_no_abbreviation_ends_a_sentence(self):
        self.assertEqual(values("Wir bogen um. 0.25 Liter fehlten.", "de"), [("0.25", "0.25")])
        self.assertEqual(values("Abbiamo aspettato due ore. 0.25 euro il biglietto.", "it"),
                         [("due", "2"), ("0.25", "0.25")])
