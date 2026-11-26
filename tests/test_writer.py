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
    return lang in ("pt-PT", "pt-BR") and bool(ISSUE_305.search(text))


ISSUE_315 = re.compile(r"\b(?:veinti[a-z]+|(?:cuarent|cincuent|sesent|setent|ochent|novent)a?|treintai[a-z]+|"
                       r"[a-z]+ientos[a-z]*|ciento[a-z]+|[a-z]*mil[a-z]*)avos?\b|\w+(?:mil|llon)ésim[oa]s?\b|^ésimo$"
                       r"|^(?:un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve)avo$")  # the rest part of "treintaiunavo"


def _issue_315(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/315: the es reader misses -avo words past 30, veinti- -avo words, and fused scale ordinals."""
    return lang == "es" and bool(ISSUE_315.search(text))


ISSUE_318 = re.compile(r"(?:bilion|biliard|trilion|quadrilion)[a-z]*esim[oaie]\b|(?:milion|miliard)(?!esim)[a-z]+(?:esim|decim)[oaie]\b")


def _issue_318(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/318: the it reader misses an ordinal of "bilione" and up,
    and a fused scale ordinal with a rest ("milioneunesimo")."""
    return lang == "it" and bool(ISSUE_318.search(text))


ISSUE_323 = re.compile(r"(?:centesim|millesim)[oa] (?:prim|second|decim|undicesim)[oa]$")


def _issue_323(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/323: the it reader reads "centesimo decimo" as two ordinals."""
    return lang == "it" and bool(ISSUE_323.search(text))


ISSUE_325 = re.compile(r"(?:billion|billiard|trillion)ième")


def _issue_325(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/325: the fr reader misses ordinals of "billion" and up."""
    return lang.startswith("fr-") and bool(ISSUE_325.search(text))


ISSUE_329 = re.compile(r"^(?:al|a|de)$|sut[ăe]lea|sut[ae]$|mielea|miilea|mia$|(?:milion|miliard|bilion|biliard|trilion)(?:ulea|a)$|(?:milioan|miliard|bilioan|biliard|trilioan)elea$")


def _issue_360(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/360: the eu reader does not read a part of more than one word
    ("hogeita baten bat"); its last word is also the genitive of the count ("etxe baten")."""
    return lang == "eu" and text in ("baten", "biren", "hiruren", "lauren")


def _issue_329(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/329: the ro reader leaves out the article "al"/"a" and misses
    the ordinals of a counted hundred, thousand or scale word ("al o sutălea", "al două miilea"). The bare words
    "al", "a" and "de" are exempt too: the reader reads "de" only inside a number ("douăzeci de mii")."""
    if lang != "ro":
        return False
    bare = re.sub(r"^(?:al|a) ", "", text)
    if ISSUE_329.search(bare) or ISSUE_329.search(text):
        return True
    return bare != text and [(m.text, m.kind) for m in tag_numbers(bare, lang)] == [(bare, Kind.ORDINAL)]


SCALE_ORDINAL_GL = re.compile(r"\b(?:mil|millon|billon|trillon)ésim[oa]\b")


def _issue_331(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/331: the gl reader splits an ordinal with two scale ordinals."""
    return lang == "gl" and len(SCALE_ORDINAL_GL.findall(text)) >= 2


def _issue_343(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/343: the en reader reads "one hundredth" and ", five hundredth"
    as fractions."""
    return lang in ("en", "en-US") and re.search(r"(^|, )([a-z-]+ )?(hundred|thousand|[a-z]+illion)th$", text) is not None


def _da_hundred(lang: str, text: str) -> bool:
    """sproget.dk «Den 101. dalmatiner»: the ordinal 100 is "hundrede", "fordi den falder helt eller delvis sammen med
    mængdetallet", so a round hundred reads as the cardinal. The ordinal "tusinde" (CLDR da) is also the cardinal
    "tusind(e)" of sproget.dk «Et eller flere ord»."""
    return lang == "da" and text.endswith(("hundrede", "tusinde"))


def _issue_339(lang: str, text: str) -> bool:
    """https://github.com/TigreGotico/numtag/issues/339: the nl reader splits "een miljoenste" into een + miljoenste."""
    return lang == "nl" and re.fullmatch(r"een \w+(joen|jard)ste", text) is not None


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
        langs = {row["lang"] for row in rows}
        self.assertTrue({"id", "ms", "pt-PT", "es", "nb"} <= langs)
        self.assertEqual(langs, {row["lang"] for row in golden_writers.stored()} & set(WRITERS))
        self.assertEqual(len(rows), 11349 * len(langs))
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

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="a denominator over 20 is written as a cardinal and an ordinal that the reader "
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

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="a whole part before a fraction reads back as another value, 31/3 as 11/3 and "
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
            block = _file(lang)["writer"]
            parsed = {name: [writer_module._parse(rule["text"], lang) for rule in spec["rules"]]
                      for name, spec in block["rulesets"].items()}
            glued = self.glued(parsed) - self.form_rulesets(block)
            words = set()
            for name, rules in parsed.items():
                for tokens in rules:
                    words |= {word.casefold() for text in self.literals(tokens, name in glued)
                              for word in text.replace("\u00ad", " ").split()}
            with self.subTest(lang=lang):
                self.assertTrue(words)
                unread = [word for word in sorted(words - known)
                          if [m.text for m in tag_numbers(word, lang)] != [word] and not _issue_305(lang, word) and not _issue_315(lang, word) and not _issue_325(lang, word) and not _issue_329(lang, word) and not _issue_360(lang, word)]
                self.assertEqual(unread, [])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/360")
    def test_the_eu_reader_reads_a_part_of_more_than_one_word(self):
        self.assertEqual([m.value for m in tag_numbers("hogeita baten bat", "eu")], ["1/21"])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/305")
    def test_the_pt_PT_reader_reads_ordinals_with_two_scale_groups_and_high_scale_words(self):
        found = [[m.value for m in tag_numbers(spell(n, "pt-PT", form=SpokenForm.ORDINAL)[0].text, "pt-PT")]
                 for n in ("347713783", "1000000000000000000")]
        self.assertEqual(found, [["347713783"], ["1000000000000000000"]])

    @classmethod
    def glued(cls, parsed: dict) -> set:
        """The rule sets that a rule calls straight after a literal with no space ("vent→%tail→")."""
        names = set()
        def walk(tokens):
            for k, (kind, value) in enumerate(tokens):
                if kind == "opt":
                    walk(value)
                elif kind != "lit" and value and k and tokens[k - 1][0] == "lit" and not tokens[k - 1][1][-1:].isspace():
                    names.add(value)
        for rules in parsed.values():
            for tokens in rules:
                walk(tokens)
        return names

    @staticmethod
    def form_rulesets(block: dict) -> set:
        found = set()
        def walk(node):
            if isinstance(node, dict):
                found.update([node["ruleset"]] if isinstance(node.get("ruleset"), str) else [])
                for item in node.values():
                    walk(item)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
        walk(block["forms"])
        return found

    @classmethod
    def literals(cls, tokens: tuple, glued: bool = False):
        """The literal text of the rule, with a fragment fused to a call ("vigesimo" in "vigesimo→→") or to
        the text before a glued rule set ("a" in "trent→%tail→") dropped."""
        for k, (kind, value) in enumerate(tokens):
            if kind == "lit":
                if (k and tokens[k - 1][0] != "lit" or not k and glued) and not value[0].isspace():
                    value = value.partition(" ")[2]
                if k + 1 < len(tokens) and tokens[k + 1][0] not in ("lit",) and not value[-1:].isspace():
                    value = value.rpartition(" ")[0]
                yield value
            elif kind == "opt":
                yield from cls.literals(value, glued and not k)

    def test_the_reader_reads_every_ordinal_back(self):
        for lang in WRITERS:
            failures = []
            for number in self.numbers():
                if number == 0:
                    continue
                words = spell(str(number), lang, form=SpokenForm.ORDINAL)[0].text
                found = [(m.text, m.value, m.kind) for m in tag_numbers(words, lang)]
                if found != [(words, str(number), Kind.ORDINAL)] and not _issue_305(lang, words) and not _issue_315(lang, words) and not _issue_318(lang, words) and not _issue_323(lang, words) and not _issue_325(lang, words) and not _issue_329(lang, words) and not _issue_331(lang, words) and not _issue_343(lang, words) and not _issue_339(lang, words) and not _da_hundred(lang, words):
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
        self.assertTrue({"id", "ms", "pt-PT", "pt-BR", "es", "nb"} <= set(WRITERS))
        self.assertTrue(set(WRITERS) <= set(VERSION_TWO))

    def test_a_change_of_a_writer_rule_changes_the_revision(self):
        before = numtag.revision("id")
        variants = Variants(self)
        data = _file("id")
        data["writer"]["decimal"]["places"] = 2
        variants.write("id", data)
        numtag.lexicon.revision.cache_clear()
        self.addCleanup(numtag.lexicon.revision.cache_clear)
        self.assertNotEqual(numtag.lexicon.revision("id"), before)


class TestSpanish(unittest.TestCase):
    """Values from RAE DPD «uno», «ciento» and «fraccionarios», and CLDR RBNF es (unicode-rbnf 2.5.1)."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "es", **kw)[0].text

    def test_the_cardinal_takes_the_apocope_only_before_a_noun(self):
        self.assertEqual([self.say("21"), self.say("21", gender="masculine"), self.say("21", gender="feminine")],
                         ["veintiuno", "veintiún", "veintiuna"])

    def test_a_thousand_millions_is_a_count_of_millions(self):
        self.assertEqual(self.say("1000000000"), "mil millones")

    def test_ordinals_fuse_the_count_of_a_scale_word(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("21", "2000", "22000", "1000000000")],
                         ["vigesimoprimero", "dosmilésimo", "veintidosmilésimo", "milmillonésimo"])

    def test_eighteenth_drops_one_o(self):
        self.assertEqual(self.say("18", form=SpokenForm.ORDINAL, gender="feminine"), "decimoctava")

    def test_a_denominator_past_ten_reads_avo(self):
        self.assertEqual([self.say(f) for f in ("2/3", "1/200", "3/56", "21/50")],
                         ["dos tercios", "un doscientosavo", "tres cincuentaiseisavos", "veintiún cincuentavos"])


class TestItalian(unittest.TestCase):
    """Values from Accademia della Crusca (consulenza 1077), Treccani «numerali»
    and CLDR RBNF it (unicode-rbnf 2.5.1)."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "it", **kw)[0].text

    def test_cento_keeps_its_vowel_before_otto_and_uno(self):
        self.assertEqual([self.say(n) for n in ("101", "108", "180")], ["centouno", "centootto", "centottanta"])

    def test_a_count_before_mila_and_milioni_keeps_the_full_uno(self):
        self.assertEqual([self.say(n) for n in ("21000", "23000", "21000000")],
                         ["ventunomila", "ventitremila", "ventuno milioni"])

    def test_a_compound_that_ends_in_three_takes_the_accent(self):
        self.assertEqual([self.say(n) for n in ("3", "23", "1003", "2003", "100003", "23000", "1000003")],
                         ["tre", "ventitré", "milletré", "duemilatré", "centomilatré", "ventitremila", "un milione tre"])

    def test_only_a_bare_one_takes_the_feminine(self):
        self.assertEqual([self.say(n, gender="feminine") for n in ("1", "21")], ["una", "ventuno"])

    def test_ordinals_are_one_word(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("23", "108", "1001", "2000", "1000000")],
                         ["ventitreesimo", "centoottesimo", "millesimo primo", "duemillesimo", "milionesimo"])

    def test_the_euphony_ordinals_are_spaced(self):
        """Vocabolario Treccani «ordinale»: "centesimo decimo, millesimo primo, millesimo secondo, millesimo decimo,
        millesimo undecimo o undicesimo, ecc. (in questi casi la grafia staccata è preferita)"."""
        ordinals = [self.say(n, form=SpokenForm.ORDINAL) for n in ("110", "1001", "1002", "1010", "1011", "1003", "2010")]
        self.assertEqual(ordinals, ["centesimo decimo", "millesimo primo", "millesimo secondo", "millesimo decimo",
                                    "millesimo undicesimo", "milletreesimo", "duemiladecimo"])
        self.assertEqual(self.say("310", form=SpokenForm.ORDINAL, gender="feminine"), "trecentesima decima")

    def test_a_fraction_is_a_cardinal_and_a_plural_ordinal(self):
        self.assertEqual([self.say(f) for f in ("1/2", "2/3", "3/2", "7/1000")],
                         ["un mezzo", "due terzi", "tre mezzi", "sette millesimi"])


class TestFrench(unittest.TestCase):
    """The traditional spelling of the Académie française («Questions de langue: nombres»), and CLDR RBNF fr."""

    def say(self, value: str, lang: str = "fr-FR", **kw) -> str:
        return spell(value, lang, **kw)[0].text

    def test_et_and_the_hyphen_below_one_hundred(self):
        self.assertEqual([self.say(n) for n in ("21", "71", "72", "81", "99")],
                         ["vingt et un", "soixante et onze", "soixante-douze", "quatre-vingt-un", "quatre-vingt-dix-neuf"])

    def test_vingt_and_cent_take_the_plural_s_only_when_final_or_before_a_noun(self):
        self.assertEqual([self.say(n) for n in ("80", "200", "201", "80000", "200000", "200000000")],
                         ["quatre-vingts", "deux cents", "deux cent un", "quatre-vingt mille", "deux cent mille",
                          "deux cents millions"])

    def test_belgium_and_switzerland(self):
        self.assertEqual([self.say(n, "fr-BE") for n in ("70", "80", "91")], ["septante", "quatre-vingts", "nonante et un"])
        self.assertEqual([self.say(n, "fr-CH") for n in ("80", "81", "80000")], ["huitante", "huitante et un", "huitante mille"])

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("1", "5", "9", "21", "80", "1001", "1000000", "1000001")],
                         ["premier", "cinquième", "neuvième", "vingt et unième", "quatre-vingtième", "mille et unième",
                          "millionième", "un million unième"])
        self.assertEqual(self.say("1", form=SpokenForm.ORDINAL, gender="feminine"), "première")

    def test_vingt_and_cent_before_a_scale_ordinal_take_no_s(self):
        """OQLF BDL 21532: invariable "lorsqu'ils ont une valeur ordinale"; the noun before a rest keeps the s."""
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("80000000", "200000000", "80000001", "100000000")],
                         ["quatre-vingt millionième", "deux cent millionième", "quatre-vingts millions unième",
                          "cent millionième"])

    def test_fractions(self):
        self.assertEqual([self.say(f) for f in ("1/2", "2/3", "3/4", "5/11")],
                         ["un demi", "deux tiers", "trois quarts", "cinq onzièmes"])


