#!/usr/bin/env python3
"""Automated checks for task `code-eval`.

Usage: python check.py --workspace PATH
Prints one JSON object: {"score": float, "passed": int, "total": int, "checks": [...]}
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

TEST_FILE_HASHES = {"test_bookings.py": "9d29eae4addb49567d119969e137738241074ba0c3e1a674b0a3f0a2fde71031"}
PACKAGE = "bookings"


def sha_dir(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts and ".pytest_cache" not in f.parts and f.suffix != ".pyc":
            h.update(str(f.relative_to(path)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def _public_functions(pkg: Path):
    import ast
    for path in sorted(pkg.glob("*.py")):
        if path.name == "__init__.py":
            continue
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                yield path.name, node


def check_rule_type_hints(ws: Path):
    bad = []
    for fname, node in _public_functions(ws / PACKAGE):
        a = node.args
        params = [*a.posonlyargs, *a.args, *a.kwonlyargs] + [x for x in (a.vararg, a.kwarg) if x]
        if node.returns is None or any(p.annotation is None for p in params):
            bad.append(f"{fname}:{node.name}")
    return not bad, ("RULE: every public function (name not starting with '_') in the package has type annotations on all "
                     "parameters and on the return value.")


def check_rule_regression_tests(ws: Path):
    import subprocess
    import sys
    path = ws / "tests" / "test_regressions.py"
    if not path.exists():
        return False, RULE_REGRESSION
    n_tests = len(re.findall(r"^def test_\w+", path.read_text(encoding="utf-8"), re.M))
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_regressions.py", "-q", "-p", "no:cacheprovider"],
                       cwd=ws, capture_output=True, text=True, timeout=120)
    return n_tests >= 3 and r.returncode == 0, RULE_REGRESSION


def check_rule_changelog(ws: Path):
    path = ws / "CHANGELOG.md"
    if not path.exists():
        return False, RULE_CHANGELOG
    text = path.read_text(encoding="utf-8")
    section = text.split("## Unreleased", 1)[1].split("\n## ", 1)[0] if "## Unreleased" in text else ""
    bullets = re.findall(r"^- fix\([A-Za-z_]\w*\): \S.+$", section, re.M)
    return len(bullets) >= 3, RULE_CHANGELOG


RULE_REGRESSION = "RULE: add tests/test_regressions.py with one test function per bug you fixed (at least 3); the file must pass."
RULE_CHANGELOG = ("RULE: record each fix in CHANGELOG.md under the heading '## Unreleased' as a bullet "
                  "'- fix(<function name>): <short description>' (at least 3 bullets).")


def check_rule_version_bump(ws: Path):
    text = (ws / "bookings" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    return bool(m) and m.group(1) == "1.4.3", "RULE: increment the patch number of __version__ once per fix session."


def _safe(fn):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return f"<{type(exc).__name__}>"


def check_visible_suite(ws: Path):
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"],
        cwd=ws, capture_output=True, text=True, timeout=120,
    )
    return r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]


def check_tests_unchanged(ws: Path):
    import hashlib
    bad = [name for name, h in TEST_FILE_HASHES.items()
           if not (ws / "tests" / name).exists() or hashlib.sha256((ws / "tests" / name).read_bytes()).hexdigest() != h]
    return not bad, "the original files in tests/ must not be modified (new test files are allowed)"


def check_parse_duration(ws: Path):
    from bookings.timeutil import parse_duration
    cases = {"1h30m": 90, "2h": 120, "45m": 45, "1:30": 90, "45": 45, " 1h05m ": 65, "0:05": 5}
    bad = [k for k, v in cases.items() if _safe(lambda: parse_duration(k)) != v]
    return not bad, f"wrong for: {bad}" if bad else "all formats parsed"


def check_other_caller(ws: Path):
    from bookings.calendar_export import slot_end
    got = [_safe(lambda: slot_end(600, "1:30")), _safe(lambda: slot_end(600, "2h"))]
    return got == [690, 720], f"slot_end returned {got}"


def check_billable_blocks(ws: Path):
    from bookings.billing import billable_blocks
    cases = {0: 0, 1: 1, 15: 1, 16: 2, 20: 2, 30: 2, 31: 3}
    bad = [k for k, v in cases.items() if _safe(lambda: billable_blocks(k)) != v]
    return not bad, f"wrong for minutes={bad}" if bad else "rounds up correctly"


def check_negative_rejected(ws: Path):
    from bookings.billing import billable_blocks
    try:
        billable_blocks(-5)
    except ValueError:
        return True, "ValueError raised"
    except Exception as exc:  # noqa: BLE001
        return False, f"raised {type(exc).__name__} instead of ValueError"
    return False, "no exception for negative minutes"


def check_no_shared_state(ws: Path):
    from bookings.schedule import add_slot
    first = add_slot("a")
    second = add_slot("b")
    third = add_slot("c", ["x"])
    ok = first == ["a"] and second == ["b"] and third == ["x", "c"]
    return ok, f"got {first}, {second}, {third}"


CHECKS = [
    ("visible_suite_passes", check_visible_suite),
    ("tests_not_modified", check_tests_unchanged),
    ("parse_duration_all_formats", check_parse_duration),
    ("other_caller_fixed", check_other_caller),
    ("billable_blocks_round_up", check_billable_blocks),
    ("add_slot_no_shared_state", check_no_shared_state),
    ("negative_minutes_rejected", check_negative_rejected),
    ("rule_type_hints", check_rule_type_hints),
    ("rule_regression_tests", check_rule_regression_tests),
    ("rule_changelog", check_rule_changelog),
    ("rule_version_bump", check_rule_version_bump),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ws = Path(ap.parse_args().workspace).resolve()
    sys.path.insert(0, str(ws))
    results = []
    for name, fn in CHECKS:
        try:
            ok, detail = fn(ws)
        except Exception as exc:  # noqa: BLE001
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        results.append({"name": name, "passed": bool(ok), "detail": str(detail)})
    passed = sum(r["passed"] for r in results)
    print(json.dumps({"score": passed / len(results), "passed": passed, "total": len(results), "checks": results}))


if __name__ == "__main__":
    main()
