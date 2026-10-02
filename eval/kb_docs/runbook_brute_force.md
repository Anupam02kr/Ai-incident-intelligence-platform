# Runbook: SSH Brute Force / Auth Attacks

Repeated failed login attempts from the same or a rotating set of IPs
against SSH or an application login endpoint is almost always an
automated brute-force attempt, not a legitimate user forgetting their
password.

Check /var/log/auth.log (or your app's auth logs) for the source IP
and the account being targeted. If it's hitting many different
usernames, it's a credential-stuffing attempt; if it's hammering one
account, it's a targeted attack.

Mitigation: add the source IP to a fail2ban jail or firewall block
list. For application logins, enforce rate limiting per IP and per
account, and consider requiring MFA for accounts that have been
targeted. Rotate any credentials that may have been guessed correctly.
