#!/usr/bin/env python3
"""Automated checks for task `data-learn`.

Usage: python check.py --workspace PATH
Prints one JSON object: {"score": float, "passed": int, "total": int, "checks": [...]}
"""
import argparse
import csv
import json
import re
from pathlib import Path

EXPECTED = json.loads(r"""{"money_key": "north_q1_revenue", "north_q1_revenue_usd": 3130.24, "north_q1_revenue_cents": 313024, "north_q1_orders": 10, "top_region": "North", "missing_amount_orders": 8, "duplicate_rows_removed": 7, "meta": {"source": "sales.csv", "rows_in": 101, "rows_used": 86}, "clean_header": ["order_id", "timestamp_utc", "region", "amount_cents"], "clean_rows": [["S-1001", "2024-06-10T00:00:00Z", "North", "15015"], ["S-1003", "2024-02-08T00:00:00Z", "East", "6602"], ["S-1004", "2024-03-02T00:00:00Z", "East", "29105"], ["S-1005", "2024-05-26T17:30:00Z", "West", "51384"], ["S-1006", "2024-05-06T00:00:00Z", "North", "24570"], ["S-1007", "2024-03-11T00:00:00Z", "South", "89318"], ["S-1008", "2024-05-08T00:00:00Z", "North", "56080"], ["S-1009", "2024-05-23T00:00:00Z", "East", "61500"], ["S-1010", "2024-04-16T00:00:00Z", "East", "14597"], ["S-1011", "2024-06-01T00:00:00Z", "South", "77556"], ["S-1012", "2024-06-28T12:00:00Z", "East", "56080"], ["S-1013", "2024-04-11T00:00:00Z", "East", "78977"], ["S-1014", "2024-06-10T00:00:00Z", "West", "33588"], ["S-1015", "2024-03-01T00:00:00Z", "North", "16016"], ["S-1016", "2024-04-10T00:00:00Z", "North", "11429"], ["S-1017", "2024-05-09T18:45:00Z", "North", "45827"], ["S-1018", "2024-05-30T00:00:00Z", "South", "54500"], ["S-1019", "2024-01-17T00:00:00Z", "South", "34324"], ["S-1021", "2024-02-17T00:00:00Z", "South", "78421"], ["S-1022", "2024-02-09T00:00:00Z", "North", "37922"], ["S-1023", "2024-05-01T00:00:00Z", "North", "20513"], ["S-1024", "2024-04-14T00:00:00Z", "West", "36391"], ["S-1025", "2024-01-20T21:00:00Z", "North", "20028"], ["S-1027", "2024-04-07T00:00:00Z", "South", "76496"], ["S-1028", "2024-06-21T00:00:00Z", "North", "24523"], ["S-1029", "2024-01-18T00:00:00Z", "West", "79266"], ["S-1030", "2024-04-10T00:00:00Z", "South", "33752"], ["S-1031", "2024-01-31T18:15:00Z", "East", "18473"], ["S-1032", "2024-01-08T04:15:00Z", "South", "63730"], ["S-1034", "2024-02-24T00:00:00Z", "East", "46609"], ["S-1035", "2024-01-21T22:15:00Z", "West", "23799"], ["S-1036", "2024-04-01T22:30:00Z", "North", "52140"], ["S-1037", "2024-04-02T00:00:00Z", "East", "79472"], ["S-1038", "2024-06-20T00:00:00Z", "South", "11937"], ["S-1039", "2024-03-31T22:00:00Z", "North", "31772"], ["S-1040", "2024-01-02T08:15:00Z", "South", "6502"], ["S-1041", "2024-06-07T00:00:00Z", "South", "14231"], ["S-1042", "2024-02-27T00:00:00Z", "West", "57722"], ["S-1043", "2024-05-28T00:00:00Z", "East", "44221"], ["S-1044", "2024-02-06T19:30:00Z", "South", "83902"], ["S-1045", "2024-05-13T03:15:00Z", "West", "88805"], ["S-1046", "2024-06-24T00:00:00Z", "South", "23768"], ["S-1047", "2024-03-19T00:00:00Z", "East", "5427"], ["S-1048", "2024-03-21T00:00:00Z", "West", "64612"], ["S-1049", "2024-06-24T12:15:00Z", "South", "5060"], ["S-1050", "2024-03-23T18:45:00Z", "West", "11869"], ["S-1051", "2024-01-12T00:00:00Z", "North", "30086"], ["S-1052", "2024-05-04T03:30:00Z", "South", "80827"], ["S-1053", "2024-02-09T00:00:00Z", "West", "88327"], ["S-1054", "2024-03-27T04:30:00Z", "East", "15751"], ["S-1055", "2024-03-04T00:00:00Z", "North", "64128"], ["S-1056", "2024-03-23T00:00:00Z", "North", "42600"], ["S-1057", "2024-01-20T00:00:00Z", "North", "57947"], ["S-1058", "2024-03-13T00:00:00Z", "East", "43468"], ["S-1060", "2024-03-06T14:30:00Z", "East", "7068"], ["S-1061", "2024-04-07T06:30:00Z", "South", "27933"], ["S-1062", "2024-06-17T18:00:00Z", "North", "82579"], ["S-1063", "2024-05-09T00:00:00Z", "North", "21381"], ["S-1064", "2024-03-18T00:00:00Z", "West", "15257"], ["S-1065", "2024-06-23T00:00:00Z", "South", "37678"], ["S-1066", "2024-06-12T00:00:00Z", "East", "47458"], ["S-1069", "2024-06-11T00:00:00Z", "North", "29876"], ["S-1070", "2024-02-26T00:00:00Z", "East", "80717"], ["S-1071", "2024-03-31T00:00:00Z", "West", "38629"], ["S-1072", "2024-02-22T00:00:00Z", "East", "81907"], ["S-1073", "2024-06-13T02:15:00Z", "North", "9194"], ["S-1074", "2024-02-08T00:00:00Z", "West", "41143"], ["S-1075", "2024-04-02T00:00:00Z", "East", "39717"], ["S-1076", "2024-03-20T00:00:00Z", "South", "34627"], ["S-1077", "2024-06-24T00:00:00Z", "West", "72647"], ["S-1078", "2024-03-13T00:00:00Z", "South", "29776"], ["S-1079", "2024-03-14T00:00:00Z", "South", "38480"], ["S-1080", "2024-05-01T06:00:00Z", "North", "80509"], ["S-1081", "2024-06-22T00:00:00Z", "North", "56416"], ["S-1083", "2024-03-08T00:00:00Z", "West", "64039"], ["S-1084", "2024-01-15T00:00:00Z", "East", "45610"], ["S-1085", "2024-03-04T00:00:00Z", "East", "70670"], ["S-1086", "2024-05-18T00:00:00Z", "North", "88911"], ["S-1087", "2024-02-28T00:00:00Z", "East", "5653"], ["S-1088", "2024-01-08T00:00:00Z", "West", "20951"], ["S-1089", "2024-05-26T17:30:00Z", "South", "10806"], ["S-1090", "2024-03-05T16:15:00Z", "West", "59139"], ["S-2000", "2024-04-01T03:30:00Z", "North", "12050"], ["S-2001", "2024-03-31T19:00:00Z", "North", "8025"], ["S-2002", "2023-12-31T17:30:00Z", "North", "6410"], ["S-2003", "2024-01-01T02:00:00Z", "North", "4500"]]}""")


