"""The lexicon format: version, schema, read-or-refuse and revision."""
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import jsonschema
import pytest

import numtag
from numtag import lexicon as lexicon_module
from numtag.lexicon import (DEFAULT_SETTINGS, DEFAULT_WORDS, ENTRY_KEYS, INFLECTION_KEYS, READABLE_VERSIONS,
                            REQUIRED_SETTINGS, REQUIRED_WORDS, SCALE_OF_KEYS, SETTINGS, TOP_KEYS, WORDS,
                            UnsupportedLanguageError, WRITER_VERSION, load)
from numtag import tagger as tagger_module
from numtag.tagger import lexicon_name

PACKAGE = Path(numtag.__file__).parent
ROOT = Path(__file__).parent.parent
LEXICONS = PACKAGE / "lexicon"
SCHEMA = json.loads((PACKAGE / "lexicon.schema.json").read_text(encoding="utf-8"))
NAMES = sorted(path.stem for path in LEXICONS.glob("*.json"))


def _file(name: str) -> dict:
    return json.loads((LEXICONS / f"{name}.json").read_text(encoding="utf-8"))


class Variants:
    """Lexicons written to a directory that the loader reads in place of the shipped one."""

    def __init__(self, test: unittest.TestCase):
        self._dir = tempfile.TemporaryDirectory()
        test.addCleanup(self._dir.cleanup)
        self.path = Path(self._dir.name)
        for name in NAMES:
            (self.path / f"{name}.json").symlink_to(LEXICONS / f"{name}.json")
        patch = mock.patch.object(lexicon_module, "_HERE", self.path)
        patch.start()
        test.addCleanup(patch.stop)
        self._names = mock.patch.object(tagger_module, "LEXICONS", tuple(NAMES))
        self._names.start()
        test.addCleanup(self._names.stop)
        test.addCleanup(tagger_module.lexicon_name.cache_clear)

    def write(self, name: str, data: dict) -> None:
        target = self.path / f"{name}.json"
        target.unlink(missing_ok=True)
        target.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tagger_module.LEXICONS = tuple(sorted({*tagger_module.LEXICONS, name}))
        tagger_module.lexicon_name.cache_clear()

    def load(self, name: str, data: dict, base: str):
        """The lexicon that ``data`` makes, named as ``base`` is, so that it compares with it."""
        self.write(name, data)
        return replace(load.__wrapped__(name), lang=base)


class TestSchema(unittest.TestCase):
    def test_the_schema_is_a_schema(self):
        jsonschema.Draft202012Validator.check_schema(SCHEMA)

    def test_every_lexicon_validates_against_the_schema(self):
        validator = jsonschema.Draft202012Validator(SCHEMA)
        self.assertEqual(len(NAMES), 52)
        for name in NAMES:
            with self.subTest(lexicon=name):
                self.assertEqual([e.message for e in validator.iter_errors(_file(name))], [])

    def test_the_schema_names_the_keys_that_the_loader_reads(self):
        top = SCHEMA["properties"]
        self.assertEqual(set(top), TOP_KEYS)
        self.assertEqual(set(top["settings"]["properties"]), SETTINGS)
        self.assertEqual(set(top["words"]["properties"]), WORDS)
        self.assertEqual(set(top["inflection"]["additionalProperties"]["properties"]), INFLECTION_KEYS)
        self.assertEqual(set(SCHEMA["else"]["properties"]["settings"]["required"]), REQUIRED_SETTINGS)
        self.assertEqual(set(SCHEMA["else"]["properties"]["words"]["required"]), REQUIRED_WORDS)
        self.assertEqual(top["format_version"], {"enum": list(READABLE_VERSIONS)})

    def test_the_schema_gives_the_default_that_the_loader_uses(self):
        for section, defaults in (("settings", DEFAULT_SETTINGS), ("words", DEFAULT_WORDS)):
            properties = SCHEMA["properties"][section]["properties"]
            for key, default in defaults.items():
                with self.subTest(key=key):
                    self.assertEqual(properties[key]["properties"]["value"]["default"], default)
            for key in set(properties) - set(defaults):
                with self.subTest(required=key):
                    self.assertNotIn("default", properties[key]["properties"]["value"])

    def test_the_schema_names_the_entry_keys_of_each_role(self):
        entry = SCHEMA["properties"]["entries"]["items"]
        self.assertEqual(set(entry["properties"]), set().union(*ENTRY_KEYS.values(), SCALE_OF_KEYS))
        by_role = {}
        for rule in entry["allOf"]:
            if "enum" in rule["if"]["properties"]["role"]:
                for role in rule["if"]["properties"]["role"]["enum"]:
                    by_role[role] = set(rule["then"]["propertyNames"]["enum"])
            else:
                scale_of, plain = rule["then"], rule["else"]["then"]
                by_role["denominator"] = set(plain["propertyNames"]["enum"])
                self.assertEqual(set(scale_of["propertyNames"]["enum"]), SCALE_OF_KEYS)
        self.assertEqual(by_role, {role: set(keys) for role, keys in ENTRY_KEYS.items()})
        self.assertEqual(set(entry["properties"]["role"]["enum"]), set(ENTRY_KEYS))

    def test_the_schema_refuses_what_the_loader_refuses(self):
        validator = jsonschema.Draft202012Validator(SCHEMA)
        bad = _file("fi")
        bad["entries"] = [{"word": "x", "role": "unit", "value": "1", "rank": 3, "source": "s"}]
        self.assertTrue(list(validator.iter_errors(bad)))
        bad = _file("fi")
        bad["format_version"] = 3
        self.assertTrue(list(validator.iter_errors(bad)))
        bad = _file("fi")
        bad["writer"] = _file("id")["writer"]
        self.assertTrue(list(validator.iter_errors(bad)))
        bad = _file("fi")
        del bad["settings"]["scale"]
        self.assertTrue(list(validator.iter_errors(bad)))


