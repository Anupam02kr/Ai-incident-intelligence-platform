# Runbook: Thread Pool and File Descriptor Exhaustion

When a service stops accepting new work but doesn't crash, check
whether it has exhausted a resource limit rather than hung. Thread
pool exhaustion looks like requests queuing indefinitely with CPU
usage that's low, not high - if all worker threads are blocked waiting
on something slow (a downstream call, a lock), no new work gets picked
up.

File descriptor exhaustion shows up as "too many open files" errors.
Check the current usage against the limit with `ulimit -n` and
`lsof -p <pid> | wc -l`. This is often caused by a leak - sockets or
file handles opened but never closed.

Fix: identify what's blocking the threads (thread dump helps) or what's
leaking file descriptors, and fix that root cause. Raising the limits
is a temporary mitigation, not a fix.
