# Runbook: Intermittent Network Timeouts Between Services

When one service intermittently times out calling another, and both
services otherwise look healthy, suspect the network path rather than
either service directly. Check for packet loss between the hosts
(`mtr` or `ping` over time), and check if the timeouts correlate with
load balancer health check failures or node rotation events.

Also check DNS - if the calling service resolves the target via DNS
and the DNS TTL is short, a stale cached IP after a deploy or scaling
event can cause requests to go to a dead or wrong endpoint.

Mitigation: add retries with backoff for transient network failures,
and alert on packet loss trends separately from application error
rates so network issues aren't mistaken for application bugs.
