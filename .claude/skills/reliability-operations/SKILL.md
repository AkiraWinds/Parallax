---
name: reliability-operations
description: >
  Review dimensions: reliability (retries, idempotency, partial failure,
  recovery) and operational readiness (logging, rollout, rollback).
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# Reliability & Operations

Apply these two review dimensions to the diff you're given.

## Reliability

- **Retries**: Are retries used where transient failures are expected, and avoided where they'd cause harm (e.g., non-idempotent writes)?
- **Timeouts**: Are timeouts set for external calls, and are they reasonable for the operation?
- **Idempotency**: Is the operation idempotent, so a retry or duplicate delivery doesn't cause incorrect state?
- **Partial failures**: What happens on partial failure mid-operation — does the system end up in a consistent state?
- **Fallback**: Is there a fallback behavior when a dependency is unavailable, or does the whole path fail hard?
- **Cancellation**: Can the operation be cancelled cleanly, and does cancellation leave things in a safe state?
- **Recovery**: If something fails, can the system recover automatically, or does it require manual intervention?
- **Cleanup**: Are resources (connections, locks, temp files, background tasks) cleaned up on both success and failure paths?
- **Consistency**: Does this change preserve consistency between related pieces of state (e.g., cache vs. source of truth)?

## Operations and Delivery

- **Logging**: Is there enough logging to diagnose a failure in production without needing to reproduce it locally?
- **Metrics**: Are metrics emitted for the behavior someone would need to monitor (latency, error rate, volume)?
- **Tracing**: Is this change traceable end-to-end if it's part of a larger request or workflow?
- **Deployment**: Does deployment require special sequencing (config first, migration first, feature flag)?
- **Rollout**: Is the rollout staged or guarded (flag, percentage, canary), or does it go to 100% immediately?
- **Rollback**: Can this be rolled back safely if it causes a problem in production?
- **Migration**: If there's a data migration, is it safe to run against production data, and is it reversible?
- **Documentation**: Is there documentation for anyone operating or debugging this in the future?
- **Handoff**: If this needs handoff (to on-call, another team), is there enough context for them to act on it?
