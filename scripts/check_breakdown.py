#!/usr/bin/env python3
"""PROVIDED. Splits the checks of every run into TECHNICAL checks and HOUSE-RULE checks (to help the report).

    python scripts/check_breakdown.py

For each condition it prints, for learning and evaluation tasks, how many technical checks and how many
house-rule checks passed, the mean tokens and the number of runs that read a skill. A check is a house rule
when its name starts with `rule_` or is one of the code conventions (type hints, regression tests, changelog).
Evaluation rows are printed only after the git tag `freeze` exists (the protocol forbids looking earlier).
"""
import json
import subprocess
from collections import defaultdict
from pathlib import Path

from lab.compare import ORDER
from lab.tasks import ROOT

HOUSE = ("rule_",)


def is_rule(name: str) -> bool:
    return name.startswith(HOUSE)


def frozen() -> bool:
    return subprocess.run(["git", "rev-parse", "-q", "--verify", "refs/tags/freeze"], cwd=ROOT,
                          capture_output=True).returncode == 0


def main() -> None:
    show_eval = frozen()
    stats = defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0])   # tech_pass, tech_total, rule_pass, rule_total, tokens, skills_read, runs
    for condition in ORDER:
        for f in sorted((ROOT / "results" / condition).glob("*/run.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            if r["role"] == "eval" and not show_eval:
                continue
            s = stats[(condition, r["role"])]
            for c in r["checks"]:
                k = 2 if is_rule(c["name"]) else 0
                s[k] += c["passed"]
                s[k + 1] += 1
            s[4] += r["tokens"]["total"]
            s[5] += 1 if r.get("skills_read", 0) > 0 else 0
            s[6] += 1
    print(f"{'condition':13s} {'role':6s} {'technical':>10s} {'house rules':>12s} {'mean tokens':>12s} {'read a skill':>13s}")
    for (condition, role), s in sorted(stats.items(), key=lambda kv: (ORDER.index(kv[0][0]), kv[0][1])):
        print(f"{condition:13s} {role:6s} {s[0]:>4d}/{s[1]:<5d} {s[2]:>6d}/{s[3]:<5d} {s[4] // s[6]:>12,} {s[5]:>6d}/{s[6]:<6d}")
    if not show_eval:
        print("(evaluation rows are hidden until the git tag `freeze` exists)")


if __name__ == "__main__":
    main()
