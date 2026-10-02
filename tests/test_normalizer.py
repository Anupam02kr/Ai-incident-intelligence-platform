import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.logs.normalizer import normalize_line, normalize_file


def test_hdfs_line_parses():
    line = "081109 203615 148 INFO dfs.DataNode$PacketResponder: PacketResponder 1 for block blk_38865049064139660 terminating"
    row = normalize_line(line)

    assert row["level"] == "INFO"
    assert row["source"] == "dfs.DataNode$PacketResponder"
    assert row["timestamp"] == "2008-11-09T20:36:15"


def test_openssh_line_parses():
    line = "Dec 10 06:55:46 LabSZ sshd[24200]: Failed password for invalid user webmaster from 173.234.31.186 port 38926 ssh2"
    row = normalize_line(line, openssh_year=2023)

    assert row["source"] == "sshd"
    assert row["level"] == "ERROR"  
    assert "2023-12-10" in row["timestamp"]


def test_unknown_format_falls_back_instead_of_crashing():
    line = "this is not a real log line at all"
    row = normalize_line(line)

    assert row["level"] == "UNKNOWN"
    assert row["message"] == line


def test_blank_line_returns_none():
    assert normalize_line("") is None
    assert normalize_line("   \n") is None


if __name__ == "__main__":
    hdfs_path = "data/raw/hdfs/HDFS_2k.log"
    ssh_path = "data/raw/openssh/OpenSSH_2k.log"

    if os.path.exists(hdfs_path):
        rows = normalize_file(hdfs_path)
        print(f"HDFS: parsed {len(rows)} lines, first 3:")
        for r in rows[:3]:
            print(" ", r)
    else:
        print(f"skip: {hdfs_path} not found yet")

    print()

    if os.path.exists(ssh_path):
        rows = normalize_file(ssh_path, openssh_year=2023)
        print(f"OpenSSH: parsed {len(rows)} lines, first 3:")
        for r in rows[:3]:
            print(" ", r)
    else:
        print(f"skip: {ssh_path} not found yet")
