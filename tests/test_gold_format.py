import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

GOLD_DIR = Path(__file__).parent / "gold"
_spec = importlib.util.spec_from_file_location("check_gold", GOLD_DIR / "check_gold.py")
check_gold = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_gold)

LANGUAGES = ("pt-PT", "pt-BR", "en")
MIN_ROWS = 400


def _row(text, *mentions, source="arithmetic"):
    return {"text": text, "mentions": list(mentions), "source": source}


def _m(start, end, value, kind="cardinal", **extra):
    return {"start": start, "end": end, "value": value, "kind": kind, **extra}


class TestGoldFiles(unittest.TestCase):
    def test_every_language_file_passes(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                n_in, errors = check_gold.check_file(GOLD_DIR / f"{lang}.jsonl")
                self.assertEqual(errors, [])
                self.assertGreaterEqual(n_in, MIN_ROWS)

    def test_no_text_is_repeated_in_a_file(self):
        for lang in LANGUAGES:
            with self.subTest(lang=lang):
                lines = (GOLD_DIR / f"{lang}.jsonl").read_text(encoding="utf-8").splitlines()
                texts = [json.loads(line)["text"] for line in lines]
                self.assertEqual(len(texts), len(set(texts)))


class TestCheckerRefusesBadRows(unittest.TestCase):
    """The checker must fail on each kind of broken row, or a green run proves nothing."""

    def assertRefused(self, row):
        with self.assertRaises(AssertionError):
            check_gold.check_row(row)

    def test_a_good_row_passes(self):
        check_gold.check_row(_row("comprou duas dúzias de ovos", _m(8, 19, "24")))
        check_gold.check_row(_row("Estão -5 graus.", _m(6, 8, "-5")))
        check_gold.check_row(_row("Comprei uma casa.", _m(8, 11, "1", low_confidence=True)))
        check_gold.check_row(_row("Comeu um terço.", _m(6, 14, "1/3", "fraction")))
        check_gold.check_row(_row("Nada aqui."))

    def test_span_with_trailing_punctuation(self):
        self.assertRefused(_row("Saímos às 7, depois.", _m(10, 12, "7")))

    def test_span_with_leading_space(self):
        self.assertRefused(_row("Saímos às 7, depois.", _m(9, 11, "7")))

    def test_span_with_currency_sign(self):
        self.assertRefused(_row("Custa €10.", _m(6, 9, "10")))

    def test_span_outside_the_text(self):
        self.assertRefused(_row("dez", _m(0, 4, "10")))

    def test_empty_span(self):
        self.assertRefused(_row("dez", _m(1, 1, "10")))

    def test_overlapping_mentions(self):
        self.assertRefused(_row("vinte e um", _m(0, 5, "20"), _m(3, 10, "21")))

    def test_mentions_out_of_order(self):
        self.assertRefused(_row("dois e três", _m(7, 11, "3"), _m(0, 4, "2")))

    def test_non_canonical_values(self):
        for value in ("2.50", "007", "-0", "1,5"):
            with self.subTest(value=value):
                self.assertRefused(_row("dois vírgula cinco", _m(0, 18, value, "decimal")))

    def test_fraction_not_in_lowest_terms(self):
        self.assertRefused(_row("dois quartos", _m(0, 12, "2/4", "fraction")))

    def test_fraction_with_finite_decimal(self):
        self.assertRefused(_row("um meio", _m(0, 7, "1/2", "fraction")))

    def test_kind_that_contradicts_the_value(self):
        self.assertRefused(_row("dois e meio", _m(0, 11, "2.5", "cardinal")))
        self.assertRefused(_row("um milhão e meio", _m(0, 16, "1500000", "fraction")))

    def test_unknown_kind(self):
        self.assertRefused(_row("dez", _m(0, 3, "10", "number")))

    def test_empty_source(self):
        self.assertRefused(_row("dez", _m(0, 3, "10"), source=" "))

    def test_low_confidence_false(self):
        self.assertRefused(_row("uma casa", _m(0, 3, "1", low_confidence=False)))

    def test_unknown_key(self):
        self.assertRefused(_row("dez", _m(0, 3, "10", gender="masculine")))

    def test_span_that_cuts_a_word(self):
        self.assertRefused(_row("comprou duas dúzias", _m(8, 18, "24")))

    def test_a_unit_may_touch_the_digits(self):
        check_gold.check_row(_row("Pesava 3,5kg.", _m(7, 10, "3.5", "decimal")), "pt-PT")

    def test_decimal_kind_without_a_decimal_mark(self):
        with self.assertRaises(AssertionError):
            check_gold.check_row(_row("três quartos", _m(0, 12, "0.75", "decimal")), "pt-PT")

    def test_fraction_kind_with_a_decimal_mark(self):
        with self.assertRaises(AssertionError):
            check_gold.check_row(_row("dois vírgula cinco", _m(0, 18, "2.5", "fraction")), "pt-PT")

    def test_a_repeated_text_is_reported_by_the_file_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pt-PT.jsonl"
            line = '{"text": "dez", "mentions": [{"start": 0, "end": 3, "value": "10", "kind": "cardinal"}], "source": "arithmetic"}\n'
            path.write_text(line * 2, encoding="utf-8")
            n_in, errors = check_gold.check_file(path)
        self.assertEqual((n_in, len(errors)), (2, 1))
        self.assertIn("repeats line 1", errors[0])

    def test_invalid_json_line_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "xx.jsonl"
            path.write_text('{"text": "dez", "mentions": [], "source": "arithmetic"}\n{not json\n', encoding="utf-8")
            n_in, errors = check_gold.check_file(path)
        self.assertEqual(n_in, 2)
        self.assertEqual(len(errors), 1)
        self.assertIn("xx.jsonl:2", errors[0])


if __name__ == "__main__":
    unittest.main()
