# Runbook: OAuth and Token Validation Failures

If an authentication service starts rejecting previously valid tokens
as expired or invalid, check clock synchronization first - JWT
validation is time-sensitive, and clock skew between the issuing and
validating services can cause valid tokens to be rejected.

If tokens are being rejected right after a deploy, check whether the
signing key or secret changed - tokens issued before a key rotation
won't validate against the new key unless both keys are accepted
during a transition window.

For OAuth callback failures specifically, check the redirect URI
configured with the provider against what the application is actually
using - these have to match exactly, including trailing slashes and
protocol (http vs https).
