"""docs/languages/index.md and benchmarks/results.json match what scripts/language_table.py writes."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "language_table.py"
sys.path.insert(0, str(ROOT / "scripts"))
import language_table  # noqa: E402


class TestLanguageTable(unittest.TestCase):
    def test_page_matches_lexicons_and_results(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "--check"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_results_match_a_fresh_gold_run(self):
        committed = json.loads(language_table.RESULTS.read_text(encoding="utf-8"))
        self.assertEqual(language_table.measure(), committed,
                         "run python scripts/language_table.py --measure")

    def test_leader_rows(self):
        page = language_table.PAGE.read_text(encoding="utf-8")
        results = json.loads(language_table.RESULTS.read_text(encoding="utf-8"))

        def score(lang: str) -> str:
            rows, right = results[lang]["rows"], results[lang]["rows_right"]
            return f"| {rows} | {right} | {100 * right / rows:.1f}%"

        self.assertIn(f"| `mwr` | yes | yes | yes | yes {score('mwr')}[^mwr] |", page)
        self.assertIn("| `es-CO` (resolves to `es`) |", page)
        self.assertIn(f"| `pt-PT` | yes | yes | yes | yes {score('pt-PT')} |", page)
        self.assertIn(f"The score of `bn` rests on {results['bn']['rows']} rows.", page)

if __name__ == "__main__":
    unittest.main()
