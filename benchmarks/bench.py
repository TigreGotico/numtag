"""Score and time one library on the numtag gold corpus.

usage: bench.py numtag|parser <gold_dir> <out.json>
Runs in its own process, so the memory numbers belong to one library.
"""
import json
import statistics
import sys
import time
import tracemalloc
from fractions import Fraction
from pathlib import Path

LANGS = ("pt-PT", "pt-BR", "en")


def rss_kib() -> int:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return -1


def same_value(gold: str, value) -> bool:
    g = Fraction(gold)
    if isinstance(value, str):
        return value == gold
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return Fraction(value) == g
    return abs(float(g) - value) <= 1e-9 * max(1.0, abs(float(g)))


lib, gold_dir, out = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
rows = {lang: [json.loads(l) for l in (gold_dir / f"{lang}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        for lang in LANGS}
report = {"lib": lib, "rss_kib_start": rss_kib()}

t0 = time.perf_counter()
if lib == "numtag":
    from numtag import tag_numbers

    def read(text, lang):
        return [(m.char_span[0], m.char_span[1], m.value) for m in tag_numbers(text, lang)]
else:
    import warnings
    warnings.simplefilter("ignore")
    from ovos_number_parser import extract_number_spans

    def read(text, lang):
        return [(s.start, s.end, s.value) for s in extract_number_spans(text, lang, ordinals=True)]
report["import_s"] = time.perf_counter() - t0
report["rss_kib_after_import"] = rss_kib()

# first call per language: lexicon or vocabulary load
tracemalloc.start()
first = {}
for lang in LANGS:
    t = time.perf_counter()
    read(rows[lang][0]["text"], lang)
    first[lang] = time.perf_counter() - t
report["first_call_s"] = first
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
report["tracemalloc_peak_first_calls_kib"] = peak // 1024

# accuracy: a row is right when the set of (start, end, value) equals the gold set;
# a low_confidence gold mention counts when it is reported at all
acc = {}
for lang in LANGS:
    right = mentions_gold = mentions_hit = predicted = 0
    for row in rows[lang]:
        pred = read(row["text"], lang)
        gold = row["mentions"]
        predicted += len(pred)
        mentions_gold += len(gold)
        hit = 0
        used = set()
        for g in gold:
            for k, (s, e, v) in enumerate(pred):
                if k not in used and s == g["start"] and e == g["end"] and same_value(g["value"], v):
                    used.add(k)
                    hit += 1
                    break
        mentions_hit += hit
        right += hit == len(gold) == len(pred)
    acc[lang] = {"rows": len(rows[lang]), "rows_right": right,
                 "gold_mentions": mentions_gold, "mentions_found": mentions_hit,
                 "predicted_mentions": predicted}
report["accuracy"] = acc

# latency: every gold sentence, 5 passes after the warm-up above
lat = {}
for lang in LANGS:
    times = []
    for _ in range(5):
        for row in rows[lang]:
            t = time.perf_counter()
            read(row["text"], lang)
            times.append(time.perf_counter() - t)
    times.sort()
    lat[lang] = {"calls": len(times), "median_ms": statistics.median(times) * 1e3,
                 "p95_ms": times[int(len(times) * 0.95)] * 1e3, "max_ms": times[-1] * 1e3}
report["latency_per_sentence"] = lat

short = {"pt-PT": "quanto é vinte e três mais quarenta e cinco", "pt-BR": "quanto é vinte e três mais quarenta e cinco",
         "en": "what is twenty three plus forty five"}
sh = {}
for lang, text in short.items():
    times = []
    for _ in range(200):
        t = time.perf_counter()
        read(text, lang)
        times.append(time.perf_counter() - t)
    sh[lang] = statistics.median(times) * 1e3
report["short_command_median_ms"] = sh

long_text = " ".join(r["text"] for r in rows["pt-PT"])
words = long_text.split()[:2000]
long_text = " ".join(words)
times = []
for _ in range(3):
    t = time.perf_counter()
    n = len(read(long_text, "pt-PT"))
    times.append(time.perf_counter() - t)
report["long_text_pt_2000_words"] = {"words": len(words), "best_s": min(times), "mentions": n}
report["rss_kib_end"] = rss_kib()
Path(out).write_text(json.dumps(report, indent=1), encoding="utf-8")
print(json.dumps(report, indent=1))
