"""Sanity tests of the PROVIDED code. They must pass right after installation."""
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from lab.compare import build_table, load_runs
from lab.curator import parse_skill_blocks, validate_skill
from lab.grading import grade
from lab.runner import render_trace
from lab.tasks import eval_markers, get_task, hash_dir, hash_skills, list_tasks, prepare_sandbox


def test_six_tasks_three_families():
    tasks = list_tasks()
    assert [t.id for t in tasks] == ["code-eval", "code-learn", "data-eval", "data-learn", "logs-eval", "logs-learn"]
    assert {t.family for t in tasks} == {"code", "data", "logs"}
    assert len(list_tasks("learn")) == 3 and len(list_tasks("eval")) == 3


def test_untouched_workspace_does_not_score_full():
    for t in list_tasks():
        result = grade(t, t.dir / "workspace")
        assert result["total"] >= 5
        assert result["score"] < 1.0, t.id


def test_feedback_only_on_failed_checks_of_learning_tasks():
    learn = grade(get_task("data-learn"), get_task("data-learn").dir / "workspace")
    ev = grade(get_task("data-eval"), get_task("data-eval").dir / "workspace")
    assert any(not c["passed"] and c["detail"] for c in learn["checks"])
    assert all(c["detail"] == "" for c in learn["checks"] if c["passed"])
    assert all(c["detail"] == "" for c in ev["checks"]) and all(c["name"] for c in ev["checks"])


def test_instructions_use_relative_paths():
    for t in list_tasks():
        assert "workspace/" in t.instruction and "/workspace" not in t.instruction, t.id


def test_hash_dir_detects_changes(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "f.txt").write_text("x")
    before = hash_dir(tmp_path)
    assert len(before) == 64 and hash_dir(tmp_path / "missing") != before
    (tmp_path / "a" / "f.txt").write_text("y")
    assert hash_dir(tmp_path) != before


def test_eval_markers_are_computed_from_the_eval_tasks():
    markers = eval_markers()
    assert "data-eval" in markers and len(markers) >= 6
    assert not any(m in markers for m in ("readme", "tests"))
    assert "changelog" not in markers      # an Acme convention file that also exists in a learning workspace


def test_render_trace_hides_home_directory_and_shows_calls():
    text = render_trace([
        HumanMessage(content="go"),
        AIMessage(content="", tool_calls=[{"name": "execute", "args": {"command": f"ls {Path.home()}"}, "id": "1"}]),
        ToolMessage(content="done", tool_call_id="1"),
    ])
    assert "execute" in text and str(Path.home()) not in text


def test_compare_table_columns_cells_and_means():
    def run(task, cond, passed, tokens=1000, skills_read=0):
        return {"task": task, "condition": cond, "role": task.split("-")[1], "passed": passed, "total": 5,
                "score": passed / 5, "tokens": {"total": tokens}, "skills_read": skills_read}
    table = build_table([run("code-learn", "baseline", 1), run("code-eval", "baseline", 2),
                         run("code-learn", "skills-auto", 4, skills_read=1), run("code-eval", "skills-auto", 3, 3000)])
    assert "skills-auto" in table.splitlines()[0] and "subagents" not in table.splitlines()[0]
    assert "| code-eval | 2/5 | 3/5 |" in table
    assert table.index("code-learn") < table.index("code-eval")
    assert "0.20" in table and "0.80" in table and "0.40" in table and "0.60" in table
    assert "1,000" in table and "2,000" in table and "1/2" in table


def test_hash_skills_matches_the_hash_of_a_sandbox(tmp_path):
    skills = tmp_path / "skills-src"
    for name in ("alpha", "beta"):
        (skills / name).mkdir(parents=True)
        (skills / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: d\n---\n")
    (skills / "README.md").write_text("not a skill")
    (skills / "empty-folder").mkdir()
    sandbox = tmp_path / "sandbox"
    prepare_sandbox(get_task("data-learn"), sandbox, skills)
    assert hash_skills(skills) == hash_dir(sandbox / "skills")


GOOD_SKILL = """---
name: check-data-quality
description: Use when analysing a tabular file before computing any number.
---
1. Profile the columns first.
2. Look for sentinel values and duplicate keys.
"""


def test_validate_skill_accepts_good_and_rejects_bad():
    assert validate_skill(GOOD_SKILL) == []
    assert validate_skill(GOOD_SKILL, expected_name="check-data-quality") == []
    assert validate_skill("no frontmatter here")
    assert validate_skill(GOOD_SKILL.replace("check-data-quality", "Bad Name"))
    assert validate_skill(GOOD_SKILL, expected_name="another-name")
    assert validate_skill(GOOD_SKILL + f"\nSee {eval_markers()[0]} for an example.")
    assert validate_skill(GOOD_SKILL + "\n".join(["line"] * 100))
    assert validate_skill(GOOD_SKILL + "\nCreate CHANGELOG.md and tests/test_regressions.py.") == []   # Acme convention names are allowed


def test_parse_skill_blocks_survives_missing_end_markers():
    reply = (
        "Here are the skills:\n"
        "=== SKILL: one ===\n---\nname: one\ndescription: d\n---\nbody one\n"
        "=== SKILL: two ===\n---\nname: two\ndescription: d\n---\nbody two\n"
        "=== SKILL: three ===\n---\nname: three\ndescription: d\n---\nbody three\n=== END ===\nbye"
    )
    blocks = parse_skill_blocks(reply)
    assert [n for n, _ in blocks] == ["one", "two", "three"]
    assert all("=== SKILL" not in text and text.startswith("---") for _, text in blocks)
    assert "bye" not in blocks[-1][1]


def test_compare_ignores_renamed_backup_folders(tmp_path):
    import json
    for folder in ("skills-auto", "skills-auto-v1"):
        d = tmp_path / folder / "code-learn"
        d.mkdir(parents=True)
        (d / "run.json").write_text(json.dumps({"task": "code-learn", "condition": "skills-auto", "role": "learn",
                                                 "passed": 1 if folder.endswith("v1") else 9, "total": 10, "score": 0.5,
                                                 "tokens": {"total": 1}}))
    runs = load_runs(tmp_path)
    assert [r["passed"] for r in runs] == [9] and runs[0]["condition"] == "skills-auto"
