# Runbook: Disk Failure and Block Errors

When a storage node reports repeated block write or termination errors,
suspect a failing physical disk before anything else. Check disk health
with `smartctl -a /dev/sdX` and look for reallocated sector counts or
pending sector counts above zero - these are early warning signs of a
drive that's about to fail completely.

If SMART data looks clean but errors persist, check dmesg for I/O errors
at the kernel level (`dmesg | grep -i error`). A disk can produce
application-level errors before SMART attributes cross their thresholds.

Mitigation: if a specific disk is confirmed failing, drain the node
(stop new writes, let existing replicas rebalance), then physically
replace the disk. Don't wait for total failure - a degrading disk slows
down every read/write that touches it, which cascades into timeouts
elsewhere in the cluster.
