import json
import tomllib
import unittest
from fnmatch import fnmatch
from pathlib import Path

from numtag.lexicon import load

SLAVIC = ("ru", "uk", "bg", "pl", "cs", "sk", "sl", "hr")

ROOT = Path(__file__).parent.parent
LEXICONS = sorted((ROOT / "numtag" / "lexicon").glob("*.json"))
# The word for 10^6 in each language.
MILLION = {"en": "million", "pt-BR": "milhão", "pt-PT": "milhão", "ru": "миллион", "uk": "мільйон",
           "bg": "милион", "pl": "milion", "cs": "milión", "sk": "milión", "sl": "milijon", "hr": "milijun"}


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
                    self.assertEqual(lexicon.of(MILLION[path.stem], "scale_numeral" if path.stem in SLAVIC else "scale_noun")[0].exponent, 6)

    def test_pt_br_extends_pt_pt_with_the_short_scale(self):
        self.assertEqual(load("pt-BR").readings, load("pt-PT", "short").readings)
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

    def test_only_portuguese_takes_a_round_hundred_after_the_thousands_joiner(self):
        self.assertEqual({lang: load(lang).joiner_before_round_hundred for lang in ("en", "pt-BR", "pt-PT")},
                         {"en": False, "pt-BR": True, "pt-PT": True})

    def test_an_unknown_language_is_refused(self):
        with self.assertRaises(ValueError):
            load("xx")


if __name__ == "__main__":
    unittest.main()