def _load(ws):
    return json.loads((ws / "answer.json").read_text(encoding="utf-8"))


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _money(key):
    """Substantive check: the value is right either in dollars or in integer cents."""
    def fn(ws):
        got = _load(ws).get(key)
        ok = _is_num(got) and (abs(got - EXPECTED[key + "_usd"]) <= 0.01 or got == EXPECTED[key + "_cents"])
        return ok, f"{key}: wrong value (got {got!r})"
    return fn


def _num(key):
    def fn(ws):
        got = _load(ws).get(key)
        return _is_num(got) and got == EXPECTED[key], f"{key}: wrong value (got {got!r})"
    return fn


def _text(key):
    def fn(ws):
        got = _load(ws).get(key)
        return isinstance(got, str) and got.strip().lower() == EXPECTED[key].lower(), f"{key}: wrong value (got {got!r})"
    return fn


def check_money_in_cents(ws):
    key = EXPECTED["money_key"]
    got = _load(ws).get(key)
    ok = isinstance(got, int) and not isinstance(got, bool) and got == EXPECTED[key + "_cents"]
    return ok, "RULE: money values in answer.json are integer cents (1606.67 USD is written 160667)."


def check_meta(ws):
    got = _load(ws).get("meta")
    return got == EXPECTED["meta"], ("RULE: answer.json has an object `meta` = {\"source\": <input file name>, "
                                      "\"rows_in\": <number of data rows in the input file, duplicates included>, "
                                      "\"rows_used\": <number of distinct orders with a known amount>}.")


def check_clean_csv(ws):
    path = ws / "clean.csv"
    if not path.exists():
        return False, CLEAN_RULE
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    ok = bool(rows) and rows[0] == EXPECTED["clean_header"] \
        and sorted(map(tuple, rows[1:])) == sorted(tuple(r) for r in EXPECTED["clean_rows"])
    return ok, CLEAN_RULE


CLEAN_RULE = ("RULE: write workspace/clean.csv with the header order_id,timestamp_utc,region,amount_cents; one row per distinct order "
              "with a known amount; timestamp_utc as YYYY-MM-DDTHH:MM:SSZ (UTC); region in canonical spelling "
              "(North, South, East, West); amount in integer cents.")

CHECKS = [
    ("north_q1_revenue", _money("north_q1_revenue")),
    ("north_q1_orders", _num("north_q1_orders")),
    ("top_region", _text("top_region")),
    ("missing_amount_orders", _num("missing_amount_orders")),
    ("duplicate_rows_removed", _num("duplicate_rows_removed")),
    ("rule_money_in_cents", check_money_in_cents),
    ("rule_meta_block", check_meta),
    ("rule_clean_csv", check_clean_csv),
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