class TestSpecPage(unittest.TestCase):
    def test_the_spec_page_names_every_key_and_every_role(self):
        page = (ROOT / "docs" / "lexicon-format.md").read_text(encoding="utf-8")
        entry = SCHEMA["properties"]["entries"]["items"]["properties"]
        for key in sorted(TOP_KEYS | SETTINGS | WORDS | INFLECTION_KEYS | set(entry) | set(ENTRY_KEYS)):
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", page)


class TestVersion(unittest.TestCase):
    def test_every_lexicon_names_the_version(self):
        for name in NAMES:
            with self.subTest(lexicon=name):
                data = _file(name)
                self.assertEqual(data["format_version"], WRITER_VERSION if "writer" in data else 1)

    def test_a_lexicon_with_an_unknown_version_is_refused_by_name(self):
        variants = Variants(self)
        for version in (3, 0, "1", None):
            data = _file("en")
            data["format_version"] = version
            variants.write("variant", data)
            with self.subTest(version=version), self.assertRaisesRegex(
                    ValueError, rf"variant: format_version {version!r} is unknown"):
                load.__wrapped__("variant")

    def test_a_lexicon_with_no_version_is_refused_by_name(self):
        variants = Variants(self)
        data = _file("en")
        del data["format_version"]
        variants.write("variant", data)
        with self.assertRaisesRegex(ValueError, "variant: format_version None is unknown"):
            load.__wrapped__("variant")

    def test_a_base_lexicon_with_an_unknown_version_is_refused_by_name(self):
        variants = Variants(self)
        base = _file("pt-PT")
        base["format_version"] = 3
        variants.write("base", base)
        variants.write("variant", {**_file("pt-BR"), "extends": "base"})
        with self.assertRaisesRegex(ValueError, "base: format_version 3 is unknown"):
            load.__wrapped__("variant")