class TestGalician(unittest.TestCase):
    """RAG e ILG, Normas ortográficas e morfolóxicas, §16."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "gl", **kw)[0].text

    def test_cardinals(self):
        self.assertEqual([self.say(n) for n in ("21", "100", "101", "121", "200", "500", "1001", "2000000")],
                         ["vinte e un", "cen", "cento un", "cento vinte e un", "douscentos", "cincocentos", "mil un",
                          "dous millóns"])
        self.assertEqual([self.say(n, gender="feminine") for n in ("21", "22", "200", "2000", "200000")],
                         ["vinte e unha", "vinte e dúas", "duascentas", "dúas mil", "duascentas mil"])

    def test_ordinals_take_the_feminine_on_the_last_word_only(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("7", "11", "12", "21", "101", "3000", "3001")],
                         ["sétimo", "undécimo", "duodécimo", "vixésimo primeiro", "centésimo primeiro",
                          "tres milésimo", "tres milésimo primeiro"])
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL, gender="feminine") for n in ("11", "13", "21", "3000")],
                         ["undécima", "décimo terceira", "vixésimo primeira", "tres milésima"])

    def test_partitives(self):
        self.assertEqual([self.say(f) for f in ("1/2", "3/2", "2/3", "1/16", "2/29", "7/345", "3/1000")],
                         ["un medio", "tres medios", "dous terzos", "un dezaseisavo", "dous vinte e noveavos",
                          "sete trescentos corenta e cincoavos", "tres milésimos"])


class TestEnglish(unittest.TestCase):
    """OALD «and» and «billion», GPO Style Manual 6.36 and 12.20, CLDR RBNF en."""

    def say(self, value: str, variant: int = 0, **kw) -> str:
        return spell(value, "en", **kw)[variant].text

    def test_british_and_first_american_second(self):
        self.assertEqual(self.say("2264"), "two thousand two hundred and sixty-four")
        self.assertEqual(self.say("1850", 1), "one thousand eight hundred fifty")
        self.assertEqual(self.say("152305", 1), "one hundred fifty-two thousand three hundred five")
        self.assertEqual(self.say("1000001"), "one million and one")

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("0", "12", "21", "40", "101", "1000000")],
                         ["zeroth", "twelfth", "twenty-first", "fortieth", "one hundred and first", "one millionth"])

    def test_the_long_scale_billion_is_a_million_million(self):
        self.assertEqual([self.say(n, scale="long") for n in ("1000000000", "1000000000000")],
                         ["one thousand million", "one billion"])
        self.assertEqual(self.say("1000000000000"), "one trillion")

    def test_en_us_drops_the_and(self):
        self.assertEqual([spell(n, "en-US")[0].text for n in ("2264", "1000001")],
                         ["two thousand two hundred sixty-four", "one million one"])
        self.assertEqual(spell("101", "en-US", form=SpokenForm.ORDINAL)[0].text, "one hundred first")
        self.assertEqual(spell("2264", "en-GB")[0].text, "two thousand two hundred and sixty-four")

    def test_fractions(self):
        self.assertEqual([self.say(f) for f in ("1/2", "3/2", "2/3", "3/4", "1/100", "7/1000000")],
                         ["one half", "three halves", "two thirds", "three quarters", "one hundredth", "seven millionths"])



class TestBasque(unittest.TestCase):
    """Euskaltzaindia, 7., 18. and 203. arauak."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "eu", **kw)[0].text

    def test_cardinals_follow_the_examples_of_the_norms(self):
        self.assertEqual([self.say(n) for n in ("18", "21", "30", "101", "1200", "1201", "1984", "13425", "1200000",
                                                "1647413", "2700000", "60200001", "1000000000", "1000000000000")],
                         ["hemezortzi", "hogeita bat", "hogeita hamar", "ehun eta bat", "mila eta berrehun",
                          "mila berrehun eta bat", "mila bederatziehun eta laurogeita lau",
                          "hamahiru mila laurehun eta hogeita bost", "milioi bat eta berrehun mila",
                          "milioi bat seiehun eta berrogeita zazpi mila laurehun eta hamahiru",
                          "bi milioi eta zazpiehun mila", "hirurogei milioi berrehun mila eta bat", "mila milioi",
                          "bilioi bat"])

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("0", "1", "5", "21", "25", "101", "1001", "1000000")],
                         ["zerogarren", "lehen", "bosgarren", "hogeita batgarren", "hogeita bosgarren",
                          "ehun eta batgarren", "mila eta batgarren", "milioigarren"])

    def test_fractions(self):
        self.assertEqual([self.say(f) for f in ("1/3", "1/21", "1/1000000", "2/3", "3/2", "7/60", "13/47")],
                         ["heren bat", "hogeita baten bat", "milioiren bat", "bi heren", "hiru erdi",
                          "zazpi hirurogeiren", "hamahiru zati berrogeita zazpi"])

    def test_decimals_and_negatives(self):
        self.assertEqual([self.say(n) for n in ("0.27", "-15")], ["zero koma hogeita zazpi", "minus hamabost"])


