# Runbook: Out of Memory Kills

When a process or container is killed unexpectedly with no application
error in the logs, check `dmesg` or the kernel log for "Out of memory:
Killed process" - this is the kernel's OOM killer stepping in when a
cgroup or the whole machine ran out of memory.

Common causes: a memory leak in the application (RSS growing steadily
over time rather than stabilizing), a container memory limit set too
low for actual peak usage, or a spike in traffic causing many
concurrent requests to each hold more memory than usual.

Check memory usage trends before the kill with your monitoring tool.
If it's a slow climb over hours, it's a leak - profile the application
to find what's not being garbage collected. If it's a sudden spike,
either the limit needs raising or the traffic spike needs handling
(rate limiting, autoscaling).
