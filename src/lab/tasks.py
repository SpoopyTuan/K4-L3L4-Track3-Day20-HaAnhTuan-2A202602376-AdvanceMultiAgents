"""PROVIDED - do not edit. Task discovery and sandbox preparation."""
import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.getenv("LAB_ROOT", Path(__file__).resolve().parents[2]))
TASKS_DIR = ROOT / "tasks"


@dataclass(frozen=True)
class Task:
    id: str          # for example "code-learn"
    family: str      # "code", "data" or "logs"
    role: str        # "learn" (learning task) or "eval" (evaluation task)
    instruction: str
    dir: Path


def get_task(task_id: str) -> Task:
    d = TASKS_DIR / task_id
    if not (d / "instruction.md").exists():
        raise KeyError(f"unknown task: {task_id}")
    family, role = task_id.split("-", 1)
    return Task(task_id, family, role, (d / "instruction.md").read_text(encoding="utf-8"), d)


def list_tasks(role: str | None = None) -> list[Task]:
    tasks = [get_task(p.name) for p in sorted(TASKS_DIR.iterdir()) if (p / "instruction.md").exists()]
    return [t for t in tasks if role is None or t.role == role]


def prepare_sandbox(task: Task, sandbox: Path, skills_dir: Path | None = None) -> None:
    """Create `sandbox/workspace` (copy of the task workspace) and, optionally, `sandbox/skills`.

    `skills_dir` contains one sub-folder per skill (each with a SKILL.md); they are copied
    to `sandbox/skills/<skill-name>/`.
    """
    sandbox.mkdir(parents=True, exist_ok=True)
    shutil.copytree(task.dir / "workspace", sandbox / "workspace", dirs_exist_ok=True)
    if skills_dir is not None and skills_dir.exists():
        for skill in sorted(p for p in skills_dir.iterdir() if (p / "SKILL.md").exists()):
            shutil.copytree(skill, sandbox / "skills" / skill.name, dirs_exist_ok=True)


def hash_dir(path: Path) -> str:
    """SHA-256 over the relative names and bytes of every file under `path` (empty digest if it does not exist).

    Used to detect that the skills folder was modified during a run, and recorded in run.json
    (`skills_sha256`) so that a grader can compare it with the folder frozen by the `freeze` tag.
    """
    h = hashlib.sha256()
    path = Path(path)
    if path.exists():
        for f in sorted(path.rglob("*")):
            if f.is_file():
                h.update(str(f.relative_to(path)).encode())
                h.update(f.read_bytes())
    return h.hexdigest()


def hash_skills(skills_dir: Path) -> str:
    """Hash of the skills that `prepare_sandbox` would copy from `skills_dir` (sub-folders having a SKILL.md).

    Equals `hash_dir(sandbox/"skills")` of a run, so it can be compared with `skills_sha256` in run.json.
    """
    h = hashlib.sha256()
    skills_dir = Path(skills_dir)
    files = []
    if skills_dir.exists():
        for skill in (p for p in skills_dir.iterdir() if (p / "SKILL.md").exists()):
            files += [f for f in skill.rglob("*") if f.is_file()]
    for f in sorted(files):
        h.update(str(f.relative_to(skills_dir)).encode())
        h.update(f.read_bytes())
    return h.hexdigest()


_GENERIC = {"readme.md", "__init__.py", "tests", "__pycache__", "workspace"}


def eval_markers() -> list[str]:
    """Lower-case identifiers that belong ONLY to the evaluation tasks (their ids and the names of their files).

    Computed at run time from `tasks/`, so no evaluation name is hard-coded in the source. Names that also
    exist in a learning workspace (for example CHANGELOG.md, an Acme convention file) are not markers.
    A skill that contains one of these strings leaks evaluation material.
    """
    def names(role):
        found = set()
        for t in list_tasks(role):
            for p in (t.dir / "workspace").iterdir():
                if p.name.lower() not in _GENERIC and not p.name.startswith("."):
                    found.update({p.name.lower(), p.stem.lower()})
        return found

    markers = {t.id for t in list_tasks("eval")} | (names("eval") - names("learn"))
    return sorted(m for m in markers if len(m) >= 4)