class TestDanish(unittest.TestCase):
    """CLDR RBNF da, sproget.dk and Den Danske Ordbog."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "da", **kw)[0].text

    def test_cardinals(self):
        self.assertEqual([self.say(n) for n in ("21", "55", "99", "100", "101", "1001", "2000000")],
                         ["enogtyve", "femoghalvtreds", "nioghalvfems", "hundrede", "hundrede og en", "tusind og en",
                          "to millioner"])
        self.assertEqual(self.say("1", gender="neuter"), "et")

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("2", "20", "21", "100", "101", "1000000")],
                         ["anden", "tyvende", "enogtyvende", "hundrede", "hundrede og første", "millionte"])
        self.assertEqual([s.text for s in spell("40", "da", form=SpokenForm.ORDINAL)], ["fyrrende", "fyrretyvende"])
        self.assertEqual(self.say("2", form=SpokenForm.ORDINAL, gender="neuter"), "andet")

    def test_fractions_take_the_ordinal_and_del(self):
        self.assertEqual([self.say(f) for f in ("2/3", "3/4", "1/27", "1/100", "1/2")],
                         ["to tredjedele", "tre fjerdedele", "en syvogtyvendedel", "en hundrededel", "en halv"])


class TestNorwegianNynorsk(unittest.TestCase):
    """CLDR RBNF nn, Nynorskordboka and Språkrådet, «Tredjedel, tredel, fjerdedel, firedel og så vidare»."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "nn", **kw)[0].text

    def test_cardinals(self):
        self.assertEqual([self.say(n) for n in ("1", "21", "101", "1001", "1000000", "2000000")],
                         ["éin", "tjueein", "hundre og ein", "tusen og ein", "éin million", "to millionar"])
        self.assertEqual([self.say("1", gender=g) for g in ("masculine", "feminine", "neuter")], ["éin", "éi", "eitt"])

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("1", "13", "20", "21", "30", "100", "1000000")],
                         ["første", "trettande", "tjuande", "tjueførste", "trettiande", "hundrede", "millionte"])

    def test_fractions_take_the_cardinal(self):
        self.assertEqual([self.say(f) for f in ("1/3", "2/3", "8/13")], ["ein tredel", "to tredelar", "åtte trettendelar"])


