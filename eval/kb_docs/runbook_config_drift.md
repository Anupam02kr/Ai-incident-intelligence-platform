# Runbook: Configuration Drift and Bad Deploys

A service behaving unexpectedly after a deploy, with no code changes
involved, points at configuration rather than a code bug. Common cases:
wrong environment file loaded (staging config in production), a
feature flag rolled out further than intended, or a missing
environment variable causing a silent fallback to a default value.

Check what config the running process actually loaded - many
frameworks expose this via a debug endpoint or startup log line. Diff
it against the expected config for that environment.

Fix: correct the config and redeploy. Afterward, consider adding a
startup check that validates required config is present and correct
before the service accepts traffic, so this fails loudly next time
instead of degrading silently.
