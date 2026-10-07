#!/usr/bin/env python3
"""Automated checks for task `logs-eval`.

Usage: python check.py --workspace PATH
Prints one JSON object: {"score": float, "passed": int, "total": int, "checks": [...]}
"""
import argparse
import csv
import json
import re
from pathlib import Path

EXPECTED = json.loads(r"""{"errors": [{"timestamp_utc": "2024-05-02T02:17:44Z", "service": "queue_worker", "level": "ERROR", "message": "Job 412 failed: timeout", "repeat_count": 1, "source_line": 10}, {"timestamp_utc": "2024-05-02T02:40:24Z", "service": "mailer", "level": "ERROR", "message": "Job 101 failed: timeout", "repeat_count": 3, "source_line": 24}, {"timestamp_utc": "2024-05-02T02:47:35Z", "service": "queue_worker", "level": "FATAL", "message": "Scheduler crashed tick=275", "repeat_count": 5, "source_line": 27}, {"timestamp_utc": "2024-05-02T02:51:33Z", "service": "queue_worker", "level": "SEVERE", "message": "Disk quota exceeded vol=270", "repeat_count": 5, "source_line": 29}, {"timestamp_utc": "2024-05-02T02:59:19Z", "service": "scheduler", "level": "ERROR", "message": "Job 276 failed: timeout", "repeat_count": 4, "source_line": 35}, {"timestamp_utc": "2024-05-02T03:05:47Z", "service": "scheduler", "level": "FATAL", "message": "Scheduler crashed tick=541", "repeat_count": 1, "source_line": 37}, {"timestamp_utc": "2024-05-02T03:19:12Z", "service": "mailer", "level": "ERROR", "message": "Job 297 failed: timeout", "repeat_count": 1, "source_line": 48}, {"timestamp_utc": "2024-05-02T03:40:32Z", "service": "scheduler", "level": "ERROR", "message": "SMTP rejected message id=40", "repeat_count": 1, "source_line": 57}, {"timestamp_utc": "2024-05-02T03:53:39Z", "service": "scheduler", "level": "ERROR", "message": "SMTP rejected message id=226", "repeat_count": 1, "source_line": 59}, {"timestamp_utc": "2024-05-02T03:55:31Z", "service": "queue_worker", "level": "ERROR", "message": "Job 431 failed: timeout", "repeat_count": 1, "source_line": 60}, {"timestamp_utc": "2024-05-02T04:05:34Z", "service": "queue_worker", "level": "SEVERE", "message": "Disk quota exceeded vol=204", "repeat_count": 1, "source_line": 67}, {"timestamp_utc": "2024-05-02T04:11:14Z", "service": "mailer", "level": "ERROR", "message": "SMTP rejected message id=566", "repeat_count": 1, "source_line": 68}, {"timestamp_utc": "2024-05-02T04:14:27Z", "service": "scheduler", "level": "SEVERE", "message": "Disk quota exceeded vol=279", "repeat_count": 6, "source_line": 75}, {"timestamp_utc": "2024-05-02T04:17:57Z", "service": "mailer", "level": "ERROR", "message": "SMTP rejected message id=360", "repeat_count": 1, "source_line": 77}, {"timestamp_utc": "2024-05-02T04:25:02Z", "service": "queue_worker", "level": "ERROR", "message": "Job 518 failed: timeout", "repeat_count": 1, "source_line": 82}, {"timestamp_utc": "2024-05-02T04:33:25Z", "service": "mailer", "level": "ERROR", "message": "Job 254 failed: timeout", "repeat_count": 1, "source_line": 85}, {"timestamp_utc": "2024-05-02T04:43:26Z", "service": "scheduler", "level": "ERROR", "message": "Job 610 failed: timeout", "repeat_count": 1, "source_line": 87}, {"timestamp_utc": "2024-05-02T04:52:56Z", "service": "queue_worker", "level": "ERROR", "message": "Job 849 failed: timeout", "repeat_count": 1, "source_line": 93}, {"timestamp_utc": "2024-05-02T04:59:55Z", "service": "mailer", "level": "ERROR", "message": "Job 361 failed: timeout", "repeat_count": 1, "source_line": 103}, {"timestamp_utc": "2024-05-02T05:28:51Z", "service": "scheduler", "level": "ERROR", "message": "Job 941 failed: timeout", "repeat_count": 1, "source_line": 127}, {"timestamp_utc": "2024-05-02T05:39:02Z", "service": "queue_worker", "level": "ERROR", "message": "SMTP rejected message id=503", "repeat_count": 6, "source_line": 129}, {"timestamp_utc": "2024-05-02T05:47:15Z", "service": "queue_worker", "level": "FATAL", "message": "Scheduler crashed tick=727", "repeat_count": 1, "source_line": 137}, {"timestamp_utc": "2024-05-02T06:10:15Z", "service": "queue_worker", "level": "SEVERE", "message": "Disk quota exceeded vol=283", "repeat_count": 1, "source_line": 142}, {"timestamp_utc": "2024-05-02T06:13:41Z", "service": "scheduler", "level": "FATAL", "message": "Scheduler crashed tick=998", "repeat_count": 6, "source_line": 143}], "counts_by_service": {"queue_worker": 23, "mailer": 8, "scheduler": 21}, "entry_keys": ["timestamp_utc", "service", "level", "message", "repeat_count"]}""")


