import json
import re
import tomllib
import unittest
from copy import deepcopy
from unittest import mock
from fnmatch import fnmatch
from pathlib import Path

from numtag import lexicon as lexicon_module, tag_numbers
from numtag.lexicon import Joiner, load
from numtag.tagger import lexicon_name

SLAVIC = ("ru", "uk", "bg", "pl", "cs", "sk", "sl", "hr")

ROOT = Path(__file__).parent.parent
LEXICONS = sorted((ROOT / "numtag" / "lexicon").glob("*.json"))
#: each language's word for a million
MILLION = {"en": "million", "pt-BR": "milhão", "pt-PT": "milhão", "de": "million", "nl": "miljoen",
           "fy": "miljoen", "da": "million", "sv": "miljon", "nb": "million", "nn": "million",
           "fi": "miljoona", "et": "miljon", "hu": "millió", "tr": "milyon", "az": "milyon",
           "ar": "مليون", "el": "εκατομμύριο", "fa": "میلیون", "he": "מיליון", "kab": "amelyun",
           "ru": "миллион", "uk": "мільйон", "bg": "милион", "pl": "milion", "cs": "milión", "sk": "milión",
           "sl": "milijon", "hr": "milijun", "eu": "milioi", "fr-BE": "million", "fr-CH": "million",
           "fr-FR": "million", "id": "juta", "it": "milione", "ro": "milion",
           "es": "millón", "gl": "millón", "ca": "milió", "ast": "millón", "an": "millón",
           "oc": "milion", "mwl": "milhon"}


