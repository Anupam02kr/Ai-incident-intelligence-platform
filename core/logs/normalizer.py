import re
from datetime import datetime

hdfs_pattern = re.compile(
    r"^(?P<date>\d{6})\s+(?P<time>\d{6})\s+(?P<pid>\d+)\s+"
    r"(?P<level>[A-Z]+)\s+(?P<source>[\w$.]+):\s*(?P<message>.*)$"
)


def parse_hdfs(line):
    m = hdfs_pattern.match(line)
    if not m:
        return None

    ts = datetime.strptime(m.group("date") + m.group("time"), "%y%m%d%H%M%S")
    return {
        "timestamp": ts.isoformat(),
        "level": m.group("level"),
        "source": m.group("source"),
        "message": m.group("message").strip(),
    }

openssh_pattern = re.compile(
    r"^(?P<month>\w{3})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+(?P<source>[\w.\-]+)(\[\d+\])?:\s*(?P<message>.*)$"
)

severity_keywords = [
    ("fatal", "FATAL"),
    ("failed", "ERROR"),
    ("failure", "ERROR"),
    ("invalid", "ERROR"),
    ("error", "ERROR"),
    ("break-in", "WARN"),
    ("warn", "WARN"),
    ("accepted", "INFO"),
    ("session opened", "INFO"),
    ("session closed", "INFO"),
]


def guess_severity(message):
    msg_lower = message.lower()
    for keyword, level in severity_keywords:
        if keyword in msg_lower:
            return level
    return "INFO"


def parse_openssh(line, year=None):
    m = openssh_pattern.match(line)
    if not m:
        return None

    if year is None:
        year = datetime.now().year

    raw_ts = f"{year} {m.group('month')} {m.group('day')} {m.group('time')}"
    try:
        ts = datetime.strptime(raw_ts, "%Y %b %d %H:%M:%S")
    except ValueError:
        return None

    message = m.group("message").strip()
    return {
        "timestamp": ts.isoformat(),
        "level": guess_severity(message),
        "source": m.group("source"),
        "message": message,
    }

level_keyword_pattern = re.compile(
    r"\b(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b", re.IGNORECASE
)


def parse_fallback(line):
    match = level_keyword_pattern.search(line)
    level = match.group(1).upper() if match else "UNKNOWN"

    return {
        "timestamp": None,
        "level": level,
        "source": "unknown",
        "message": line.strip(),
    }


parsers = [parse_hdfs, parse_openssh]


def normalize_line(line, openssh_year=None):
    line = line.rstrip("\n")
    if not line.strip():
        return None

    for parser in parsers:
        if parser is parse_openssh:
            row = parser(line, year=openssh_year)
        else:
            row = parser(line)

        if row is not None:
            return row

    return parse_fallback(line)


def normalize_file(path, openssh_year=None):
    rows = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            row = normalize_line(line, openssh_year=openssh_year)
            if row:
                rows.append(row)
    return rows


if __name__ == "__main__":
    test_lines = [
        "081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating",
        "Dec 10 06:55:46 LabSZ sshd[24200]: reverse mapping checking getaddrinfo for ns.marryaldkfaczcz.com failed - POSSIBLE BREAK-IN ATTEMPT!",
        "some totally unrecognized log format here, level=oops",
    ]

    for line in test_lines:
        print(normalize_line(line))