def _load(ws):
    return json.loads((ws / "errors.json").read_text(encoding="utf-8"))


def _norm(name):
    return str(name).lower().replace("-", "_")


def check_structure(ws):
    d = _load(ws)
    keys = set(EXPECTED["entry_keys"])
    ok = isinstance(d, dict) and isinstance(d.get("errors"), list) and isinstance(d.get("counts_by_service"), dict) \
        and all(isinstance(e, dict) and keys <= set(e) for e in d["errors"])
    return ok, "structure: missing keys or wrong types"


def check_entry_count(ws):
    got = len(_load(ws)["errors"])
    return got == len(EXPECTED["errors"]), f"wrong number of entries (got {got})"


def check_timestamps(ws):
    got = sorted(e["timestamp_utc"] for e in _load(ws)["errors"])
    exp = sorted(e["timestamp_utc"] for e in EXPECTED["errors"])
    return got == exp, f"{len(set(got) & set(exp))}/{len(exp)} timestamps match"


def _field_check(field):
    def fn(ws):
        got = {e["timestamp_utc"]: e.get(field, "<missing>") for e in _load(ws)["errors"]}
        exp = {e["timestamp_utc"]: e[field] for e in EXPECTED["errors"]}
        bad = [k for k in exp if got.get(k, "<missing>") != exp[k]]
        return not bad, f"{len(bad)} wrong `{field}` values"
    return fn


def check_counts(ws):
    got = {_norm(k): v for k, v in _load(ws)["counts_by_service"].items()}
    return got == EXPECTED["counts_by_service"], "counts_by_service: wrong values"


def check_service_names(ws):
    d = _load(ws)
    ok = bool(d["errors"]) and all(e["service"] == _norm(e["service"]) for e in d["errors"]) \
        and all(k == _norm(k) for k in d["counts_by_service"])
    return ok, "RULE: service names in the output are lower-case with '-' replaced by '_' (payment-service -> payment_service)."


def check_sorted(ws):
    keys = [(e["service"], e["timestamp_utc"]) for e in _load(ws)["errors"]]
    return bool(keys) and keys == sorted(keys), "RULE: `errors` is sorted by service, then by timestamp_utc, ascending."


def check_schema_header(ws):
    d = _load(ws)
    ok = d.get("schema_version") == 2 and d.get("generated_by") == "log-triage"
    return ok, 'RULE: the top-level object has "schema_version": 2 and "generated_by": "log-triage".'


CHECKS = [
    ("valid_structure", check_structure),
    ("entry_count", check_entry_count),
    ("timestamps_utc", check_timestamps),
    ("levels_uppercase", _field_check("level")),
    ("repeat_counts", _field_check("repeat_count")),
    ("counts_by_service", check_counts),
    ("rule_service_names", check_service_names),
    ("rule_sorted_errors", check_sorted),
    ("rule_schema_header", check_schema_header),
    ("rule_source_line", _field_check("source_line")),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ws = Path(ap.parse_args().workspace).resolve()
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
