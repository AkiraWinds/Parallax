# Review Report Template

Produced once by the orchestrator after Stage 7–10, over every dispatched
subagent's combined canonical findings.

```markdown
# PR Review

## 1. Overall Understanding

## 2. Review Contract

## 3. Change and Execution Map

## 4. Static Analysis (Layer 1 — tool-verified, not LLM-judged)
- Tool run:
- Findings: (raw linter/formatter output, or "no static analysis tool detected")

## 5. What Looks Strong

## 6. Blocking Findings

## 7. Important Findings

## 8. Questions and Unverified Hypotheses

## 9. Suggestions

## 10. Testing and Evaluation Assessment

## 11. Definition of Done Assessment

## 12. Source-System Summary

### Subagent Dispatch
- A (Intent, Correctness & Testing): dispatched / completed | failed after retries
- B (Reliability & Operations): dispatched / completed | failed after retries
- C (Security, Privacy & Data): dispatched / completed | failed after retries
- D (Architecture & Documentation): dispatched / completed | failed after retries
- E (Agent Runtime & Tooling): dispatched | skipped (Agent-System Extension not active) / completed | failed after retries
- F (Accountability & Safeguards): dispatched | skipped (Agent-System Extension not active) / completed | failed after retries
- G (SANYI): dispatched | skipped (no SANYI.md) / completed | failed after retries

### SANYI
- contract found:
- review invoked:
- source verdict:
- findings imported:

## 13. Suggested Merge Decision

approve | comment | request_changes | insufficient_context
```
