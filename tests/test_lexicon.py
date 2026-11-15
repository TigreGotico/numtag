import json
import tomllib
import unittest
from fnmatch import fnmatch
from pathlib import Path

from numtag.lexicon import load
from numtag.tagger import lexicon_name

ROOT = Path(__file__).parent.parent
LEXICONS = sorted((ROOT / "numtag" / "lexicon").glob("*.json"))
MILLION = {"en": "million", "eu": "milioi", "fr": "million", "id": "juta", "it": "milione", "pt": "milhão",
           "ro": "milion"}


class TestLexiconFiles(unittest.TestCase):
    def test_every_language_is_there(self):
        self.assertEqual([p.stem for p in LEXICONS],
                         ["en", "eu", "fr-BE", "fr-CH", "fr-FR", "id", "it", "pt-BR", "pt-PT", "ro"])

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
            items += data.get("entries", [])
            with self.subTest(file=path.name):
                self.assertGreater(len(items), 0)
                self.assertEqual([i for i in items if not i.get("source", "").strip()], [])

    def test_every_lexicon_loads_in_both_scales(self):
        for path in LEXICONS:
            for scale in ("short", "long"):
                with self.subTest(file=path.name, scale=scale):
                    lexicon = load(path.stem, scale)
                    self.assertEqual(lexicon.scale.value, scale)
                    self.assertIn(MILLION[path.stem.split("-")[0]], lexicon.readings)

    def test_pt_br_extends_pt_pt_with_the_short_scale(self):
        self.assertEqual(load("pt-BR").readings, load("pt-PT", "short").readings)
        self.assertEqual(load("pt-BR").of("bilião", "scale_noun")[0].exponent, 9)
        self.assertEqual(load("pt-PT").of("bilião", "scale_noun")[0].exponent, 12)

    def test_the_round_hundred_after_the_thousands_joiner_is_per_language(self):
        langs = ("en", "eu", "fr-FR", "id", "it", "pt-BR", "pt-PT", "ro")
        self.assertEqual({lang: load(lang).joiner_before_round_hundred for lang in langs},
                         {"en": False, "eu": True, "fr-FR": False, "id": False, "it": True, "pt-BR": True,
                          "pt-PT": True, "ro": False})

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

    def test_a_region_without_a_file_reads_with_the_base_lexicon(self):
        self.assertEqual(lexicon_name("fr"), "fr-FR")
        self.assertEqual(lexicon_name("fr-CA"), "fr-FR")
        self.assertEqual(lexicon_name("fr_be"), "fr-BE")
        self.assertEqual(lexicon_name("fr-CH"), "fr-CH")
        self.assertEqual(lexicon_name("it-IT"), "it")
        self.assertEqual(lexicon_name("pt"), "pt-PT")

    def test_an_unknown_language_is_refused(self):
        with self.assertRaises(ValueError):
            load("xx")


if __name__ == "__main__":
    unittest.main()
