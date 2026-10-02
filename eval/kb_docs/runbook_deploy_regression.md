# Runbook: Error Rate Spike After Deployment

If error rates or 500 responses spike shortly after a deployment, treat
the deployment as the primary suspect until ruled out. Check the
timestamp of the error spike against the deployment timestamp - a
match within a few minutes is a strong signal.

First step: check the diff of what was deployed. Look specifically for
changed error handling, new external calls that could fail, or
changed validation logic that might reject previously-valid input.

If the regression is confirmed, the fastest fix is usually a rollback
to the previous version while the root cause is investigated properly,
rather than trying to hotfix under pressure. Once rolled back, reproduce
the issue in a staging environment before attempting a fix.
