"""GUIDE Phần 1 - run_task (offline, zero token)."""
import json
from datetime import datetime

from langchain_core.messages import AIMessage

from lab.runner import CONDITIONS, run_task
from lab.testing import ScriptedChatModel

WRITE_PARTIAL = AIMessage(content="", tool_calls=[{
    "name": "write_file",
    "args": {"file_path": "workspace/answer.json", "content": json.dumps({"duplicate_rows_removed": 7})},
    "id": "1",
}])


def test_three_conditions_defined():
    assert set(CONDITIONS) == {"baseline", "subagents", "skills-auto"}


def test_run_task_saves_a_complete_record(tmp_path, scripted):
    rec = run_task("data-learn", "baseline", results_dir=tmp_path, model=scripted(WRITE_PARTIAL, AIMessage(content="done")))
    assert (rec["passed"], rec["total"]) == (1, 8)
    assert rec["tokens"]["total"] > 0 and rec["tool_calls"] == 1 and rec["subagent_calls"] == 0 and rec["skills_read"] == 0
    assert rec["role"] == "learn" and rec["error"] is None and rec["skills_modified"] is False
    assert len(rec["skills_sha256"]) == 64 and datetime.fromisoformat(rec["timestamp"])
    assert {"seconds", "final_message", "checks"} <= set(rec)
    out = tmp_path / "baseline" / "data-learn"
    saved = json.loads((out / "run.json").read_text(encoding="utf-8"))
    assert saved["passed"] == 1 and "write_file" in (out / "trace.md").read_text(encoding="utf-8")


def test_task_workspace_in_repo_is_never_modified(tmp_path, scripted):
    from lab.tasks import get_task
    run_task("data-learn", "baseline", results_dir=tmp_path, model=scripted(WRITE_PARTIAL, AIMessage(content="done")))
    assert not (get_task("data-learn").dir / "workspace" / "answer.json").exists()


def test_errors_are_recorded_not_raised(tmp_path):
    class Boom(ScriptedChatModel):
        def _generate(self, *a, **k):
            raise RuntimeError("api down")
    rec = run_task("data-learn", "baseline", results_dir=tmp_path, model=Boom(script=[AIMessage(content="x")]))
    assert "api down" in rec["error"] and rec["passed"] == 0


def test_modifying_skills_is_flagged(tmp_path, scripted):
    sneaky = AIMessage(content="", tool_calls=[{
        "name": "write_file",
        "args": {"file_path": "skills/sneaky/SKILL.md", "content": "---\nname: sneaky\ndescription: x\n---\n"},
        "id": "1",
    }])
    rec = run_task("data-learn", "baseline", results_dir=tmp_path, model=scripted(sneaky, AIMessage(content="done")))
    assert rec["skills_modified"] is True


def test_skill_reads_and_subagent_calls_are_counted(tmp_path, scripted):
    first = AIMessage(content="", tool_calls=[
        {"name": "read_file", "args": {"file_path": "skills/a/SKILL.md"}, "id": "1"},
        {"name": "read_file", "args": {"file_path": "/skills/b/SKILL.md"}, "id": "2"},
        {"name": "read_file", "args": {"file_path": "skills/a/SKILL.md"}, "id": "3"},
        {"name": "read_file", "args": {"file_path": "workspace/README.md"}, "id": "4"},
        {"name": "task", "args": {"description": "look around", "subagent_type": "general-purpose"}, "id": "5"},
    ])
    rec = run_task("data-learn", "baseline", results_dir=tmp_path,
                   model=scripted(first, AIMessage(content="subagent report"), AIMessage(content="done")))
    assert rec["skills_read"] == 2 and rec["subagent_calls"] == 1 and rec["tool_calls"] == 5     # a, b (a read twice)
