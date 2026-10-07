"""GUIDE Phần 1 - build_agent / make_backend / get_subagents (offline, zero token)."""
from langchain_core.messages import AIMessage

from lab.agent import BASE_PROMPT, PATHS_NOTE, build_agent, make_backend
from lab.subagents import get_subagents


def _run(agent, text="hello"):
    return agent.invoke({"messages": [{"role": "user", "content": text}]}, config={"recursion_limit": 30})


def test_backend_finds_python_and_hides_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_KEY", "super-secret-key-123")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "super-secret-key-123")
    out = make_backend(tmp_path).execute("which python && env").output
    assert "python" in out
    assert "super-secret-key-123" not in out


def test_file_tools_and_shell_share_relative_paths(tmp_path, scripted):
    (tmp_path / "workspace").mkdir()
    (tmp_path / "workspace" / "a.txt").write_text("hello-from-a\n")
    model = scripted(
        AIMessage(content="", tool_calls=[
            {"name": "write_file", "args": {"file_path": "workspace/new.txt", "content": "x"}, "id": "1"},
        ]),
        AIMessage(content="", tool_calls=[
            {"name": "execute", "args": {"command": "cat workspace/a.txt && ls workspace"}, "id": "2"},
        ]),
        AIMessage(content="done"),
    )
    out = _run(build_agent(tmp_path, model=model))
    shell_out = [str(m.content) for m in out["messages"] if m.type == "tool"][-1]
    assert "hello-from-a" in shell_out and "new.txt" in shell_out
    assert (tmp_path / "workspace" / "new.txt").read_text() == "x"


def test_agent_has_file_shell_and_task_tools(tmp_path, scripted):
    model = scripted(AIMessage(content="done"))
    _run(build_agent(tmp_path, mode="single", model=model))
    for name in ("read_file", "write_file", "edit_file", "execute", "task"):
        assert name in model.tool_names


def test_agent_uses_the_provided_base_prompt(tmp_path, scripted):
    model = scripted(AIMessage(content="done"))
    _run(build_agent(tmp_path, model=model))
    assert BASE_PROMPT in model.system_prompts[0]


def test_subagents_have_required_fields():
    subs = get_subagents()
    assert len(subs) >= 2
    for s in subs:
        assert s["name"] and s["description"] and s["system_prompt"]
    assert len({s["name"] for s in subs}) == len(subs)


def test_subagents_mode_adds_subagents_and_delegation_note(tmp_path, scripted):
    custom = scripted(AIMessage(content="done"))
    _run(build_agent(tmp_path, mode="subagents", model=custom))
    plain = scripted(AIMessage(content="done"))
    _run(build_agent(tmp_path, mode="single", model=plain))
    assert "specialised subagents" in custom.system_prompts[0]
    assert "specialised subagents" not in plain.system_prompts[0]
    assert get_subagents()[0]["name"] in custom.tool_descriptions["task"]


def test_skills_are_loaded_only_when_requested(tmp_path, scripted):
    skill = tmp_path / "skills" / "zzz-test-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: zzz-test-skill\ndescription: Only for tests.\n---\n# T\n", encoding="utf-8")
    with_skills = scripted(AIMessage(content="done"))
    _run(build_agent(tmp_path, use_skills=True, model=with_skills))
    assert "zzz-test-skill" in with_skills.system_prompts[0] and "FIRST action" in with_skills.system_prompts[0]
    without = scripted(AIMessage(content="done"))
    _run(build_agent(tmp_path, use_skills=False, model=without))
    assert "zzz-test-skill" not in without.system_prompts[0]


def test_unknown_mode_is_rejected(tmp_path, scripted):
    import pytest
    with pytest.raises(ValueError):
        build_agent(tmp_path, mode="swarm", model=scripted(AIMessage(content="x")))


def test_subagents_receive_the_path_convention(tmp_path, scripted):
    name = get_subagents()[0]["name"]
    model = scripted(
        AIMessage(content="", tool_calls=[{"name": "task", "args": {"description": "look", "subagent_type": name}, "id": "1"}]),
        AIMessage(content="subagent report"),
        AIMessage(content="done"),
    )
    _run(build_agent(tmp_path, mode="subagents", model=model))
    assert PATHS_NOTE in model.system_prompts[1]      # call 1 is the subagent's first call
