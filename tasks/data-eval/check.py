#!/usr/bin/env python3
"""Automated checks for task `data-eval`.

Usage: python check.py --workspace PATH
Prints one JSON object: {"score": float, "passed": int, "total": int, "checks": [...]}
"""
import argparse
import csv
import json
import re
from pathlib import Path

EXPECTED = json.loads(r"""{"money_key": "march_revenue_utc", "march_revenue_utc_usd": 52957.19, "march_revenue_utc_cents": 5295719, "march_orders_utc": 44, "top_category": "toys", "missing_total_orders": 7, "duplicate_events_removed": 5, "meta": {"source": "orders.json", "rows_in": 88, "rows_used": 76}, "clean_header": ["order_id", "timestamp_utc", "category", "amount_cents"], "clean_rows": [["A-2002", "2024-03-15T06:27:00Z", "books", "221485"], ["A-2004", "2024-03-01T23:59:00Z", "books", "213220"], ["A-2005", "2024-02-29T10:16:00Z", "garden", "69276"], ["A-2006", "2024-03-15T08:06:00Z", "toys", "75284"], ["A-2007", "2024-03-02T15:23:00Z", "books", "83875"], ["A-2008", "2024-03-04T10:53:00Z", "garden", "208591"], ["A-2009", "2024-04-05T03:55:00Z", "music", "40748"], ["A-2011", "2024-03-25T21:16:00Z", "music", "43129"], ["A-2012", "2024-04-03T16:56:00Z", "music", "212776"], ["A-2013", "2024-03-19T20:05:00Z", "toys", "236733"], ["A-2014", "2024-03-06T17:06:00Z", "books", "1993"], ["A-2015", "2024-04-02T14:29:00Z", "garden", "198387"], ["A-2016", "2024-03-06T08:06:00Z", "music", "92861"], ["A-2017", "2024-04-05T12:21:00Z", "music", "96058"], ["A-2018", "2024-03-21T22:39:00Z", "books", "146708"], ["A-2019", "2024-02-24T13:39:00Z", "garden", "216033"], ["A-2020", "2024-04-06T15:08:00Z", "toys", "162997"], ["A-2021", "2024-04-04T19:44:00Z", "books", "207162"], ["A-2022", "2024-04-04T05:06:00Z", "music", "38421"], ["A-2023", "2024-03-20T13:12:00Z", "garden", "64390"], ["A-2024", "2024-03-29T19:29:00Z", "music", "136653"], ["A-2025", "2024-02-28T02:05:00Z", "books", "81747"], ["A-2026", "2024-03-26T04:27:00Z", "toys", "154451"], ["A-2027", "2024-02-29T07:49:00Z", "music", "159124"], ["A-2028", "2024-03-30T14:18:00Z", "books", "3155"], ["A-2029", "2024-03-22T16:18:00Z", "toys", "103030"], ["A-2030", "2024-03-23T13:23:00Z", "books", "197932"], ["A-2031", "2024-03-29T00:21:00Z", "garden", "15833"], ["A-2033", "2024-02-26T07:49:00Z", "toys", "158590"], ["A-2034", "2024-04-04T08:05:00Z", "toys", "68022"], ["A-2035", "2024-02-25T00:28:00Z", "toys", "203747"], ["A-2036", "2024-04-01T11:33:00Z", "music", "174962"], ["A-2037", "2024-03-10T16:04:00Z", "garden", "91880"], ["A-2038", "2024-03-14T03:13:00Z", "music", "70245"], ["A-2039", "2024-03-10T15:10:00Z", "books", "3454"], ["A-2040", "2024-04-08T07:44:00Z", "music", "97330"], ["A-2042", "2024-02-20T11:31:00Z", "toys", "134673"], ["A-2043", "2024-04-05T07:28:00Z", "music", "109718"], ["A-2044", "2024-02-24T04:25:00Z", "garden", "69690"], ["A-2045", "2024-03-26T13:35:00Z", "garden", "186650"], ["A-2046", "2024-03-20T18:51:00Z", "toys", "190902"], ["A-2047", "2024-03-20T07:06:00Z", "garden", "32009"], ["A-2048", "2024-03-29T18:51:00Z", "garden", "205371"], ["A-2049", "2024-03-16T14:32:00Z", "music", "236179"], ["A-2050", "2024-04-07T16:58:00Z", "toys", "78465"], ["A-2051", "2024-04-01T08:38:00Z", "garden", "90052"], ["A-2053", "2024-03-04T01:48:00Z", "toys", "215620"], ["A-2054", "2024-03-12T16:50:00Z", "garden", "117559"], ["A-2055", "2024-03-19T12:13:00Z", "garden", "175777"], ["A-2056", "2024-02-29T06:18:00Z", "toys", "21884"], ["A-2057", "2024-02-20T03:49:00Z", "music", "108049"], ["A-2058", "2024-03-29T04:45:00Z", "garden", "209277"], ["A-2059", "2024-03-07T00:07:00Z", "toys", "73259"], ["A-2060", "2024-03-25T04:23:00Z", "garden", "161515"], ["A-2061", "2024-02-23T12:03:00Z", "music", "34483"], ["A-2062", "2024-03-06T15:30:00Z", "toys", "1580"], ["A-2063", "2024-02-21T08:47:00Z", "music", "206008"], ["A-2064", "2024-02-28T03:09:00Z", "toys", "216709"], ["A-2065", "2024-04-01T20:31:00Z", "garden", "199047"], ["A-2066", "2024-02-21T06:11:00Z", "garden", "166254"], ["A-2067", "2024-03-02T04:07:00Z", "garden", "22909"], ["A-2068", "2024-03-02T12:08:00Z", "toys", "237879"], ["A-2069", "2024-03-23T04:51:00Z", "toys", "191717"], ["A-2070", "2024-04-07T00:09:00Z", "books", "215189"], ["A-2071", "2024-02-25T00:42:00Z", "music", "174208"], ["A-2072", "2024-03-25T08:04:00Z", "toys", "194795"], ["A-2073", "2024-03-03T02:38:00Z", "toys", "65832"], ["A-2074", "2024-03-30T20:04:00Z", "toys", "12951"], ["A-2075", "2024-03-23T11:33:00Z", "garden", "162487"], ["A-2076", "2024-03-25T06:15:00Z", "toys", "153015"], ["A-2077", "2024-03-31T07:01:00Z", "garden", "102084"], ["A-2079", "2024-02-20T08:24:00Z", "toys", "5489"], ["A-2080", "2024-03-27T23:38:00Z", "music", "161375"], ["A-3000", "2024-03-01T01:00:00Z", "books", "12050"], ["A-3001", "2024-03-31T18:00:00Z", "books", "8025"], ["A-3002", "2024-04-01T03:30:00Z", "toys", "30000"]]}""")


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


CLEAN_RULE = ("RULE: write workspace/clean.csv with the header order_id,timestamp_utc,category,amount_cents; one row per distinct order "
              "with a known amount; timestamp_utc as YYYY-MM-DDTHH:MM:SSZ (UTC); category lower-case and trimmed; amount in integer cents.")


def check_sorted_keys_format(ws):
    text = (ws / "answer.json").read_text(encoding="utf-8")
    return text == json.dumps(json.loads(text), indent=2, sort_keys=True) + "\n", "format"


CHECKS = [
    ("march_revenue_utc", _money("march_revenue_utc")),
    ("march_orders_utc", _num("march_orders_utc")),
    ("top_category", _text("top_category")),
    ("missing_total_orders", _num("missing_total_orders")),
    ("duplicate_events_removed", _num("duplicate_events_removed")),
    ("rule_money_in_cents", check_money_in_cents),
    ("rule_meta_block", check_meta),
    ("rule_clean_csv", check_clean_csv),
    ("rule_sorted_keys_format", check_sorted_keys_format),
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
