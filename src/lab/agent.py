"""GUIDE Phần 1 - Dựng tác tử (agent) bằng Deep Agents.   >>> SINH VIÊN CÀI ĐẶT make_backend VÀ build_agent <<<

Pseudo-code: guides/pseudocode/01_agent.md
Kiểm tra:    pytest tests/test_02_agent.py
"""

import os
import sys
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend

from .model import make_model
from .subagents import get_subagents

# ---- CÓ SẴN, KHÔNG SỬA: system prompt dùng chung cho mọi sinh viên (để đường cơ sở so sánh được) ----

PATHS_NOTE = (
    "PATHS: every path is relative to the sandbox root and never starts with '/'. "
    "The task files are in the folder workspace/ (for example workspace/app.log). "
    "Use exactly this relative form both in the file tools and in the shell (execute); "
    "the shell starts in the sandbox root. "
)
BASE_PROMPT = (
    "You are an engineering assistant working in a sandbox. "
    + PATHS_NOTE
    + "Use the shell to run Python and tests. "
    "When you are done, reply with a short summary that mentions only files you really created or changed."
)
SKILLS_NOTE = (
    " Skills are in the folder skills/ (one sub-folder per skill with a SKILL.md). "
    "As your FIRST action, read the SKILL.md of every skill whose description could apply to the task, "
    "then follow them. Never modify skills/."
)
SUBAGENTS_NOTE = (
    " You have specialised subagents (see the description of the task tool). "
    "For anything beyond a trivial step, delegate to a suitable subagent and put ALL the task rules and file paths "
    "in the delegation message, because a subagent sees only what you send. "
    "Check what a subagent returns before you rely on it."
)
# --------------------------------------------------------------------------------------------------


def make_backend(sandbox: Path):
    sandbox = Path(sandbox).resolve()
    env = {
        "PATH": os.pathsep.join((str(Path(sys.executable).parent), "/usr/local/bin", "/usr/bin", "/bin")),
        "HOME": str(sandbox),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    return LocalShellBackend(
        root_dir=sandbox, virtual_mode=True, inherit_env=False, env=env, timeout=120,
    )


def build_agent(sandbox: Path, mode: str = "single", use_skills: bool = False, model=None):
    if mode not in {"single", "subagents"}:
        raise ValueError(f"Unknown agent mode: {mode}")
    prompt = BASE_PROMPT
    kwargs = {}
    if mode == "subagents":
        kwargs["subagents"] = [
            {**sub, "system_prompt": sub["system_prompt"] + " " + PATHS_NOTE}
            for sub in get_subagents()
        ]
        prompt += SUBAGENTS_NOTE
    if use_skills:
        kwargs["skills"] = ["/skills/"]
        prompt += SKILLS_NOTE
    return create_deep_agent(
        model=make_model() if model is None else model,
        system_prompt=prompt,
        backend=make_backend(sandbox),
        **kwargs,
    )
