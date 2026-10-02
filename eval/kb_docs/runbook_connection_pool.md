# Runbook: Database Connection Pool Exhaustion

Symptoms: new requests hang waiting for a database connection, error
logs show "connection pool exhausted" or "timeout waiting for
connection." This almost always means connections are being checked
out and not returned - usually a code path that opens a connection but
doesn't close it in a finally block, or a slow query holding a
connection far longer than expected.

First step: check `pg_stat_activity` (Postgres) or equivalent to see
how many connections are open and what they're doing. Long-idle
connections in "idle in transaction" state are the usual culprit.

Fix: identify and kill the offending long-running transaction, then
find and patch the code path that isn't releasing connections properly.
As a stopgap, increasing pool size buys time but doesn't fix the leak.