class TestUnknownKeys(unittest.TestCase):
    def refused(self, variants: Variants, data: dict, where: str) -> None:
        variants.write("variant", data)
        with self.assertRaisesRegex(ValueError, rf"variant: unknown key 'bogus' in {where}"):
            load.__wrapped__("variant")

    def test_an_unknown_key_is_refused_by_name_at_every_level(self):
        variants = Variants(self)

        def edit(name, change):
            data = _file(name)
            change(data)
            return data

        self.refused(variants, edit("en", lambda d: d.update(bogus=1)), "the lexicon")
        self.refused(variants, edit("en", lambda d: d["settings"].update(bogus={"value": 1, "source": "s"})),
                     "settings")
        self.refused(variants, edit("en", lambda d: d["words"].update(bogus={"value": [], "source": "s"})), "words")
        self.refused(variants, edit("en", lambda d: d["settings"]["scale"].update(bogus=1)), "settings 'scale'")
        self.refused(variants, edit("en", lambda d: d["words"]["joiner"].update(bogus=1)), "words 'joiner'")
        self.refused(variants, edit("fi", lambda d: next(iter(d["inflection"].values())).update(bogus=1)),
                     "inflection")
        self.refused(variants, edit("ar", lambda d: d["settings"]["native_digits"]["value"].update(bogus=1)),
                     "setting 'native_digits'")
        self.refused(variants, edit("pt-BR", lambda d: d["settings"].update(bogus={"value": 1, "source": "s"})),
                     "settings")

    def test_an_unknown_entry_key_is_refused_for_every_role(self):
        variants = Variants(self)
        entries = {}
        for name in NAMES:
            for entry in _file(name).get("entries", ()):
                if "scale_of" not in entry:
                    entries.setdefault(entry["role"], (name, entry))
        self.assertEqual(set(entries), set(ENTRY_KEYS))
        for role, (name, entry) in entries.items():
            data = _file(name)
            data["entries"] = [{**entry, "bogus": 1}]
            with self.subTest(role=role):
                variants.write("variant", data)
                with self.assertRaisesRegex(ValueError, rf"unknown key 'bogus' in entry {entry['word']!r} of role"):
                    load.__wrapped__("variant")

    def test_a_key_of_another_role_is_refused(self):
        variants = Variants(self)
        for role, key in (("unit", "rank"), ("half", "value"), ("ordinal_suffix", "plural"),
                          ("vague_quantifier", "gender"), ("ten", "scale_of")):
            entry = next(e for e in _file("en")["entries"] if e["role"] == role) if role != "vague_quantifier" \
                else next(e for e in _file("hr")["entries"] if e["role"] == role)
            data = _file("en" if role != "vague_quantifier" else "hr")
            data["entries"] = [{**entry, key: "1"}]
            with self.subTest(role=role, key=key):
                variants.write("variant", data)
                with self.assertRaisesRegex(ValueError, rf"unknown key {key!r} in entry"):
                    load.__wrapped__("variant")

    def test_a_denominator_that_names_a_scale_word_reads_no_value(self):
        variants = Variants(self)
        data = _file("en")
        entry = next(e for e in data["entries"] if "scale_of" in e)
        data["entries"] = [{**entry, "value": "5"}]
        variants.write("variant", data)
        with self.assertRaisesRegex(ValueError, "unknown key 'value' in entry"):
            load.__wrapped__("variant")


# A key that no reading depends on: it cites the source of its value.
NO_EFFECT = {"source": "the source of a rule is read by people and by tests/test_lexicon.py"}

# Lexicons that give each key a place to act, in the order tried.
CANDIDATES = ("en", "fi", "ar", "tr", "hu", "fr-FR", "ro", "de", "pt-PT", "fa", "el", "sr", "lt", "hr")


def _different(spec: dict, current):
    """A value of the same shape as ``current`` that ``spec`` allows and that differs from it."""
    if "enum" in spec:
        return next(item for item in spec["enum"] if item != current)
    kind = spec["type"]
    if isinstance(kind, list):
        return None if current else {"digits": ["٠١٢٣٤٥٦٧٨٩"], "decimal_mark": "٫", "group_mark": "٬"}
    if kind == "boolean":
        return not current
    if kind == "integer":
        return (current or 0) + 1
    if kind == "string":
        return (current or "") + "x"
    if kind == "array":
        return [] if current else ["zz"]
    if kind == "object":
        return {k: v for k, v in current.items() if k != next(iter(current))} if current else {"q": "w"}
    raise AssertionError(kind)


def _value_spec(section: str, key: str) -> dict:
    return SCHEMA["properties"][section]["properties"][key]["properties"]["value"]


