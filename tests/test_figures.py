"""Each docs figure and the benchmark table match the committed result files.

The checks compare data, not SVG bytes, so they need no matplotlib.
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPTS = sorted(p for p in (ROOT / "docs" / "img").glob("plot_*.py") if p.name != "plot_style.py")


class TestFigures(unittest.TestCase):
    def test_every_figure_matches_its_data(self):
        self.assertEqual(len(SCRIPTS), 3)
        for script in SCRIPTS:
            with self.subTest(script=script.name):
                run = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True, cwd=ROOT)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
