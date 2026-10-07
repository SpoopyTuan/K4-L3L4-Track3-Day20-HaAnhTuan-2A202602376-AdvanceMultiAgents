#!/usr/bin/env python3
"""PROVIDED. Tour of a DEFAULT Deep Agent - uses a fake model, so it costs ZERO token.

    python scripts/tour.py

It prints (1) the tools the model is offered, (2) the description of the `task` tool (how subagents are
described to the model) and (3) the system prompt (empty unless you provide one).
"""
import tempfile
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langchain_core.messages import AIMessage

from lab.testing import ScriptedChatModel

model = ScriptedChatModel(script=[AIMessage(content="ok")])
with tempfile.TemporaryDirectory() as tmp:
    agent = create_deep_agent(model=model, backend=LocalShellBackend(root_dir=Path(tmp), virtual_mode=True))
    agent.invoke({"messages": [{"role": "user", "content": "hello"}]})

print("=== TOOLS OFFERED TO THE MODEL (file tools: ls, read_file, write_file, edit_file, delete, glob, grep; shell: execute; subagents: task) ===")
for name in model.tool_names:
    print(" -", name)
print("\n=== DESCRIPTION OF THE `task` TOOL (subagents) ===")
print(model.tool_descriptions["task"])
print("\n=== DESCRIPTION OF THE `execute` TOOL (shell) ===")
print(model.tool_descriptions["execute"])
print("\n=== SYSTEM PROMPT (empty unless you pass system_prompt=...) ===")
print(repr(model.system_prompts[0][:300]))
