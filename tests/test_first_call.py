"""The first writer call in a fresh process stays fast."""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_first_spell_in_a_fresh_process_is_fast():
    code = "import time, numtag; t = time.perf_counter(); out = numtag.spell('21', 'pt-PT')[0].text; " \
           "print(out); print(time.perf_counter() - t)"
    done = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    spoken, seconds = done.stdout.splitlines()
    assert spoken == "vinte e um"
    assert float(seconds) < 2.0
