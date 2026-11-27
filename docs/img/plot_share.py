"""Draw the gold score ("Share") of each gold set from benchmarks/results.json.

usage: python docs/img/plot_share.py [--check]
--check compares docs/img/share.json with a fresh read and writes nothing.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "scripts"), str(ROOT)]
from plot_style import save  # noqa: E402
import language_table  # noqa: E402

STEM = HERE / "share"


def data() -> dict:
    from numtag.tagger import lexicon_name
    results = json.loads(language_table.RESULTS.read_text(encoding="utf-8"))
    leaders = {lexicon_name(tag) for tag in language_table.LEADERS}
    rows = [{"lang": lang, "rows": r["rows"], "rows_right": r["rows_right"],
             "share": round(100 * r["rows_right"] / r["rows"], 1), "leader": lang in leaders}
            for lang, r in results.items()]
    rows.sort(key=lambda row: (row["share"], row["rows"], row["lang"]))
    return {"rows": rows}


def alt(data) -> str:
    rows = data["rows"]
    full = sum(row["share"] == 100 for row in rows)
    low = ", ".join(f"{row['lang']} at {row['share']} %" for row in rows[:3])
    return f"{full} of {len(rows)} gold sets score 100 %. The lowest are {low}."


def draw(fig, theme, data):
    ax = fig.subplots()
    rows = data["rows"]
    colours = [theme["series"][1] if row["leader"] else theme["series"][0] for row in rows]
    ax.barh([row["lang"] for row in rows], [row["share"] for row in rows], color=colours)
    for index, row in enumerate(rows):
        ax.text(row["share"] + 0.05, index, f"{row['share']:.1f}", va="center", fontsize=7, color=theme["muted"])
    ax.set_xlim(95, 100.8)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Gold rows read right (%)")
    ax.set_title("Gold score per language (orange: leader languages)")


def main() -> int:
    fresh = data()
    if "--check" in sys.argv:
        stale = ["docs/img/share.json"] if json.loads(STEM.with_suffix(".json").read_text(encoding="utf-8")) != fresh else []
        stale += [page for page in ("docs/index.md", "docs/languages/index.md") if f'alt="{alt(fresh)}"' not in (ROOT / page).read_text(encoding="utf-8")]
        for path in stale:
            print(f"{path} differs from the data: run python docs/img/plot_share.py")
        return int(bool(stale))
    save(str(STEM), draw, fresh, height=9.5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
