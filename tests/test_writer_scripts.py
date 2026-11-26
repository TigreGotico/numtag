"""The writer blocks and the allow-list entries are what their scripts write."""
import subprocess
import sys
import unittest
from pathlib import Path

import golden_writers

ROOT = Path(__file__).parent.parent


class TestWriterScripts(unittest.TestCase):
    def check(self, script: str, lang: str) -> None:
        run = subprocess.run([sys.executable, f"scripts/{script}", lang, "--check"], cwd=ROOT,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_the_portuguese_writer_blocks_are_what_the_script_writes(self):
        for lang in ("pt-PT", "pt-BR"):
            with self.subTest(lang=lang):
                self.check("writer_pt.py", lang)

    def test_the_spanish_writer_block_is_what_the_script_writes(self):
        self.check("writer_es.py", "--check")

    def test_the_italian_writer_block_is_what_the_script_writes(self):
        self.check("writer_it.py", "--check")

    def test_the_kabyle_writer_block_is_what_the_script_writes(self):
        self.check("writer_kab.py", "--check")

    def test_the_french_writer_blocks_are_what_the_script_writes(self):
        for variety in ("fr-FR", "fr-BE", "fr-CH"):
            with self.subTest(variety=variety):
                self.check("writer_fr.py", variety)

    def test_the_galician_writer_block_is_what_the_script_writes(self):
        self.check("writer_gl.py", "")
    def test_the_dutch_writer_block_is_what_the_script_writes(self):
        self.check("writer_nl.py", "")
    def test_the_norwegian_nynorsk_writer_block_is_what_the_script_writes(self):
        self.check("writer_nn.py", "")

    def test_the_bengali_writer_block_is_what_the_script_writes(self):
        self.check("writer_bn.py", "")

    def test_the_norwegian_bokmal_writer_block_is_what_the_script_writes(self):
        self.check("writer_nb.py", "")

    def test_the_danish_writer_block_is_what_the_script_writes(self):
        self.check("writer_da.py", "")

    def test_the_german_writer_block_is_what_the_script_writes(self):
        self.check("writer_de.py", "")

    def test_the_english_writer_block_is_what_the_script_writes(self):
        for variety in ("en", "en-US"):
            self.check("writer_en.py", variety)

    def test_the_catalan_writer_block_is_what_the_script_writes(self):
        for variety in ("ca", "ca-ES-valencia"):
            self.check("writer_ca.py", variety)

    def test_the_hindi_writer_block_is_what_the_script_writes(self):
        self.check("writer_hi.py", "")

    def test_the_romanian_writer_block_is_what_the_script_writes(self):
        self.check("writer_ro.py", "")

    def test_the_allow_list_entries_are_what_the_script_writes(self):
        langs = sorted({row["lang"] for row in golden_writers.stored() if golden_writers.has_writer(row["lang"])})
        self.assertTrue({"id", "ms", "pt-PT", "es", "nb"} <= set(langs))
        for lang in langs:
            with self.subTest(lang=lang):
                self.check("allow_list.py", lang)