class TestNorwegianBokmal(unittest.TestCase):
    """CLDR RBNF no, Bokmålsordboka and Språkrådet, «Tall, tid og dato»."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "nb", **kw)[0].text

    def test_cardinals(self):
        self.assertEqual([self.say(n) for n in ("21", "101", "121", "1001", "1100", "2000000", "2000000001")],
                         ["tjueen", "hundre og en", "hundre og tjueen", "tusen og en", "tusen hundre", "to millioner",
                          "to milliarder en"])
        self.assertEqual([self.say("1", gender=g) for g in ("masculine", "feminine", "neuter")], ["en", "ei", "ett"])
        self.assertEqual([[self.say(n, gender=g) for n in ("21", "101", "1001")] for g in ("feminine", "neuter")],
                         [["tjueen", "hundre og ei", "tusen og ei"], ["tjueett", "hundre og ett", "tusen og ett"]])
        self.assertEqual(self.say("1000000"), "én million")

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("2", "13", "20", "21", "100", "1000", "2000001")],
                         ["andre", "trettende", "tjuende", "tjueførste", "hundrede", "tusende", "to millioner første"])

    def test_fractions_take_the_cardinal(self):
        self.assertEqual([self.say(f) for f in ("1/3", "2/3", "8/13", "9/34", "1/2")],
                         ["en tredel", "to tredeler", "åtte trettendeler", "ni trettifiredeler", "en halv"])


class TestDutch(unittest.TestCase):
    """Taaladvies.net, «Aaneenschrijven van telwoorden (algemeen)»."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "nl", **kw)[0].text

    def test_one_word_up_to_duizend_then_a_space(self):
        self.assertEqual([self.say(n) for n in ("21", "43", "101", "6028", "271850", "3000000", "5200000000")],
                         ["eenentwintig", "drieënveertig", "honderdeen", "zesduizend achtentwintig",
                          "tweehonderdeenenzeventigduizend achthonderdvijftig", "drie miljoen",
                          "vijf miljard tweehonderd miljoen"])

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("1", "3", "20", "100", "102", "135", "3220", "4000000", "4400000")],
                         ["eerste", "derde", "twintigste", "honderdste", "honderdtweede", "honderdvijfendertigste",
                          "drieduizend tweehonderdtwintigste", "vier miljoenste", "vier miljoen vierhonderdduizendste"])

    def test_fractions(self):
        self.assertEqual([self.say(f) for f in ("2/3", "4/13", "47/10000", "15/827000")],
                         ["twee derde", "vier dertiende", "zevenenveertig tienduizendste",
                          "vijftien achthonderdzevenentwintigduizendste"])


    def test_a_one_of_its_own_is_stressed(self):
        """Taaladvies.net, «Eén / een van de»: "uitspraaktekens op een als men een precies aantal bedoelt"."""
        self.assertEqual([[x.text for x in spell(n, "nl")] for n in ("1", "1000000", "1001", "101", "21")],
                         [["één", "een"], ["één miljoen", "een miljoen"], ["duizend één", "duizend een"],
                          ["honderdeen"], ["eenentwintig"]])
        self.assertEqual([spell(n, "nl", form=SpokenForm.ORDINAL)[0].text for n in ("1000000", "1000001")],
                         ["miljoenste", "één miljoen eerste"])


