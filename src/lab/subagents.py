"""GUIDE Phần 1 - Định nghĩa subagent (tác tử con).   >>> SINH VIÊN CÀI ĐẶT <<<

Pseudo-code: guides/pseudocode/02_subagents.md
Kiểm tra:    pytest tests/test_02_agent.py
"""


def get_subagents() -> list[dict]:
    return [
        {
            "name": "explorer",
            "description": "Delegate when requirements, files, or data need investigation before implementation.",
            "system_prompt": "Read the supplied requirements and relevant files. Do not modify files. Report findings, paths, constraints, and recommended next steps concisely.",
        },
        {
            "name": "reviewer",
            "description": "Delegate when completed changes need independent checks against requirements and edge cases.",
            "system_prompt": "Check the supplied requirements against the resulting files. Run relevant tests when needed. Do not modify files. Report concrete failures and supporting evidence, or confirm the checks passed.",
        },
    ]
