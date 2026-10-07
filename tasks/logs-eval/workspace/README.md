# worker.log - format

Each log entry starts with a line:

    [<date> <time> <offset>] <service> | <LEVEL> | <message>

- The offset is a UTC offset such as `+0700`, `-0500` or `+0000`.
- Error-class levels are ERROR, SEVERE and FATAL. Level names are not always written in upper case.
- Lines that start with spaces belong to the entry above them (for example a JSON payload dump).
- A line `-- last message repeated N times --` means the entry above it (together with its extra lines) occurred N more times.