class TestReadOrRefuse(unittest.TestCase):
    """Each key set away from its default in a copy of a lexicon changes the loaded Lexicon."""

    def changes(self, variants: Variants, edits) -> bool:
        """True when some candidate lexicon, edited by ``edits(data)``, loads as another Lexicon."""
        for name in CANDIDATES:
            data = _file(name)
            if edits(data) is False:
                continue
            if variants.load("variant", data, name) != replace(load.__wrapped__(name), lang=name):
                return True
        return False

    def test_every_setting_changes_the_lexicon(self):
        variants = Variants(self)
        for key in sorted(SETTINGS):
            if key in NO_EFFECT:
                continue

            def edit(data, key=key):
                item = data["settings"].setdefault(key, {"source": "test"})
                item["value"] = _different(_value_spec("settings", key), item.get("value", DEFAULT_SETTINGS.get(key)))

            with self.subTest(setting=key):
                self.assertTrue(self.changes(variants, edit))

    def test_every_word_list_changes_the_lexicon(self):
        variants = Variants(self)
        for key in sorted(WORDS):
            def edit(data, key=key):
                item = data["words"].setdefault(key, {"source": "test"})
                item["value"] = _different(_value_spec("words", key), item.get("value", []))

            with self.subTest(words=key):
                self.assertTrue(self.changes(variants, edit))

    def test_every_inflection_key_changes_the_lexicon(self):
        variants = Variants(self)
        properties = SCHEMA["properties"]["inflection"]["additionalProperties"]["properties"]
        for key in sorted(INFLECTION_KEYS - {"source"}):
            def edit(data, key=key):
                if "inflection" not in data:
                    return False
                for item in data["inflection"].values():
                    item[key] = _different(properties[key], item.get(key, False))

            with self.subTest(inflection=key):
                self.assertTrue(self.changes(variants, edit))

    def test_every_entry_key_changes_the_lexicon(self):
        variants = Variants(self)
        properties = SCHEMA["properties"]["entries"]["items"]["properties"]
        for key in sorted(set(properties) - set(NO_EFFECT)):
            roles = [role for role, keys in ENTRY_KEYS.items() if key in keys]
            if key == "scale_of":
                roles = ["denominator"]
            elif key == "role":
                roles = ["unit", "ten"]

            def edit(data, key=key, roles=roles):
                # Entries that hold the key come first, so that its value moves away from the data's.
                held = [e for e in data["entries"] if e["role"] in roles and key in e]
                free = [e for e in data["entries"] if e["role"] in roles and key not in e
                        and ("scale_of" in e) == (key == "scale_of")]
                if not held and not free or key == "stems" and "inflection" not in data:
                    return False
                for entry in (held or free)[:1]:
                    spec = properties[key]
                    if key == "stems":
                        entry[key] = {"zz": [next(iter(data["inflection"]))]}
                    elif key == "scale_of":
                        entry[key] = "trillion" if entry.get(key) == "billion" else "billion"
                    elif key == "role":
                        entry[key] = "ten" if entry["role"] == "unit" else "unit"
                    elif key == "gender":
                        entry[key] = next(g for g in spec["enum"] if g != entry.get(key))
                    elif key in ("value", "rank") and isinstance(entry.get(key), int):
                        entry[key] = entry[key] + 1
                    elif key == "value":
                        entry[key] += "1"
                    elif key in ("ambiguous_forms", "excluded_forms", "weak_forms") and key not in entry:
                        entry[key] = [entry["word"]]
                    else:
                        entry[key] = _different(spec, entry.get(key))

            with self.subTest(entry=key):
                self.assertTrue(self.changes(variants, edit))

    def test_every_key_that_has_no_effect_says_so(self):
        every = set(SETTINGS) | set(WORDS) | INFLECTION_KEYS | set(SCHEMA["properties"]["entries"]["items"]["properties"])
        self.assertLessEqual(set(NO_EFFECT), every)


class TestRevision(unittest.TestCase):
    @staticmethod
    def sha256(data: dict) -> str:
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def test_a_revision_is_the_sha256_of_the_canonical_bytes_of_the_file(self):
        for name in NAMES:
            data = _file(name)
            if "extends" not in data:
                with self.subTest(lexicon=name):
                    self.assertEqual(numtag.revision(name), self.sha256(data))

    def test_the_revision_of_a_lexicon_with_a_base_covers_the_base(self):
        base, derived = _file("pt-PT"), _file("pt-BR")
        merged = {"format_version": base["format_version"],
                  "settings": {**base["settings"], **derived["settings"]},
                  "words": {**base["words"], **derived.get("words", {})},
                  "inflection": {},
                  "entries": base["entries"],
                  "writer": derived["writer"]}
        self.assertEqual(numtag.revision("pt-BR"), self.sha256(merged))

    def test_every_lexicon_has_its_own_revision(self):
        revisions = {numtag.revision(name) for name in NAMES}
        self.assertEqual(len(revisions), len(NAMES))
        self.assertTrue(all(len(r) == 64 and set(r) <= set("0123456789abcdef") for r in revisions))

    def test_a_language_tag_reads_the_revision_of_its_lexicon(self):
        self.assertEqual(numtag.revision("pt"), numtag.revision("pt-PT"))
        self.assertEqual(numtag.revision("pt_br"), numtag.revision("pt-BR"))
        self.assertEqual(numtag.revision("no"), numtag.revision("nb"))
        self.assertEqual(numtag.revision("de-AT"), numtag.revision("de"))

    def test_a_changed_setting_or_word_changes_the_revision(self):
        variants = Variants(self)
        data = _file("en")
        variants.write("variant", data)
        before = lexicon_module.revision.__wrapped__("variant")
        data["settings"]["decimal_mark"]["value"] = "x"
        variants.write("variant", data)
        self.assertNotEqual(lexicon_module.revision.__wrapped__("variant"), before)

    def test_a_changed_base_changes_the_revision_of_the_lexicon_that_extends_it(self):
        variants = Variants(self)
        variants.write("base", _file("pt-PT"))
        variants.write("variant", {**_file("pt-BR"), "extends": "base"})
        before = lexicon_module.revision.__wrapped__("variant")
        base = _file("pt-PT")
        base["settings"]["decimal_mark"]["value"] = "x"
        variants.write("base", base)
        self.assertNotEqual(lexicon_module.revision.__wrapped__("variant"), before)

    def test_an_unknown_language_has_no_revision(self):
        with self.assertRaises(UnsupportedLanguageError):
            numtag.revision("xx")


