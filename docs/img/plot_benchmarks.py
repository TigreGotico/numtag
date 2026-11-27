"""Draw the accuracy of numtag and ovos-number-parser from the reports of benchmarks/bench.py.

usage: python docs/img/plot_benchmarks.py [--check]
Reads benchmarks/numtag.json and benchmarks/parser.json.
--check compares docs/img/benchmarks.json and the accuracy table of docs/benchmarks.md
with a fresh read, and writes nothing.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from plot_style import save  # noqa: E402

STEM = HERE / "benchmarks"
PAGE = ROOT / "docs" / "benchmarks.md"
LIBS = ("numtag", "parser")


def data() -> dict:
    reports = {lib: json.loads((ROOT / "benchmarks" / f"{lib}.json").read_text(encoding="utf-8"))["accuracy"]
               for lib in LIBS}
    langs = list(reports["numtag"])
    return {"langs": langs, "accuracy": reports,
            "share": {lib: {lang: round(100 * reports[lib][lang]["rows_right"] / reports[lib][lang]["rows"], 1)
                            for lang in langs} for lib in LIBS}}


def table(data) -> list[str]:
    acc = data["accuracy"]
    return [f"| {lang} | {acc['numtag'][lang]['rows']} | {acc['numtag'][lang]['rows_right']} | "
            f"{acc['parser'][lang]['rows_right']} | {acc['numtag'][lang]['gold_mentions']} | "
            f"{acc['numtag'][lang]['mentions_found']} | {acc['parser'][lang]['mentions_found']} |"
            for lang in data["langs"]]


def alt(data) -> str:
    share = data["share"]
    langs = data["langs"]
    return " ".join(f"{lang}: numtag {share['numtag'][lang]} %, ovos-number-parser {share['parser'][lang]} %."
                    for lang in langs)


def draw(fig, theme, data):
    ax = fig.subplots()
    langs = data["langs"]
    height = 0.38
    for index, (lib, label) in enumerate((("numtag", "numtag"), ("parser", "ovos-number-parser"))):
        ys = [y + (index - 0.5) * height for y in range(len(langs))]
        values = [data["share"][lib][lang] for lang in langs]
        ax.barh(ys, values, height=height, color=theme["series"][index], label=label)
        for y, value in zip(ys, values):
            ax.text(value + 0.5, y, f"{value:.1f}", va="center", fontsize=8, color=theme["text"])
    ax.set_yticks(range(len(langs)), langs)
    ax.invert_yaxis()
    ax.set_xlim(0, 108)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Gold rows read right (%)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.set_title("Accuracy on the numtag gold corpus")


def main() -> int:
    fresh = data()
    if "--check" in sys.argv:
        stale = []
        if json.loads(STEM.with_suffix(".json").read_text(encoding="utf-8")) != fresh:
            stale.append("docs/img/benchmarks.json")
        page = PAGE.read_text(encoding="utf-8").splitlines()
        if any(row not in page for row in table(fresh)):
            stale.append("docs/benchmarks.md")
        for page in ("docs/benchmarks.md",):
            if f'alt="{alt(fresh)}"' not in (ROOT / page).read_text(encoding="utf-8"):
                stale.append(page)
        for path in stale:
            print(f"{path} differs from benchmarks/*.json: run python docs/img/plot_benchmarks.py")
        return int(bool(stale))
    save(str(STEM), draw, fresh, height=2.6)
    print("\n".join(table(fresh)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
