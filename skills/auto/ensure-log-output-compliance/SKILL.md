---
name: ensure-log-output-compliance
description: Use when generating log output to ensure it adheres to specified structure and conventions.
---
1. Verify that the output JSON structure includes an `errors` array and a `counts_by_service` object.
2. Ensure that only ERROR or CRITICAL log entries are included, excluding WARN, WARNING, INFO, and DEBUG entries.
3. Format `timestamp_utc` in the output as `YYYY-MM-DDTHH:MM:SSZ`.
4. Convert the `level` of log entries to uppercase.
5. Extract the `message` from the log entry correctly, ensuring it follows the specified format.
6. Capture the last line of the traceback as the `exception` field, or set it to `null` if no traceback exists.
7. Calculate `repeat_count` accurately based on the number of repeated messages.
8. Validate the output against the specified log-triage conventions before finalizing the results.