class TestLanguageTags(unittest.TestCase):
    def test_a_bare_tag_reads_the_default_region_of_its_language(self):
        for tag, name in [("pt", "pt-PT"), ("fr", "fr-FR"), ("no", "nb")]:
            with self.subTest(tag=tag):
                self.assertEqual(lexicon_name(tag), name)

    def test_every_lexicon_is_read_by_its_name_in_every_spelling(self):
        for name in NAMES:
            for spelling in (name, name.upper(), name.replace("-", "_"), name.lower().replace("-", "_")):
                with self.subTest(spelling=spelling):
                    self.assertEqual(lexicon_name(spelling), name)

    def test_a_code_that_names_a_language_another_way_reads_its_lexicon(self):
        for tag, name in [("deu", "de"), ("eng", "en"), ("fra", "fr-FR"), ("por", "pt-PT"), ("spa", "es"),
                          ("iw", "he"), ("in", "id"), ("nob", "nb"), ("nno", "nn"), ("nor", "nb"), ("zlm", "ms"),
                          ("pt-Latn-BR", "pt-BR")]:
            with self.subTest(tag=tag):
                self.assertEqual(lexicon_name(tag), name)
                self.assertEqual(numtag.revision(tag), numtag.revision(name))

    def test_a_language_that_linguatag_places_near_a_lexicon_reads_it(self):
        for tag, name in [("bs", "hr"), ("gsw", "de"), ("hbs", "sr"), ("sh", "sr"), ("arz", "ar"), ("ars", "ar"),
                          ("arb", "ar"), ("ajp", "ar"), ("azj", "az"), ("ekk", "et"), ("pes", "fa")]:
            with self.subTest(tag=tag):
                self.assertEqual(lexicon_name(tag), name)

    def test_an_unknown_region_and_a_trailing_separator_read_the_language(self):
        for tag in ("pt-ZZ", "PT_zz", "pt-BR-", "pt_BR_", "pt-BR--"):
            with self.subTest(tag=tag):
                self.assertEqual(lexicon_name(tag), "pt-PT")

    def test_a_script_before_the_region_reads_the_region(self):
        for tag in ("pt-Latn-BR", "pt_Latn_BR", "pt-Latn_BR"):
            with self.subTest(tag=tag):
                self.assertEqual(lexicon_name(tag), "pt-BR")

    def test_a_region_without_a_lexicon_reads_the_language(self):
        for tag, name in [("de-AT", "de"), ("fr-CA", "fr-FR"), ("pt-AO", "pt-PT"), ("en-AU", "en"), ("ar-EG", "ar")]:
            with self.subTest(tag=tag):
                self.assertEqual(lexicon_name(tag), name)

    def test_a_padded_bare_tag_reads_the_default_region(self):
        self.assertEqual(lexicon_name(" pt "), "pt-PT")

    def test_a_padded_region_tag_reads_its_region(self):
        for tag in (" pt-BR", "pt-BR "):
            self.assertEqual(lexicon_name(tag), "pt-BR")

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/291")
    def test_bosnian_reads_a_thousand_of_hiljada(self):
        self.assertEqual([(m.text, m.value) for m in numtag.tag_numbers("dvije hiljade i petsto", "bs")],
                         [("dvije hiljade i petsto", "2500")])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/291")
    def test_swiss_german_reads_its_twenty(self):
        self.assertEqual([(m.text, m.value) for m in numtag.tag_numbers("zwänzg", "gsw")], [("zwänzg", "20")])

    @pytest.mark.xfail(strict=True, raises=AssertionError, reason="https://github.com/TigreGotico/numtag/issues/291")
    def test_egyptian_arabic_reads_its_twenty_two(self):
        self.assertEqual([(m.text, m.value) for m in numtag.tag_numbers("اتنين وعشرين", "arz")],
                         [("اتنين وعشرين", "22")])

    def test_a_language_without_a_lexicon_is_refused_in_every_spelling(self):
        for tag in ("xx", "XX_US", "", " "):
            with self.subTest(tag=tag), self.assertRaises(UnsupportedLanguageError):
                numtag.tag_numbers("21", tag)
