#!/usr/bin/env python3
"""Automated checks for task `logs-learn`.

Usage: python check.py --workspace PATH
Prints one JSON object: {"score": float, "passed": int, "total": int, "checks": [...]}
"""
import argparse
import csv
import json
import re
from pathlib import Path

EXPECTED = json.loads(r"""{"errors": [{"timestamp_utc": "2024-05-01T03:06:40Z", "service": "inventory_service", "level": "ERROR", "message": "Stock update failed sku=72", "exception": null, "repeat_count": 1}, {"timestamp_utc": "2024-05-01T03:09:30Z", "service": "inventory_service", "level": "ERROR", "message": "Upstream call failed id=413", "exception": "TimeoutError: upstream did not answer in 30s", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T03:43:13Z", "service": "auth_service", "level": "ERROR", "message": "Charge failed order=222", "exception": "TimeoutError: upstream did not answer in 30s", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T03:54:35Z", "service": "inventory_service", "level": "ERROR", "message": "Stock update failed sku=148", "exception": null, "repeat_count": 3}, {"timestamp_utc": "2024-05-01T03:56:45Z", "service": "payment_service", "level": "ERROR", "message": "Upstream call failed id=811", "exception": "TimeoutError: upstream did not answer in 30s", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T04:02:04Z", "service": "payment_service", "level": "ERROR", "message": "Charge failed order=28", "exception": null, "repeat_count": 1}, {"timestamp_utc": "2024-05-01T04:06:19Z", "service": "auth_service", "level": "CRITICAL", "message": "Queue overflow depth=515", "exception": "KeyError: 'sku'", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T04:08:17Z", "service": "inventory_service", "level": "ERROR", "message": "Upstream call failed id=191", "exception": "ValueError: invalid card number", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T04:17:25Z", "service": "inventory_service", "level": "CRITICAL", "message": "Queue overflow depth=417", "exception": "TimeoutError: upstream did not answer in 30s", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T04:25:11Z", "service": "payment_service", "level": "CRITICAL", "message": "Queue overflow depth=327", "exception": "KeyError: 'sku'", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T04:49:49Z", "service": "auth_service", "level": "ERROR", "message": "Charge failed order=741", "exception": "TimeoutError: upstream did not answer in 30s", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T04:50:54Z", "service": "inventory_service", "level": "ERROR", "message": "Charge failed order=471", "exception": "ValueError: invalid card number", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T04:56:56Z", "service": "payment_service", "level": "CRITICAL", "message": "Database unreachable node=640", "exception": null, "repeat_count": 1}, {"timestamp_utc": "2024-05-01T05:05:36Z", "service": "auth_service", "level": "ERROR", "message": "Upstream call failed id=988", "exception": null, "repeat_count": 1}, {"timestamp_utc": "2024-05-01T05:15:13Z", "service": "auth_service", "level": "ERROR", "message": "Stock update failed sku=935", "exception": "ValueError: invalid card number", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T05:18:36Z", "service": "payment_service", "level": "ERROR", "message": "Charge failed order=777", "exception": "ValueError: invalid card number", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T05:22:52Z", "service": "auth_service", "level": "ERROR", "message": "Charge failed order=365", "exception": "TimeoutError: upstream did not answer in 30s", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T05:29:03Z", "service": "auth_service", "level": "ERROR", "message": "Upstream call failed id=830", "exception": "ConnectionResetError: peer closed connection", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T05:33:38Z", "service": "payment_service", "level": "ERROR", "message": "Charge failed order=900", "exception": null, "repeat_count": 1}, {"timestamp_utc": "2024-05-01T05:37:34Z", "service": "inventory_service", "level": "ERROR", "message": "Charge failed order=266", "exception": "TimeoutError: upstream did not answer in 30s", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T05:41:52Z", "service": "auth_service", "level": "ERROR", "message": "Stock update failed sku=644", "exception": "ValueError: invalid card number", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T06:01:43Z", "service": "payment_service", "level": "ERROR", "message": "Upstream call failed id=614", "exception": null, "repeat_count": 1}, {"timestamp_utc": "2024-05-01T06:04:08Z", "service": "payment_service", "level": "ERROR", "message": "Stock update failed sku=30", "exception": "ConnectionResetError: peer closed connection", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T06:19:16Z", "service": "inventory_service", "level": "ERROR", "message": "Upstream call failed id=858", "exception": "TimeoutError: upstream did not answer in 30s", "repeat_count": 1}, {"timestamp_utc": "2024-05-01T06:19:56Z", "service": "inventory_service", "level": "ERROR", "message": "Upstream call failed id=669", "exception": null, "repeat_count": 3}], "counts_by_service": {"inventory_service": 13, "auth_service": 8, "payment_service": 8}, "entry_keys": ["timestamp_utc", "service", "level", "message", "exception", "repeat_count"]}""")


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
    ("exception_fields", _field_check("exception")),
    ("repeat_counts", _field_check("repeat_count")),
    ("counts_by_service", check_counts),
    ("rule_service_names", check_service_names),
    ("rule_sorted_errors", check_sorted),
    ("rule_schema_header", check_schema_header),
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
