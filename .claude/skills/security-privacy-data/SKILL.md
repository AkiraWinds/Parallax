---
name: security-privacy-data
description: >
  Review dimensions: security, privacy, and data/state handling
  (authn/authz, PII, secrets, validation, provenance, migration).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Security, Privacy & Data

Apply these two review dimensions to the diff you're given.

## Security and Privacy

- **Authn**: Is authentication required where it should be, and not bypassable?
- **Authz**: Is authorization checked at the right boundary — not just "is this user logged in" but "can this user do this specific thing"?
- **Tenant isolation**: If this is multi-tenant, can one tenant's data or actions leak into another's?
- **PII**: Does this diff introduce, log, or expose PII that wasn't handled carefully before?
- **Secrets**: Are secrets (keys, tokens, credentials) kept out of code, logs, and error messages?
- **Injection**: Is user-controlled input safe from injection (SQL, command, template, prompt) at every sink it reaches?
- **Unsafe writes**: Can this diff perform an unsafe write — one a malicious or malformed input could turn into an unintended data modification?
- **Auditability**: Is there an audit trail for sensitive actions this change introduces?

## Data and State

- **Validation**: Is data validated at the boundary where it enters the system, not just assumed correct downstream?
- **Provenance**: Is the provenance of the data (where it came from, how trustworthy it is) tracked or lost?
- **Migration**: If a migration is involved, is it safe for existing data, and is there a rollback path?
- **Serialization**: Does serialization/deserialization round-trip correctly, including edge cases (nulls, new/missing fields)?
- **Stale data**: Can this change read or act on stale data, and does that matter here?
- **Duplicated state**: Does this introduce duplicated state that can drift out of sync with its source?
- **Source of truth**: Is it clear what the single source of truth is for this data, or does this diff create a second one?
