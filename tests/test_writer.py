"""The writer: the golden file, the round trip, the interpreter and the API."""
import json
import random
import re
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path
from unittest import mock

import pytest

import numtag
from numtag import Kind, SpokenForm, SpellingReason, UnsupportedLanguageError, spell, tag_numbers
from numtag.lexicon import load
from numtag import lexicon as lexicon_module
from numtag import tagger as tagger_module
from numtag import writer as writer_module
import golden_writers

PACKAGE = Path(numtag.__file__).parent
LEXICONS = PACKAGE / "lexicon"
VERSION_TWO = sorted(path.stem for path in LEXICONS.glob("*.json") if "writer" in json.loads(path.read_text("utf-8")))
WRITERS = sorted(name for name in VERSION_TWO if json.loads((LEXICONS / f"{name}.json").read_text("utf-8"))["writer"])


# https://github.com/TigreGotico/numtag/issues/305: the pt-PT reader splits an ordinal with two scale
# groups and lacks the ordinal scale words above "bilionésimo".
ISSUE_305 = re.compile(r"(?:ilionésim[ao].*){2}|(?:mil|ilion)ésim[ao] .*(?:mil|ilion)ésim[ao]|(?<!b)(?<!m)ilionésim[ao]")


def _issue_305(lang: str, text: str) -> bool:
    return lang == "pt-PT" and bool(ISSUE_305.search(text))


def _file(name: str) -> dict:
    return json.loads((LEXICONS / f"{name}.json").read_text(encoding="utf-8"))


