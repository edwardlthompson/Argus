# Read-only GitHub App (optional)

For report-only scans without a classic PAT:

1. Create a GitHub App with **Metadata: Read-only** and **Contents: Read-only**.
2. Install on the orgs/users you want to score.
3. Set `GITHUB_APP_ID`, `GITHUB_APP_INSTALLATION_ID`, and a private key path in the **private runner** secrets only.
4. Prefer classic `GITHUB_TOKEN` / fine-grained PAT until App token minting is wired in Argus.

Do not put App private keys in the public product repo.
