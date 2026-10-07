"""PROVIDED - do not edit. Builds the comparison table of GUIDE Phần 4.3.

    python -m lab.compare > report/table.md
"""
import argparse
import json
from pathlib import Path

ORDER = ["baseline", "subagents", "skills-auto"]


def load_runs(results_dir="results") -> list[dict]:
    """Read every <results_dir>/<condition>/<task>/run.json.

    The condition is the NAME OF THE DIRECTORY, and only the four known conditions are read, so a renamed
    backup folder such as results/skills-auto-dev is ignored.
    """
    runs = []
    for p in sorted(Path(results_dir).glob("*/*/run.json")):
        condition = p.parent.parent.name
        if condition in ORDER:
            runs.append({**json.loads(p.read_text(encoding="utf-8")), "condition": condition})
    return runs


def build_table(runs: list[dict]) -> str:
    """Markdown table: one column per condition, one row per task (learning tasks first, then evaluation tasks),
    then the mean score per role, the mean number of tokens per run and the share of runs that read a skill."""
    conditions = [c for c in ORDER if any(r["condition"] == c for r in runs)]
    tasks = sorted({r["task"] for r in runs}, key=lambda t: (t.split("-")[1] != "learn", t))
    cell = {(r["task"], r["condition"]): r for r in runs}
    lines = ["| Task | " + " | ".join(conditions) + " |", "|---|" + "---|" * len(conditions)]
    for t in tasks:
        row = [f"{cell[(t, c)]['passed']}/{cell[(t, c)]['total']}" if (t, c) in cell else "-" for c in conditions]
        lines.append(f"| {t} | " + " | ".join(row) + " |")
    for role, label in (("learn", "Mean score - learning tasks"), ("eval", "Mean score - evaluation tasks")):
        row = []
        for c in conditions:
            rs = [r for r in runs if r["condition"] == c and r["role"] == role]
            row.append(f"{sum(r['score'] for r in rs) / len(rs):.2f}" if rs else "-")
        lines.append(f"| **{label}** | " + " | ".join(row) + " |")
    row = []
    for c in conditions:
        rs = [r for r in runs if r["condition"] == c]
        row.append(f"{sum(r['tokens']['total'] for r in rs) // len(rs):,}" if rs else "-")
    lines.append("| **Mean tokens per run** | " + " | ".join(row) + " |")
    row = []
    for c in conditions:
        rs = [r for r in runs if r["condition"] == c]
        row.append(f"{sum(1 for r in rs if r.get('skills_read', 0) > 0)}/{len(rs)}" if rs else "-")
    lines.append("| **Runs that read a skill** | " + " | ".join(row) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    args = ap.parse_args()
    print(build_table(load_runs(args.results)))


if __name__ == "__main__":
    main()