class TestGerman(unittest.TestCase):
    """Amtliches Regelwerk (2024), § 36(1.6) and § 56(6) E5."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "de", **kw)[0].text

    def test_one_word_below_a_million_and_the_scale_words_apart(self):
        self.assertEqual([self.say(n) for n in ("1", "21", "101", "1989", "700", "1000000", "2000500000")],
                         ["eins", "einundzwanzig", "einhunderteins", "eintausendneunhundertneunundachtzig",
                          "siebenhundert", "eine Million", "zwei Milliarden fünfhunderttausend"])
        self.assertEqual([self.say("1", gender=g) for g in ("masculine", "feminine", "neuter")], ["ein", "eine", "ein"])

    def test_ordinals_are_one_word(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("17", "100", "500000", "2000000")],
                         ["siebzehnte", "einhundertste", "fünfhunderttausendste", "zweimillionste"])

    def test_fractions_are_capital_nouns(self):
        self.assertEqual([self.say(f) for f in ("1/3", "1/5", "9/10", "3/4", "5/100")],
                         ["ein Drittel", "ein Fünftel", "neun Zehntel", "drei Viertel", "fünf Hundertstel"])


    def test_case_and_gender(self):
        """Duden online, «hundertundein»: "hundertundeinen Krimi lesen"; «tausendundein»: "Tausendundeiner Nacht"."""
        self.assertEqual([spell(n, "de", case=c, gender=g)[0].text for n, c, g in
                          (("1", "dative", "feminine"), ("101", "accusative", "masculine"), ("1001", "dative", "feminine"),
                           ("1", "genitive", "neuter"), ("21", "dative", "masculine"))],
                         ["einer", "einhunderteinen", "eintausendeiner", "eines", "einundzwanzig"])
        self.assertEqual([(x.text, x.reason.value) for x in spell("3", "de", form=SpokenForm.ORDINAL, case="dative",
                                                                  gender="masculine")],
                         [("dritten", "standard"), ("drittem", "strong")])
        self.assertEqual(spell("20", "de", form=SpokenForm.ORDINAL, case="nominative", gender="neuter")[1].text,
                         "zwanzigstes")
        with self.assertRaises(ValueError):
            spell("3", "de", form=SpokenForm.ORDINAL, case="dative")


class TestValencian(unittest.TestCase):
    """AVL, Diccionari normatiu valencià: the main form of each entry."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "ca-ES-valencia", **kw)[0].text

    def test_cardinals(self):
        self.assertEqual([self.say(n) for n in ("8", "17", "18", "19", "80", "28")],
                         ["huit", "dèsset", "díhuit", "dènou", "huitanta", "vint-i-huit"])
        self.assertEqual([self.say(n, gender="feminine") for n in ("2", "200")], ["dos", "dos-centes"])

    def test_ordinals_end_in_e_acute(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("5", "8", "17", "18", "19")],
                         ["cinqué", "huité", "desseté", "dihuité", "denové"])
        self.assertEqual(self.say("17", form=SpokenForm.ORDINAL, gender="feminine"), "dessetena")

    def test_fractions(self):
        self.assertEqual([self.say(f) for f in ("1/5", "4/5", "2/3", "3/4")],
                         ["un quint", "quatre quints", "dos terços", "tres quarts"])

    def test_the_language_tag_reads_the_variety(self):
        self.assertEqual(spell("17", "ca_ES_valencia")[0].text, "dèsset")
        self.assertEqual(spell("17", "ca")[0].text, "disset")


