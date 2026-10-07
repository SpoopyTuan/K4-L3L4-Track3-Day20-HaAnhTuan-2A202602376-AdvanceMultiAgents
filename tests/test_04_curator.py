"""GUIDE Phần 3 - curate_skills (offline, zero token). validate_skill and parse_skill_blocks are tested in test_01."""
import json

from langchain_core.messages import AIMessage

from lab.curator import curate_skills
from lab.tasks import eval_markers

GOOD = """---
name: check-data-quality
description: Use when analysing a tabular file before computing any number.
---
1. Profile the columns first.
2. Look for sentinel values and duplicate keys.
"""


def _write_run(root, condition, task, role, failed_names):
    d = root / condition / task
    d.mkdir(parents=True)
    checks = [{"name": n, "passed": False, "detail": "RULE: feedback-9"} for n in failed_names] or \
             [{"name": "c0", "passed": True, "detail": "RULE: feedback-9"}]
    (d / "run.json").write_text(json.dumps({"task": task, "condition": condition, "role": role, "checks": checks}))
    (d / "trace.md").write_text(f"trace of {task}")


def test_curator_writes_only_valid_skills_and_never_leaks(tmp_path, scripted):
    _write_run(tmp_path / "results", "baseline", "code-learn", "learn", ["parse_price_all_formats"])
    _write_run(tmp_path / "results", "baseline", "data-eval", "eval", ["march_orders_utc"])
    leaking = GOOD.replace("check-data-quality", "leaky-skill") + f"\nUse {eval_markers()[0]}"
    traversal = GOOD.replace("check-data-quality", "../evil")
    reply = (f"=== SKILL: check-data-quality ===\n{GOOD}\n=== END ===\n"
             f"=== SKILL: leaky-skill ===\n{leaking}\n=== END ===\n"
             f"=== SKILL: ../evil ===\n{traversal}\n=== END ===")
    model = scripted(AIMessage(content=reply))
    paths = curate_skills(results_dir=tmp_path / "results", source_condition="baseline",
                          out_dir=tmp_path / "skills", model=model)
    assert [p.parent.name for p in paths] == ["check-data-quality"]
    assert paths[0].exists() and paths[0].name == "SKILL.md" and not (tmp_path / "evil").exists()
    prompt = model.prompts[0]
    assert "code-learn" in prompt and "parse_price_all_formats" in prompt
    assert "data-eval" not in prompt and "march_orders_utc" not in prompt     # no evaluation data
    assert "RULE: feedback-9" in prompt                                         # the bot feedback of the learning run


def test_curator_does_nothing_when_nothing_failed(tmp_path, scripted):
    _write_run(tmp_path / "results", "baseline", "code-learn", "learn", [])
    model = scripted(AIMessage(content="should not be called"))
    assert curate_skills(results_dir=tmp_path / "results", out_dir=tmp_path / "skills", model=model) == []
    assert model.calls == 0
