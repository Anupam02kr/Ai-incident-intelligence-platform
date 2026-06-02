# 502s on checkout API

Last updated: march sometime

**what we usually see**
- ALB throws 502/504
- latency graph goes hockey stick
- health checks unhappy

**try this first**
1. check if a deploy landed in the last 30 min — rollback is boring but works
2. `kubectl get pods -n checkout` — anything CrashLoopBackOff?
3. bump replicas by 2 if CPU looks fine but queue is backing up
4. DB side: look for connections maxed or queries sitting >30s

**how you know it's better**
- 5xx under 1% for ~10 min
- p95 back under 400ms

**page someone if**
still ugly after 15 min, or customers yelling in #support