class TestCatalan(unittest.TestCase):
    """IEC, GIEC §17.2 and OIEC §4.4.2.2."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "ca", **kw)[0].text

    def test_the_hyphen_joins_tens_and_units_and_units_and_hundreds_only(self):
        self.assertEqual([self.say(n) for n in ("22", "32", "102", "123", "200", "2000", "2100000")],
                         ["vint-i-dos", "trenta-dos", "cent dos", "cent vint-i-tres", "dos-cents", "dos mil",
                          "dos milions cent mil"])
        self.assertEqual([self.say(n, gender="feminine") for n in ("21", "200", "2000")],
                         ["vint-i-una", "dues-centes", "dues mil"])

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("1", "4", "10", "22", "102", "125", "200", "2000")],
                         ["primer", "quart", "desè", "vint-i-dosè", "cent dosè", "cent vint-i-cinquè", "dos-centè",
                          "dos milè"])
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL, gender="feminine") for n in ("1", "5", "21")],
                         ["primera", "cinquena", "vint-i-unena"])

    def test_fractions(self):
        self.assertEqual([self.say(f) for f in ("1/2", "1/3", "2/3", "1/4", "3/4", "2/5", "5/11")],
                         ["un mig", "un terç", "dos terços", "un quart", "tres quarts", "dos cinquens", "cinc onzens"])


class TestRomanian(unittest.TestCase):
    """DOOM 3 spellings, genders and ordinal headwords, as quoted by dexonline."""

    def say(self, value: str, **kw) -> str:
        return spell(value, "ro", **kw)[0].text

    def test_cardinals(self):
        self.assertEqual([self.say(n) for n in ("14", "16", "21", "60", "101", "2000", "20000", "120000", "2000000")],
                         ["paisprezece", "șaisprezece", "douăzeci și unu", "șaizeci", "o sută unu", "două mii",
                          "douăzeci de mii", "o sută douăzeci de mii", "două milioane"])

    def test_the_last_word_agrees_with_the_gender(self):
        self.assertEqual([self.say(n, gender="feminine") for n in ("1", "12", "22", "1002")],
                         ["una", "douăsprezece", "douăzeci și două", "o mie două"])
        self.assertEqual(self.say("2", gender="neuter"), "două")

    def test_ordinals(self):
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL) for n in ("1", "2", "11", "21", "100", "1000", "2000")],
                         ["primul", "al doilea", "al unsprezecelea", "al douăzeci și unulea", "al o sutălea",
                          "al mielea", "al două miilea"])
        self.assertEqual([self.say(n, form=SpokenForm.ORDINAL, gender="feminine") for n in ("2", "11", "20", "100", "1000")],
                         ["a doua", "a unsprezecea", "a douăzecea", "a suta", "a mia"])

    def test_fractions(self):
        self.assertEqual([self.say(f) for f in ("1/2", "3/2", "2/3", "3/4", "7/100", "20/3", "3/25")],
                         ["o jumătate", "trei jumătăți", "două treimi", "trei pătrimi", "șapte sutimi",
                          "douăzeci de treimi", "trei pe douăzeci și cinci"])


class TestPortugueseScales(unittest.TestCase):
    """pt-BR counts in the short scale (Priberam, "bilião", sense 2: "[Brasil] Mil milhões"), pt-PT in the long."""

    def test_the_short_scale_reads_brazilian_words(self):
        self.assertEqual(spell("1000000000", "pt-BR")[0].text, "um bilhão")
        self.assertEqual(spell("16", "pt-BR")[0].text, "dezesseis")
        self.assertEqual(spell("1000000000", "pt-PT")[0].text, "mil milhões")
        self.assertEqual(spell("1000000000", "pt-PT", scale="short")[0].text, "um bilião")

    def test_a_cardinal_past_the_scale_words_reads_the_exponent(self):
        # the -illions run with no gap to rank 20, "vigintilhão", 10^63 in the short scale
        self.assertEqual(spell("1" + "0" * 68, "pt-BR")[0].text, "cem mil vigintilhões")
        self.assertEqual(spell("1" + "0" * 100, "pt-BR")[0].text, "um vezes dez elevado a cem")
        self.assertEqual(spell("1" + "0" * 100, "pt-PT")[0].text, "dez mil sedeciliões")

    def test_an_ordinal_past_the_scale_words_raises(self):
        self.assertEqual(spell("1" + "0" * 30, "pt-BR", form="ordinal")[0].text, "nonilionésimo")
        with self.assertRaises(ValueError):
            spell("1" + "0" * 69, "pt-BR", form="ordinal")


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

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="the apostrophe that opens a rule text stays in the words "
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
            spell("1", "sv")
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

    def test_an_ordinal_above_the_maximum_of_the_form_raises(self):
        variants = Variants(self)
        data = _file("id")
        data["writer"]["forms"]["ordinal"]["maximum"] = "999"
        variants.write("id", data)
        self.assertEqual(spell("999", "id", form=SpokenForm.ORDINAL)[0].text, "kesembilan ratus sembilan puluh sembilan")
        with self.assertRaisesRegex(ValueError, "above 999"):
            spell("1000", "id", form=SpokenForm.ORDINAL)

    def test_decimals_as_one_number_keep_the_written_trailing_zeros(self):
        self.assertEqual([spell(v, "pt-PT", decimals="number", places=2)[0].text for v in ("1.80", "12.50", "100.10")],
                         ["um vírgula oitenta", "doze vírgula cinquenta", "cem vírgula dez"])
        self.assertEqual(spell("1.80", "pt-PT", decimals="digits")[0].text, "um vírgula oito")
        self.assertEqual([spell(v, "pt-PT", decimals="number", places=2)[0].text for v in ("5.0", "1.00", "0.00")],
                         ["cinco", "um", "zero"])

    def test_a_decimals_value_other_than_digits_or_number_raises(self):
        with self.assertRaisesRegex(ValueError, "'bogus'"):
            spell("2.5", "pt-PT", decimals="bogus")

    def test_a_counted_fraction_over_one_raises(self):
        for value in ("3/1", "1/1", "-2/1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                spell(value, "pt-PT")

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
    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="a named denominator drops the numerator also where it is more than 1 "
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
    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="-0/5 is written with a minus word although its value is zero "
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
