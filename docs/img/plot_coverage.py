"""Draw what each lexicon reads and writes, from numtag/lexicon/*.json.

usage: python docs/img/plot_coverage.py [--check]
--check compares docs/img/coverage.json with a fresh read and writes nothing.
The features are the columns of docs/languages/index.md, from scripts/language_table.py.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT / "scripts")]
from plot_style import save  # noqa: E402
import language_table  # noqa: E402

STEM = HERE / "coverage"
FEATURES = ["cardinals", "ordinals", "fractions", "writer"]


def data() -> dict:
    rows = []
    for path in sorted(language_table.LEXICONS.glob("*.json")):
        found = language_table.roles(path.stem)
        has = {"cardinals": "unit" in found,
               "ordinals": bool(found & language_table.ORDINAL_ROLES),
               "fractions": bool(found & language_table.FRACTION_ROLES),
               "writer": "writer" in json.loads(path.read_text(encoding="utf-8"))}
        rows.append({"lang": path.stem, **has})
    totals = {feature: sum(row[feature] for row in rows) for feature in FEATURES}
    return {"features": FEATURES, "lexicons": len(rows), "totals": totals, "rows": rows}


def alt(data) -> str:
    n, totals = data["lexicons"], data["totals"]
    return (f"Of {n} lexicons, {totals['cardinals']} read cardinals, {totals['ordinals']} read ordinals, "
            f"{totals['fractions']} read fractions and {totals['writer']} have a writer.")


def draw(fig, theme, data):
    ax = fig.subplots()
    features, rows = data["features"], data["rows"]
    for y, feature in enumerate(features):
        xs = [x for x, row in enumerate(rows) if row[feature]]
        ax.scatter(xs, [y] * len(xs), marker="s", s=60, color=theme["series"][0])
        missing = [x for x, row in enumerate(rows) if not row[feature]]
        ax.scatter(missing, [y] * len(missing), marker="s", s=60, facecolor="none", edgecolor=theme["muted"])
    ax.set_yticks(range(len(features)),
                  [f"{f} ({data['totals'][f]}/{data['lexicons']})" for f in features])
    ax.set_xticks(range(len(rows)), [row["lang"] for row in rows], rotation=90, fontsize=7)
    ax.set_xlim(-1, len(rows))
    ax.set_ylim(len(features) - 0.5, -0.5)
    ax.grid(False)
    ax.set_title("What each lexicon reads and writes (filled: yes)")


def main() -> int:
    fresh = data()
    if "--check" in sys.argv:
        stale = ["docs/img/coverage.json"] if json.loads(STEM.with_suffix(".json").read_text(encoding="utf-8")) != fresh else []
        stale += [page for page in ("docs/languages/index.md",) if f'alt="{alt(fresh)}"' not in (ROOT / page).read_text(encoding="utf-8")]
        for path in stale:
            print(f"{path} differs from the data: run python docs/img/plot_coverage.py")
        return int(bool(stale))
    save(str(STEM), draw, fresh, width=9.0, height=2.6)
    return 0


if __name__ == "__main__":
    sys.exit(main())
