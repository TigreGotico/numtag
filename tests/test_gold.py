"""Scoreboard over the gold corpus in tests/gold/<lang>.jsonl.

A row scores when the tagger returns exactly its mentions, compared on
(start, end, value, kind, number_scale), where a missing "number_scale"
means None, and gives a confidence below 0.5 to each gold
mention marked "low_confidence". Each language's score must reach its floor
in tests/gold_floor.json. The rows each language misses are written to
tests/.gold-report/<lang>.txt, the work queue for the next fix.
"""
import json
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

from numtag import tag_numbers

HERE = Path(__file__).parent
GOLD = HERE / "gold"
FLOORS = HERE / "gold_floor.json"
REPORT = HERE / ".gold-report"


@dataclass
class Score:
    lang: str
    rows: int = 0
    correct: int = 0
    misses: list[str] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        return self.correct / self.rows if self.rows else 1.0


def row_matches(row: dict, lang: str) -> tuple[bool, list]:
    mentions = tag_numbers(row["text"], lang)
    got = [(m.char_span[0], m.char_span[1], m.value, m.kind.value,
            m.number_scale and m.number_scale.value) for m in mentions]
    expected = [(g["start"], g["end"], g["value"], g["kind"], g.get("number_scale"))
                for g in row["mentions"]]
    if got != expected:
        return False, got
    weak = all(m.confidence < 0.5 for m, g in zip(mentions, row["mentions"]) if g.get("low_confidence"))
    return weak, got


def score_file(path: Path) -> Score:
    score = Score(path.stem)
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        score.rows += 1
        ok, got = row_matches(row, score.lang)
        if ok:
            score.correct += 1
        else:
            score.misses.append(f"{path.name}:{number}\t{row['text']}\n"
                                f"  expected {row['mentions']}\n  got      {got}")
    return score


def scoreboard(files: list[Path]) -> list[Score]:
    scores = [score_file(path) for path in files]
    if scores:
        REPORT.mkdir(exist_ok=True)
    for score in scores:
        (REPORT / f"{score.lang}.txt").write_text("\n".join(score.misses) + "\n", encoding="utf-8")
    return scores


class TestGoldScoreboard(unittest.TestCase):
    def test_each_language_reaches_its_floor(self):
        files = sorted(GOLD.glob("*.jsonl"))
        floors = json.loads(FLOORS.read_text(encoding="utf-8"))
        if not files:
            print("\ngold scoreboard: no gold files in tests/gold")
            return
        scores = scoreboard(files)
        print(f"\ngold scoreboard ({len(files)} files)")
        for score in scores:
            print(f"  {score.lang:6} {score.correct:5}/{score.rows:<5} {score.ratio:.4f}"
                  f"  floor {floors.get(score.lang)}")
        self.assertEqual(sum(s.rows for s in scores),
                         sum(1 for f in files for line in f.read_text(encoding="utf-8").splitlines()
                             if line.strip()))
        for score in scores:
            with self.subTest(lang=score.lang):
                self.assertIn(score.lang, floors, f"no floor for {score.lang} in {FLOORS.name}")
                self.assertGreaterEqual(score.ratio, floors[score.lang])


class TestScoring(unittest.TestCase):
    """The scorer itself, on rows built here."""

    def test_an_exact_row_scores(self):
        row = {"text": "comprou duas dúzias", "mentions": [
            {"start": 8, "end": 19, "value": "24", "kind": "cardinal"}]}
        self.assertTrue(row_matches(row, "pt-PT")[0])

    def test_a_wrong_value_or_span_or_kind_does_not_score(self):
        for start, end, value, kind in ((8, 19, "12", "cardinal"), (8, 12, "24", "cardinal"),
                                        (8, 19, "24", "ordinal")):
            row = {"text": "comprou duas dúzias", "mentions": [
                {"start": start, "end": end, "value": value, "kind": kind}]}
            with self.subTest(row=row):
                self.assertFalse(row_matches(row, "pt-PT")[0])

    def test_number_scale_is_compared_and_missing_means_none(self):
        mention = {"start": 0, "end": 9, "value": "1" + "0" * 12, "kind": "cardinal"}
        self.assertTrue(row_matches({"text": "um bilião", "mentions": [
            {**mention, "number_scale": "long"}]}, "pt-PT")[0])
        for other in ({**mention, "number_scale": "short"}, mention):
            with self.subTest(mention=other):
                self.assertFalse(row_matches({"text": "um bilião", "mentions": [other]}, "pt-PT")[0])
        million = {"start": 0, "end": 9, "value": "1000000", "kind": "cardinal"}
        self.assertTrue(row_matches({"text": "um milhão", "mentions": [million]}, "pt-PT")[0])
        self.assertFalse(row_matches({"text": "um milhão", "mentions": [
            {**million, "number_scale": "long"}]}, "pt-PT")[0])

    def test_a_missing_or_extra_mention_does_not_score(self):
        self.assertFalse(row_matches({"text": "dois e três", "mentions": [
            {"start": 0, "end": 4, "value": "2", "kind": "cardinal"}]}, "pt-PT")[0])
        self.assertFalse(row_matches({"text": "olá", "mentions": [
            {"start": 0, "end": 3, "value": "1", "kind": "cardinal"}]}, "pt-PT")[0])
        self.assertTrue(row_matches({"text": "olá", "mentions": []}, "pt-PT")[0])

    def test_low_confidence_is_checked(self):
        weak = {"start": 8, "end": 11, "value": "1", "kind": "cardinal", "low_confidence": True}
        self.assertTrue(row_matches({"text": "comprei uma casa", "mentions": [weak]}, "pt-PT")[0])
        strong_row = {"text": "comprei uma dúzia", "mentions": [
            {"start": 8, "end": 17, "value": "12", "kind": "cardinal", "low_confidence": True}]}
        self.assertFalse(row_matches(strong_row, "pt-PT")[0])

    def test_a_file_is_scored_row_by_row(self):
        rows = [{"text": "comprou duas dúzias", "mentions": [
                    {"start": 8, "end": 19, "value": "24", "kind": "cardinal"}]},
                {"text": "dois e três", "mentions": []}]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "pt-PT.jsonl"
            path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n\n",
                            encoding="utf-8")
            score = score_file(path)
        self.assertEqual((score.lang, score.rows, score.correct, len(score.misses)), ("pt-PT", 2, 1, 1))
        self.assertEqual(score.ratio, 0.5)


if __name__ == "__main__":
    unittest.main()
