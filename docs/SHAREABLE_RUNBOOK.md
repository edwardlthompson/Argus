# Signed shareable runbook export

`dist/runbook.md` is a private artifact. To share a redacted copy:

1. Run `argus run --dry-run` on the private runner.
2. Strip repo security sections if any remain (status page already counts-only).
3. Optional: `gpg --clearsign dist/runbook.md` and attach the signature.

Argus does not auto-publish runbooks to public Pages.
