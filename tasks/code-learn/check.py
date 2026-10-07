#!/usr/bin/env python3
"""Automated checks for task `code-learn`.

Usage: python check.py --workspace PATH
Prints one JSON object: {"score": float, "passed": int, "total": int, "checks": [...]}
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

TEST_FILE_HASHES = {"test_report.py": "79e05f4cc2e62a4f606d210b0b08a2cc21777245bc2f6ad244a126e9a2aee00d"}
PACKAGE = "inventory"


def sha_dir(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file() and "__pycache__" not in f.parts and ".pytest_cache" not in f.parts and f.suffix != ".pyc":
            h.update(str(f.relative_to(path)).encode())
            h.update(f.read_bytes())
    return h.hexdigest()


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


def check_parse_price(ws: Path):
    from inventory.pricing import parse_price
    cases = {
        "$1,299.50": Decimal("1299.50"),
        "  12 ": Decimal("12"),
        "1299.5": Decimal("1299.5"),
        "(12.00)": Decimal("-12.00"),
        "$1,000,000.00": Decimal("1000000.00"),
    }
    bad = [k for k, v in cases.items() if _safe(lambda: parse_price(k)) != v]
    return not bad, f"wrong for: {bad}" if bad else "all formats parsed"


def check_other_caller(ws: Path):
    from inventory.export import to_csv_row
    got = _safe(lambda: to_csv_row({"name": "tv", "price": "$1,299.50", "qty": 1}))
    return got == "tv,1299.50,1", f"to_csv_row returned {got!r}"


def check_discount_half_up(ws: Path):
    from inventory.pricing import apply_discount
    cases = [("10.05", 10, "9.05"), ("19.99", 15, "16.99"), ("0.05", 50, "0.03"), ("2.665", 0, "2.67")]
    bad = [c for c in cases if _safe(lambda: apply_discount(Decimal(c[0]), c[1])) != Decimal(c[2])]
    return not bad, f"wrong for: {bad}" if bad else "half-up rounding correct"


def check_low_stock(ws: Path):
    from inventory.report import low_stock
    items = [{"name": "b", "qty": 5}, {"name": "A", "qty": 4}, {"name": "c", "qty": 1}, {"name": "d", "qty": 6}]
    got = _safe(lambda: low_stock(items, 5))
    return got == ["A", "c"], f"low_stock returned {got}"


def check_csv_quoting(ws: Path):
    from inventory.export import to_csv_row
    got = _safe(lambda: to_csv_row({"name": 'Desk, large "oak"', "price": "$10.00", "qty": 2}))
    return got == '"Desk, large ""oak""",10.00,2', f"to_csv_row returned {got!r}"


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


def _safe(fn):
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return f"<{type(exc).__name__}>"


CHECKS = [
    ("visible_suite_passes", check_visible_suite),
    ("tests_not_modified", check_tests_unchanged),
    ("parse_price_all_formats", check_parse_price),
    ("other_caller_fixed", check_other_caller),
    ("discount_rounds_half_up", check_discount_half_up),
    ("low_stock_follows_docstring", check_low_stock),
    ("csv_quoting_follows_docstring", check_csv_quoting),
    ("rule_type_hints", check_rule_type_hints),
    ("rule_regression_tests", check_rule_regression_tests),
    ("rule_changelog", check_rule_changelog),
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
