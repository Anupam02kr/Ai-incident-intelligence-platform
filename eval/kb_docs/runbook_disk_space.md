# Runbook: Disk Space Exhaustion

A service failing to write logs, temp files, or database writes with
"no space left on device" needs immediate disk space triage. Check
usage with `df -h` first to confirm which mount is full.

Common causes: log files that were never rotated, a temp directory
accumulating files from a job that doesn't clean up after itself, or a
database's write-ahead log growing because replication or a backup
process is stuck and can't consume it.

Immediate fix: find and clear safe-to-delete files (old logs, temp
files) to restore headroom. Root cause fix: add log rotation if
missing, fix the job that isn't cleaning up, or resolve whatever is
blocking the WAL from being consumed.
