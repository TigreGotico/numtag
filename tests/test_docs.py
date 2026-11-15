"""Every example in README.md and docs/ runs and shows the output it gives.

A ```python block with ">>>" lines is a doctest session: each line after
">>>" runs, and the lines after it must equal the result. A ```python block
with no ">>>" line is a script: it runs, and the ```text block right after
it must equal what it prints. The blocks of one file share their names, in
file order. A ```json block parses, and a block that holds a lexicon entry,
setting or word list equals one in a lexicon file. Each quote in a block quote ("> ") of
docs/ is text from a source field of a lexicon or a gold file, so a quote in
the docs is never written from memory.
"""
import contextlib
import doctest
import io
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
FILES = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"))]
FENCE = re.compile(r"^```(\w*)\n(.*?)^```\n?", re.M | re.S)
QUOTE = re.compile(r'"([^"]+)"')
PARSER = doctest.DocTestParser()


def fenced(path: Path) -> list[tuple[int, str, str]]:
    """(line, language, body) of each fenced block, in file order."""
    text = path.read_text(encoding="utf-8")
    return [(text.count("\n", 0, m.start()) + 1, m.group(1), m.group(2)) for m in FENCE.finditer(text)]


def normalise(text: str) -> str:
    for mark in "“”„«»":
        text = text.replace(mark, '"')
    text = text.replace("–", "-").replace("—", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", text).casefold().strip()


def source_fields() -> list[str]:
    fields = []

    def walk(item):
        if isinstance(item, dict):
            fields.extend([item["source"]] if isinstance(item.get("source"), str) else [])
            for value in item.values():
                walk(value)
        elif isinstance(item, list):
            for value in item:
                walk(value)

    for path in sorted((ROOT / "numtag" / "lexicon").glob("*.json")):
        walk(json.loads(path.read_text(encoding="utf-8")))
    for path in sorted((ROOT / "tests" / "gold").glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                walk(json.loads(line))
    return fields


def lexicons() -> list[dict]:
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted((ROOT / "numtag" / "lexicon").glob("*.json"))]


def quotes(path: Path) -> list[str]:
    """Each quoted piece of at least four characters in the block quotes of
    ``path``, split at "[...]"."""
    text = FENCE.sub("", path.read_text(encoding="utf-8"))
    quoted = " ".join(line[1:].strip() for line in text.splitlines() if line.startswith(">"))
    pieces = []
    for match in QUOTE.finditer(quoted.replace("“", '"').replace("”", '"')):
        pieces += [p.strip(" ,;:.") for p in match.group(1).split("[...]")]
    return [p for p in pieces if len(p) >= 4]


class TestDocExamples(unittest.TestCase):
    def test_every_python_block_shows_its_output(self):
        examples = 0
        for path in FILES:
            blocks = fenced(path)
            names: dict = {}
            runner = doctest.DocTestRunner(optionflags=doctest.NORMALIZE_WHITESPACE)
            for index, (line, language, body) in enumerate(blocks):
                if language != "python":
                    continue
                where = f"{path.relative_to(ROOT)}:{line}"
                with self.subTest(block=where):
                    if ">>>" in body:
                        test = PARSER.get_doctest(body, names, where, str(path), line)
                        report = io.StringIO()
                        result = runner.run(test, out=report.write, clear_globs=False)
                        names.update(test.globs)
                        examples += result.attempted
                        self.assertEqual(result.failed, 0, report.getvalue())
                        continue
                    self.assertTrue(index + 1 < len(blocks) and blocks[index + 1][1] == "text",
                                    f"{where}: a script block needs a ```text block with its output")
                    printed = io.StringIO()
                    with contextlib.redirect_stdout(printed):
                        exec(compile(body, where, "exec"), names)
                    examples += 1
                    self.assertEqual(printed.getvalue().rstrip("\n"), blocks[index + 1][2].rstrip("\n"))
        self.assertGreater(examples, 0)

    def test_every_json_block_parses_and_lexicon_items_are_real(self):
        files = lexicons()
        entries = [entry for data in files for entry in data.get("entries", [])]
        items = [{key: item} for data in files for part in ("settings", "words")
                 for key, item in data.get(part, {}).items()]
        for path in FILES:
            for line, language, body in fenced(path):
                if language != "json":
                    continue
                with self.subTest(block=f"{path.relative_to(ROOT)}:{line}"):
                    data = json.loads(body)
                    if isinstance(data, dict) and {"word", "role"} <= data.keys():
                        self.assertIn(data, entries)
                    elif isinstance(data, dict) and len(data) == 1 and isinstance(
                            item := next(iter(data.values())), dict) and item.keys() == {"value", "source"}:
                        self.assertIn(data, items)

    def test_every_quote_comes_from_a_source_field(self):
        corpus = normalise("\n".join(source_fields()))
        for path in FILES[1:]:
            for piece in quotes(path):
                with self.subTest(file=path.name, quote=piece):
                    self.assertIn(normalise(piece), corpus)


if __name__ == "__main__":
    unittest.main()