class TestLexiconFiles(unittest.TestCase):
    def test_every_language_is_there(self):
        self.assertEqual([p.stem for p in LEXICONS], sorted(MILLION))

    def test_package_data_ships_every_lexicon(self):
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        patterns = pyproject["tool"]["setuptools"]["package-data"]["numtag"]
        for path in LEXICONS:
            relative = path.relative_to(ROOT / "numtag").as_posix()
            with self.subTest(file=relative):
                self.assertTrue(any(fnmatch(relative, p) for p in patterns), patterns)

    def test_every_rule_names_its_source(self):
        for path in LEXICONS:
            data = json.loads(path.read_text(encoding="utf-8"))
            items = list(data.get("settings", {}).values()) + list(data.get("words", {}).values())
            items += data.get("entries", []) + list(data.get("inflection", {}).values())
            with self.subTest(file=path.name):
                self.assertGreater(len(items), 0)
                self.assertEqual([i for i in items if not i.get("source", "").strip()], [])

    def test_every_source_quotes_a_page_or_says_it_is_structural(self):
        # A quote is a double-quoted run of two words or more; a bare term or a digit mark is no quote.
        def quotes(source):
            return [q for q in re.findall(r'"([^"]*)"', source) if " " in q.strip() and len(q) >= 4]

        sources = []
        for lang in ("en", "pt-BR", "pt-PT"):
            data = json.loads((ROOT / "numtag" / "lexicon" / f"{lang}.json").read_text(encoding="utf-8"))
            items = list(data.get("settings", {}).values()) + list(data.get("words", {}).values())
            sources += [(lang, i["source"]) for i in items + data.get("entries", [])]
            gold = (ROOT / "tests" / "gold" / f"{lang}.jsonl").read_text(encoding="utf-8")
            sources += [(f"gold {lang}", json.loads(line)["source"]) for line in gold.splitlines()]
        unquoted = sorted({(name, s) for name, s in sources
                           if not quotes(s) and "no external source" not in s.lower()})
        self.assertEqual(unquoted, [])

    def test_every_lexicon_loads_in_both_scales(self):
        for path in LEXICONS:
            for scale in ("short", "long"):
                with self.subTest(file=path.name, scale=scale):
                    lexicon = load(path.stem, scale)
                    self.assertEqual(lexicon.scale.value, scale)
                    self.assertIn(lexicon.script.fold(MILLION[path.stem]), lexicon.readings)

    def test_pt_br_extends_pt_pt_with_the_short_scale(self):
        self.assertEqual(load("pt-BR").readings, load("pt-PT", "short").readings)
        # pt-BR adds one digit word: "meia" is 6 in a spoken digit sequence
        self.assertEqual([(w, e.role, e.value) for w, es in load("pt-BR").digit_words.items() for e in es],
                         [("meia", "digit_alias", "6")])
        self.assertEqual(load("pt-PT").digit_words, {})
        self.assertEqual(load("pt-BR").of("bilião", "scale_noun")[0].exponent, 9)
        self.assertEqual(load("pt-PT").of("bilião", "scale_noun")[0].exponent, 12)

    def test_slavic_scales(self):
        # Russian "миллиард" is 10^9 in both scales; "триллион" counts the short scale.
        self.assertEqual(load("ru").of("миллиард", "scale_numeral")[0].exponent, 9)
        self.assertFalse(load("ru").of("миллиард", "scale_numeral")[0].scale_dependent)
        self.assertEqual(load("ru").of("триллион", "scale_numeral")[0].exponent, 12)
        # Polish "bilion" is 10^12 in the long scale.
        self.assertEqual(load("pl").of("bilion", "scale_numeral")[0].exponent, 12)
        self.assertTrue(load("pl").of("bilion", "scale_numeral")[0].scale_dependent)

    def test_ukrainian_apostrophes_are_one_letter(self):
        lexicon = load("uk")
        self.assertIn("п'ять", lexicon.readings)
        self.assertEqual(lexicon.word_apostrophes, frozenset({"'", "\u2019"}))

    def test_the_round_hundred_after_the_thousands_joiner_is_per_language(self):
        langs = ("az", "en", "et", "eu", "fi", "fr-FR", "hu", "id", "it", "pt-BR", "pt-PT", "ro", "tr")
        self.assertEqual({lang: load(lang).joiner_before_round_hundred for lang in langs},
                         {"az": False, "en": False, "et": False, "eu": True, "fi": False, "fr-FR": False,
                          "hu": False, "id": False, "it": True, "pt-BR": True, "pt-PT": True, "ro": False,
                          "tr": False})
    def test_fr_be_extends_fr_fr_with_septante_and_nonante(self):
        base, belgian = load("fr-FR").readings, load("fr-BE").readings
        self.assertLessEqual(base.keys(), belgian.keys())
        self.assertEqual(set(belgian) - set(base),
                         {"septante", "septantième", "septantièmes", "nonante", "nonantième", "nonantièmes"})
        self.assertEqual(load("fr-BE").of("septante", "ten")[0].value, "70")

    def test_fr_ch_extends_fr_be_with_huitante(self):
        belgian, swiss = load("fr-BE").readings, load("fr-CH").readings
        self.assertEqual(set(swiss) - set(belgian), {"huitante", "huitantième", "huitantièmes"})
        self.assertEqual(load("fr-CH").of("huitante", "ten")[0].value, "80")

    def test_a_vague_quantifier_of_several_words_keeps_its_words_and_its_flag(self):
        data = deepcopy(lexicon_module._read("hr"))
        data["entries"] += [{"word": "jako puno", "role": "vague_quantifier", "source": "test entry"},
                            {"word": "Više", "role": "vague_quantifier", "ambiguous": True, "source": "test entry"}]
        with mock.patch.object(lexicon_module, "_read", lambda lang: data), \
                mock.patch.object(lexicon_module, "exists", lambda lang: True):
            phrases = lexicon_module.load("hr-test").vague_quantifiers
            lexicon_module.load.cache_clear()
        self.assertEqual(phrases[("jako", "puno")], False)
        self.assertEqual(phrases[("više",)], True)
        self.assertNotIn(("jako puno",), phrases)

    def test_a_multi_word_vague_quantifier_reads_before_a_scale_word(self):
        data = deepcopy(lexicon_module._read("hr"))
        data["entries"] = [e for e in data["entries"] if e["role"] != "vague_quantifier"] + [
            {"word": "jako puno", "role": "vague_quantifier", "source": "test entry"}]
        with mock.patch.object(lexicon_module, "_read", lambda lang: data), \
                mock.patch.object(lexicon_module, "exists", lambda lang: True):
            lexicon_module.load.cache_clear()
            vague = [(m.text, m.value) for m in tag_numbers("jako puno tisuća", "hr")]
            alone = [(m.text, m.value) for m in tag_numbers("puno tisuća", "hr")]
            lexicon_module.load.cache_clear()
        self.assertEqual(vague, [])
        self.assertEqual(alone, [("tisuća", "1000")])

    def test_a_comma_between_classes_does_not_carry_a_vague_quantity(self):
        # where a comma may link two classes of one number, the guard still stops at it
        data = deepcopy(lexicon_module._read("hr"))
        data["settings"]["comma_between_classes"] = {"value": True, "source": "test setting"}
        with mock.patch.object(lexicon_module, "_read", lambda lang: data):
            lexicon_module.load.cache_clear()
            read = [(m.text, m.value) for m in tag_numbers("nekoliko milijuna, tisuću ljudi", "hr")]
            lexicon_module.load.cache_clear()
        self.assertEqual(read, [("tisuću", "1000")])

    def test_a_region_without_a_file_reads_with_the_base_lexicon(self):
        self.assertEqual(lexicon_name("fr"), "fr-FR")
        self.assertEqual(lexicon_name("fr-CA"), "fr-FR")
        self.assertEqual(lexicon_name("fr_be"), "fr-BE")
        self.assertEqual(lexicon_name("fr-CH"), "fr-CH")
        self.assertEqual(lexicon_name("it-IT"), "it")
        self.assertEqual(lexicon_name("pt"), "pt-PT")

    def test_only_portuguese_requires_the_joiner_before_a_last_round_group(self):
        self.assertEqual({lang: load(lang).joiner_before_last_group for lang in ("en", "pt-BR", "pt-PT")},
                         {"en": Joiner.OPTIONAL, "pt-BR": Joiner.REQUIRED, "pt-PT": Joiner.REQUIRED})

    def test_portuguese_and_english_take_a_comma_between_classes(self):
        self.assertEqual({lang: load(lang).comma_between_classes for lang in ("en", "pt-BR", "pt-PT")},
                         {"en": True, "pt-BR": True, "pt-PT": True})

    def test_an_unknown_language_is_refused(self):
        with self.assertRaises(ValueError):
            load("xx")


if __name__ == "__main__":
    unittest.main()