class Variants:
    """Lexicons written to a directory that the loader reads in place of the shipped ones."""

    def __init__(self, test: unittest.TestCase):
        directory = tempfile.TemporaryDirectory()
        test.addCleanup(directory.cleanup)
        self.path = Path(directory.name)
        for path in LEXICONS.glob("*.json"):
            (self.path / path.name).symlink_to(path)
        patch = mock.patch.object(lexicon_module, "_HERE", self.path)
        patch.start()
        test.addCleanup(patch.stop)
        names = mock.patch.object(tagger_module, "LEXICONS", tagger_module.LEXICONS)
        names.start()
        test.addCleanup(names.stop)
        test.addCleanup(tagger_module.lexicon_name.cache_clear)
        writer_module._writer.cache_clear()
        test.addCleanup(writer_module._writer.cache_clear)
        test.addCleanup(load.cache_clear)

    def write(self, name: str, data: dict) -> None:
        target = self.path / f"{name}.json"
        target.unlink(missing_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tagger_module.LEXICONS = tuple(sorted({*tagger_module.LEXICONS, name}))
        tagger_module.lexicon_name.cache_clear()
        load.cache_clear()


def _tiny(rules: list[dict], **forms) -> dict:
    """An Indonesian lexicon with a writer block of one cardinal rule set."""
    data = _file("id")
    data["writer"] = {"source": "test", "rulesets": {"cardinal": {"source": "test", "rules": rules}},
                      "forms": {"cardinal": {"variants": [{"ruleset": "cardinal", "reason": "standard"}]}, **forms},
                      "decimal": {"word": "koma", "places": 3, "source": "test"}}
    return data


class TestGolden(unittest.TestCase):
    """The words of ovos-number-parser, for every language that has a writer block."""

    def test_every_row_of_every_writer_language_matches(self):
        rows = [row for row in golden_writers.stored() if golden_writers.has_writer(row["lang"])]
        self.assertEqual({row["lang"] for row in rows}, {"id", "ms"})
        self.assertEqual(len(rows), 22698)
        found = golden_writers.mismatches(rows, golden_writers.allowed())
        self.assertEqual([(row, got) for row, got in found[:5]], [])

    def test_the_golden_file_is_the_stored_one(self):
        self.assertEqual(len(golden_writers.stored()), 488631)

    def test_a_changed_rule_makes_the_rows_fail(self):
        variants = Variants(self)
        data = _file("id")
        rules = data["writer"]["rulesets"]["spellout-cardinal"]["rules"]
        next(rule for rule in rules if rule["value"] == "10")["text"] = "sepulu;"
        variants.write("id", data)
        rows = [row for row in golden_writers.stored() if row["lang"] == "id" and row["fn"] == "number"
                and row["arg"] == 10 and "kw" not in row]
        self.assertEqual(len(rows), 1)
        found = golden_writers.mismatches(rows, {})
        self.assertEqual([got for _, got in found], [{"out": "sepulu"}])

    def test_an_allow_list_entry_replaces_the_stored_output_of_its_row(self):
        row = {"lang": "id", "fn": "number", "arg": 10, "out": "sepuluh"}
        wrong = {**row, "out": "sepulu"}
        self.assertEqual(golden_writers.mismatches([wrong], {}), [(wrong, {"out": "sepuluh"})])
        entry = {"lang": "id", "fn": "number", "arg": 10, "out": "sepuluh", "source": "KBBI, \"sepuluh\""}
        self.assertEqual(golden_writers.mismatches([wrong], {golden_writers.key(wrong): entry}), [])

    def test_every_allow_list_entry_names_a_row_that_differs_and_cites_a_source(self):
        rows = {golden_writers.key(row): row for row in golden_writers.stored()}
        for key, entry in golden_writers.allowed().items():
            with self.subTest(row=key):
                self.assertIn(key, rows)
                self.assertTrue(entry["source"])
                self.assertNotEqual(golden_writers.outcome(entry), golden_writers.outcome(rows[key]))


class TestRoundTrip(unittest.TestCase):
    """What the writer says, the reader reads back as the same number."""

    @staticmethod
    def numbers() -> list[int]:
        rng = random.Random(7)
        round_numbers = {d * 10 ** k for k in range(1, 13) for d in range(1, 10)} | {10 ** k + 1 for k in range(3, 13)}
        return list(range(0, 1001)) + sorted(round_numbers) + [rng.randint(1001, 10 ** 9) for _ in range(500)]

    def test_the_reader_reads_every_cardinal_back(self):
        for lang in WRITERS:
            failures = []
            for number in self.numbers():
                words = spell(str(number), lang)[0].text
                found = [(m.text, m.value, m.kind) for m in tag_numbers(words, lang)]
                if found != [(words, str(number), Kind.CARDINAL)]:
                    failures.append((number, words, found))
            with self.subTest(lang=lang):
                self.assertEqual(failures[:3], [])

    DECIMALS = ("0.5", "2.5", "3.14", "12.75", "100.25", "0.001")

    def decimal_failures(self, lang: str) -> list:
        failures = []
        for value in self.DECIMALS:
            words = spell(value, lang)[0].text
            found = [(m.text, m.value) for m in tag_numbers(words, lang)]
            if found != [(words, value)]:
                failures.append((value, words, found))
        return failures

    def test_the_reader_reads_every_decimal_back_in_id(self):
        self.assertEqual(self.decimal_failures("id"), [])

    @unittest.expectedFailure
    def test_the_reader_reads_every_decimal_back_in_ms(self):
        """The writer says "koma", which the Malay lexicon does not read as a decimal mark: it says "perpuluhan"."""
        self.assertEqual(self.decimal_failures("ms"), [])

    @pytest.mark.xfail(strict=True, reason="a denominator over 20 is written as a cardinal and an ordinal that the reader "
                       "splits https://github.com/TigreGotico/numtag/issues/295")
    def test_the_reader_reads_a_fraction_with_a_denominator_over_20_back_as_one_mention(self):
        failures = []
        for lang in WRITERS:
            for numerator, denominator in ((1, 21), (3, 25), (1, 100)):
                text = spell(f"{numerator}/{denominator}", lang)[0].text
                found = [(m.text, Fraction(m.value)) for m in tag_numbers(text, lang)]
                if found != [(text, Fraction(numerator, denominator))]:
                    failures.append((lang, numerator, denominator, text, found))
        self.assertEqual(failures, [])

    @pytest.mark.xfail(strict=True, reason="a whole part before a fraction reads back as another value, 31/3 as 11/3 and "
                       "32/3 as 4 https://github.com/TigreGotico/numtag/issues/295")
    def test_a_mixed_fraction_reads_as_its_parts_or_as_its_whole_value(self):
        # Whether the reader joins the whole part and the fraction is open in the issue; any other value is wrong.
        failures = []
        for lang in WRITERS:
            for value, allowed in (("31/3", {"10", "1/3", "31/3"}), ("32/3", {"10", "2/3", "32/3"})):
                text = spell(value, lang)[0].text
                values = [m.value for m in tag_numbers(text, lang)]
                if not values or set(values) - allowed:
                    failures.append((lang, value, text, values))
        self.assertEqual(failures, [])

    def test_every_literal_word_of_a_rule_is_a_form_of_the_reader(self):
        for lang in WRITERS:
            lexicon = load(lang)
            known = set(lexicon.readings) | lexicon.minus_words | lexicon.decimal_markers | lexicon.joiners
            words = set()
            for spec in _file(lang)["writer"]["rulesets"].values():
                for rule in spec["rules"]:
                    words |= {word.casefold() for text in self.literals(writer_module._parse(rule["text"], lang))
                              for word in text.replace("\u00ad", " ").split()}
            with self.subTest(lang=lang):
                self.assertTrue(words)
                unread = [word for word in sorted(words - known)
                          if [m.text for m in tag_numbers(word, lang)] != [word] and not _issue_305(lang, word)]
                self.assertEqual(unread, [])

    @pytest.mark.xfail(strict=True, reason="https://github.com/TigreGotico/numtag/issues/305")
    def test_the_pt_PT_reader_reads_ordinals_with_two_scale_groups_and_high_scale_words(self):
        found = [[m.value for m in tag_numbers(spell(n, "pt-PT", form=SpokenForm.ORDINAL)[0].text, "pt-PT")]
                 for n in ("347713783", "1000000000000000000")]
        self.assertEqual(found, [["347713783"], ["1000000000000000000"]])

    @classmethod
    def literals(cls, tokens: tuple):
        for kind, value in tokens:
            if kind == "lit":
                yield value
            elif kind == "opt":
                yield from cls.literals(value)

    def test_the_reader_reads_every_ordinal_back(self):
        for lang in WRITERS:
            failures = []
            for number in self.numbers():
                if number == 0:
                    continue
                words = spell(str(number), lang, form=SpokenForm.ORDINAL)[0].text
                found = [(m.text, m.value, m.kind) for m in tag_numbers(words, lang)]
                if found != [(words, str(number), Kind.ORDINAL)] and not _issue_305(lang, words):
                    failures.append((number, words, found))
            with self.subTest(lang=lang):
                self.assertEqual(failures[:3], [])


class TestRevisions(unittest.TestCase):
    def test_every_lexicon_with_no_writer_has_a_stored_revision_and_keeps_it(self):
        stored = json.loads((Path(__file__).parent / "golden" / "revisions.json").read_text(encoding="utf-8"))
        names = sorted(path.stem for path in LEXICONS.glob("*.json") if path.stem not in VERSION_TWO)
        self.assertEqual(sorted(stored), names)
        for name, revision in stored.items():
            with self.subTest(lexicon=name):
                self.assertEqual(numtag.revision(name), revision)

    def test_only_the_writer_lexicons_are_version_two(self):
        names = sorted(path.stem for path in LEXICONS.glob("*.json"))
        for name in names:
            with self.subTest(lexicon=name):
                self.assertEqual(_file(name)["format_version"], 2 if name in VERSION_TWO else 1)
        self.assertEqual(WRITERS, ["id", "ms", "pt-PT"])
        self.assertEqual(VERSION_TWO, ["id", "ms", "pt-BR", "pt-PT"])

    def test_a_change_of_a_writer_rule_changes_the_revision(self):
        before = numtag.revision("id")
        variants = Variants(self)
        data = _file("id")
        data["writer"]["decimal"]["places"] = 2
        variants.write("id", data)
        numtag.lexicon.revision.cache_clear()
        self.addCleanup(numtag.lexicon.revision.cache_clear)
        self.assertNotEqual(numtag.lexicon.revision("id"), before)


class TestExtends(unittest.TestCase):
    def test_a_null_writer_drops_the_writer_of_the_base(self):
        variants = Variants(self)
        variants.write("variant", {"format_version": 2, "extends": "id", "writer": None})
        with self.assertRaises(UnsupportedLanguageError):
            spell("2", "variant")

    def test_a_null_writer_with_no_base_is_refused(self):
        variants = Variants(self)
        data = _file("id")
        data["writer"] = None
        variants.write("id", data)
        with self.assertRaisesRegex(ValueError, "null writer"):
            spell("2", "id")

    def test_a_lexicon_with_no_writer_inherits_the_writer_of_its_base(self):
        variants = Variants(self)
        variants.write("variant", {"format_version": 1, "extends": "id"})
        self.assertEqual(spell("21", "variant")[0].text, "dua puluh satu")
        self.assertEqual(writer_module.writer_block("variant"), _file("id")["writer"])

    def test_a_writer_of_the_file_replaces_the_writer_of_its_base(self):
        variants = Variants(self)
        variants.write("variant", {"format_version": 2, "extends": "id", "writer": _file("ms")["writer"]})
        self.assertEqual(spell("0", "variant")[0].text, "sifar")


class TestLoader(unittest.TestCase):
    def refused(self, data: dict, message: str) -> None:
        variants = Variants(self)
        variants.write("variant", data)
        with self.assertRaisesRegex(ValueError, message):
            writer_module._writer("variant")

    def test_a_version_one_file_with_a_writer_block_is_refused(self):
        data = _tiny([{"value": "0", "text": "nol;"}])
        data["format_version"] = 1
        self.refused(data, "variant: a writer block needs format_version 2")

    def test_an_unknown_key_of_the_block_is_refused_by_name(self):
        data = _tiny([{"value": "0", "text": "nol;"}])
        data["writer"]["bogus"] = 1
        self.refused(data, "variant: unknown key 'bogus' in the writer block")
        data = _tiny([{"value": "0", "text": "nol;", "bogus": 1}])
        self.refused(data, "variant: unknown key 'bogus' in a rule of 'cardinal'")

    def test_a_form_that_names_an_unknown_rule_set_is_refused(self):
        data = _tiny([{"value": "0", "text": "nol;"}])
        data["writer"]["forms"]["cardinal"]["variants"][0]["ruleset"] = "none"
        self.refused(data, "form 'cardinal' names the unknown rule set 'none'")

    def test_a_rule_value_that_is_no_whole_number_is_refused_at_once(self):
        for value in ("x.x", "Inf", "NaN", "010", "1,5", "", "-1", "x"):
            with self.subTest(value=value):
                self.refused(_tiny([{"value": "0", "text": "nol;"}, {"value": value, "text": "x;"}]),
                             "is not '-x' or a whole number with no leading zero")

    def test_a_rule_text_that_the_interpreter_does_not_read_is_refused(self):
        for text in ("$(cardinal,one{a}other{b})$;", "=#,##0=;", "<<a;", "←x←;"):
            with self.subTest(text=text):
                self.refused(_tiny([{"value": "0", "text": text}]), "unsupported rule text")

    def test_a_rule_that_calls_an_unknown_rule_set_is_refused(self):
        self.refused(_tiny([{"value": "0", "text": "=%none=;"}]), "calls the unknown rule set 'none'")


class TestInterpreter(unittest.TestCase):
    def read(self, rules: list[dict], number: str, **forms) -> str:
        variants = Variants(self)
        variants.write("variant", _tiny(rules, **forms))
        return writer_module._writer("variant").render("cardinal", number)

    RULES = [{"value": "0", "text": "zero;"}, {"value": "1", "text": "one;"}, {"value": "2", "text": "two;"},
             {"value": "10", "text": "ten[ →→];"}, {"value": "20", "text": "←← tens[ →→];"},
             {"value": "100", "text": "←← hundred[ →→];", "radix": 10}]

    def test_the_largest_base_below_the_number_gives_the_rule(self):
        self.assertEqual([self.read(self.RULES, n) for n in ("0", "2", "10", "11", "20", "21", "100", "221")],
                         ["zero", "two", "ten", "ten one", "two tens", "two tens one", "one hundred",
                          "two hundred two tens one"])

    def test_an_optional_part_stays_out_when_the_remainder_is_zero(self):
        self.assertEqual(self.read(self.RULES, "30"), "two tens")

    def test_a_radix_that_is_no_power_of_ten_sets_the_divisor(self):
        rules = [{"value": "0", "text": "zero;"}, {"value": "3", "text": "three;"}, {"value": "4", "text": "four;"},
                 {"value": "8", "text": "eight;"}, {"value": "80", "text": "←← score[ →→];", "radix": 20}]
        self.assertEqual(self.read(rules, "83"), "four score three")

    def test_a_soft_hyphen_goes_and_spaces_collapse(self):
        rules = [{"value": "0", "text": "a­b  c;"}]
        self.assertEqual(self.read(rules, "0"), "ab c")

    @pytest.mark.xfail(strict=True, reason="the apostrophe that opens a rule text stays in the words "
                       "https://github.com/TigreGotico/numtag/issues/293")
    def test_an_apostrophe_that_opens_a_rule_text_is_no_part_of_the_words(self):
        # ICU rule text format: a leading apostrophe keeps the space after it and is not output.
        self.assertEqual(self.read([{"value": "0", "text": "' nol;"}], "0").split(), ["nol"])

    def test_a_rule_set_with_no_rule_for_a_number_raises(self):
        rules = [{"value": "5", "text": "five;"}]
        with self.assertRaisesRegex(ValueError, "no rule for 3"):
            self.read(rules, "3")


class TestSpell(unittest.TestCase):
    def test_a_spelling_has_text_reason_and_rank(self):
        (spelling,) = spell("21", "id")
        self.assertEqual((spelling.text, spelling.reason, spelling.rank),
                         ("dua puluh satu", SpellingReason.STANDARD, 0))

    def test_a_language_with_no_writer_raises_unsupported_language(self):
        with self.assertRaises(UnsupportedLanguageError):
            spell("1", "en")
        with self.assertRaises(UnsupportedLanguageError):
            spell("1", "xx")

    def test_a_tag_reads_the_writer_of_its_lexicon(self):
        self.assertEqual(spell("8", "ms")[0].text, "lapan")
        self.assertEqual(spell("8", "ms-MY")[0].text, "lapan")
        self.assertEqual(spell("8", "id_ID")[0].text, "delapan")

    def test_two_variants_with_the_same_words_give_one_spelling(self):
        variants = Variants(self)
        data = _tiny([{"value": "0", "text": "nol;"}])
        data["writer"]["forms"]["cardinal"]["variants"] = [{"ruleset": "cardinal", "reason": "standard"},
                                                           {"ruleset": "cardinal", "reason": "variant_spelling"}]
        variants.write("variant", data)
        self.assertEqual([(s.text, s.reason, s.rank) for s in spell("0", "variant")],
                         [("nol", SpellingReason.STANDARD, 0)])

    def test_the_sign_of_zero_is_no_minus_word(self):
        self.assertEqual(spell("-0", "id")[0].text, "nol")
        self.assertEqual(spell("-0", "ms")[0].text, "sifar")
        self.assertEqual(spell("-0.0", "id")[0].text, "nol")

    def test_a_program_that_only_reads_never_loads_the_writer(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import numtag; "
                "assert numtag.__file__.startswith(sys.argv[1]), numtag.__file__; "
                "assert 'numtag.writer' not in sys.modules; numtag.tag_numbers('dua', 'id'); "
                "assert 'numtag.writer' not in sys.modules; numtag.spell('2', 'id'); "
                "assert 'numtag.writer' in sys.modules")
        subprocess.run([sys.executable, "-I", "-c", code, str(PACKAGE.parent)], check=True, cwd=tempfile.gettempdir())

    def test_a_value_that_is_no_digit_string_raises(self):
        for value in ("", "x", "1e3", "١٢", "--5", "5.", ".5", "-", "1 2"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                spell(value, "id")

    def test_a_fraction_with_a_term_that_is_no_whole_number_raises_value_error(self):
        for value in ("٣/٤", "1/ 2", "1.5/2", "1/2.5", "1/2/3", "a/b", "/2", "--1/2", "1/", "/", "1/-"):
            with self.subTest(value=value), self.assertRaises(ValueError) as caught:
                spell(value, "id")
            self.assertNotIsInstance(caught.exception, ZeroDivisionError)
        self.assertEqual(spell("-1/2", "id")[0].text, spell("1/-2", "id")[0].text)

    def test_the_forms(self):
        self.assertEqual(spell("1999", "id", form=SpokenForm.YEAR)[0].text, spell("1999", "id")[0].text)
        self.assertEqual(spell("-3", "id", form=SpokenForm.DIGITS)[0].text, "minus tiga")
        self.assertEqual(spell("30.5", "id", form=SpokenForm.DIGITS)[0].text, "tiga nol koma lima")

    def test_a_large_number_reads_without_a_limit_and_a_repeated_scale_word_reads_scientifically(self):
        self.assertEqual(spell("1000000000000000", "id")[0].text, "seribu triliun")
        self.assertEqual(spell("1" + "0" * 30, "id")[0].text, "satu kali sepuluh pangkat tiga puluh")

    def test_decimals_round_half_away_from_zero_at_places(self):
        self.assertEqual([spell("2.675", "id", places=p)[0].text for p in (0, 1, 2, 3)],
                         ["tiga", "dua koma tujuh", "dua koma enam delapan", "dua koma enam tujuh lima"])
        self.assertEqual(spell("0.4", "id", places=0)[0].text, "nol")
        self.assertEqual(spell("-0.4", "id", places=0)[0].text, "nol")
        self.assertEqual(spell("0.0004", "id", places=2)[0].text, "nol koma nol nol nol empat")

    def test_gender_and_scale_change_nothing_where_a_lexicon_lists_no_reading(self):
        self.assertEqual(spell("2", "id", gender="feminine", scale="long"), spell("2", "id"))

    def test_scale_selects_the_form_of_that_scale_and_the_setting_is_the_default(self):
        variants = Variants(self)
        data = _tiny([{"value": "0", "text": "short;"}])
        data["writer"]["rulesets"]["long"] = {"source": "test", "rules": [{"value": "0", "text": "long;"}]}
        data["writer"]["forms"]["cardinal"]["scale"] = {
            "long": {"variants": [{"ruleset": "long", "reason": "standard"}]}}
        data["settings"]["scale"] = {"value": "long", "source": "test"}
        variants.write("id", data)
        self.assertEqual([spell("2", "id", scale=s)[0].text for s in (None, "long", "short")],
                         ["long", "long", "short"])

    def test_a_scale_form_that_names_another_scale_is_refused(self):
        variants = Variants(self)
        data = _tiny([{"value": "0", "text": "nol;"}])
        data["writer"]["forms"]["cardinal"]["scale"] = {"metric": {"variants": []}}
        variants.write("id", data)
        with self.assertRaisesRegex(ValueError, "scale 'metric'"):
            spell("2", "id")

    def test_decimals_read_as_one_number_where_the_lexicon_or_the_call_says_so(self):
        variants = Variants(self)
        data = _file("id")
        data["writer"]["decimal"]["read"] = "number"
        variants.write("id", data)
        self.assertEqual(spell("2.25", "id")[0].text, "dua koma dua puluh lima")
        self.assertEqual(spell("0.05", "id")[0].text, "nol koma nol lima")
        self.assertEqual(spell("2.25", "id", decimals="digits")[0].text, "dua koma dua lima")

    def test_a_negative_ordinal_reads_with_the_minus_rule_of_its_rule_set(self):
        variants = Variants(self)
        data = _file("id")
        data["writer"]["rulesets"]["spellout-ordinal"]["rules"].append({"value": "-x", "text": "minus →→;"})
        variants.write("id", data)
        self.assertEqual(spell("-2", "id", form=SpokenForm.ORDINAL)[0].text, "minus kedua")
        with self.assertRaises(ValueError):
            spell("-2.5", "id", form=SpokenForm.ORDINAL)

    def test_a_fraction_with_no_mixed_number_counts_its_denominator(self):
        variants = Variants(self)
        data = _file("id")
        data["writer"]["fraction"] = {"mixed": False, "limit": 10, "named": {"2": "half"}, "plural": "s",
                                      "denominator": "{cardinal} parts", "single": "{denominator}", "source": "test"}
        variants.write("id", data)
        self.assertEqual([spell(v, "id")[0].text for v in ("1/2", "3/2", "3/20", "3/21", "1/1000")],
                         ["satu half", "tiga halfs", "tiga dua puluh parts", "tiga dua puluh satu parts", "satu keseribu"])

    def test_the_fraction_of_a_zero_denominator_raises(self):
        with self.assertRaises(ZeroDivisionError):
            spell("1/0", "id")


class TestFraction(unittest.TestCase):
    def test_a_decimal_is_a_fraction_in_lowest_terms(self):
        self.assertEqual([writer_module.as_fraction(v) for v in ("0.75", "-0.5", "5.5", "0.125", "7", "-3")],
                         ["3/4", "-1/2", "11/2", "1/8", "7", "-3"])


class TestNamedDenominator(unittest.TestCase):
    @pytest.mark.xfail(strict=True, reason="a named denominator drops the numerator also where it is more than 1 "
                       "https://github.com/TigreGotico/numtag/issues/294")
    def test_a_named_denominator_keeps_a_numerator_other_than_one(self):
        variants = Variants(self)
        data = _file("id")
        data["writer"]["fraction"]["named"]["4"] = "seperempat"
        variants.write("variant", data)
        # 3/4 is three of the four parts and 7/4 is 1 + 3/4, the way id.wikipedia "Pecahan" writes 3 3/4.
        self.assertEqual([spell(value, "variant")[0].text for value in ("1/4", "3/4", "7/4")],
                         ["seperempat", "tiga perempat", "satu tiga perempat"])


class TestZeroFraction(unittest.TestCase):
    @pytest.mark.xfail(strict=True, reason="-0/5 is written with a minus word although its value is zero "
                       "https://github.com/TigreGotico/numtag/issues/295")
    def test_a_fraction_of_a_zero_numerator_has_no_minus_word(self):
        self.assertEqual([spell("-0/5", lang)[0].text for lang in WRITERS],
                         [spell("0/5", lang)[0].text for lang in WRITERS])


class TestMention(unittest.TestCase):
    def test_a_fraction_mention_speaks_as_a_fraction_also_when_its_value_is_a_decimal(self):
        for text, spoken in (("setengah", "setengah"), ("tiga perempat", "tiga perempat"), ("sepertiga", "sepertiga")):
            mention = tag_numbers(text, "id")[0]
            with self.subTest(text=text):
                self.assertEqual(mention.kind, Kind.FRACTION)
                self.assertEqual(mention.spoken()[0].text, spoken)

    def test_a_mention_names_the_lexicon_that_read_it(self):
        self.assertEqual(tag_numbers("dua", "id-ID")[0].lang, "id")
        self.assertEqual(tag_numbers("duas", "pt")[0].lang, "pt-PT")

    def test_the_language_is_out_of_equality_and_repr(self):
        mention = tag_numbers("dua", "id")[0]
        self.assertEqual(mention, numtag.NumberMention(mention.char_span, "dua", "2", Kind.CARDINAL, mention.form))
        self.assertNotIn("lang", repr(mention))

    def test_a_mention_speaks_its_value(self):
        self.assertEqual(tag_numbers("21 orang", "id")[0].spoken()[0].text, "dua puluh satu")
        self.assertEqual(tag_numbers("ke-3", "id")[0].spoken()[0].text, "ketiga")
        self.assertEqual(tag_numbers("1/3", "id")[0].spoken()[0].text, "sepertiga")

    def test_a_mention_with_no_language_needs_one(self):
        mention = numtag.NumberMention((0, 1), "2", "2", Kind.CARDINAL, numtag.Form.DIGITS)
        with self.assertRaisesRegex(ValueError, "pass lang"):
            mention.spoken()
        self.assertEqual(mention.spoken("ms")[0].text, "dua")


if __name__ == "__main__":
    unittest.main()
