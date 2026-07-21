# Parallax

## Project Name

**Parallax**

Repository name:

```text
parallax-review
```

## Meaning

Parallax is the apparent shift in an object’s position when it is viewed from different perspectives.

A pull request has the same property. The author, reviewer, tests, runtime traces, architecture contracts, and domain-specific scanners may each reveal a different part of the truth. No single perspective is sufficient on its own.

Parallax combines these perspectives to help a human reviewer locate the real risk, understand the change, and make an evidence-based merge decision.

## How It Fits the Existing System

- **Akira** observes what the agent system has actually become.
- **SANYI** checks whether the change respects the architecture change contract.
- **Parallax** combines multiple perspectives, verifies the evidence, and decides whether the proposed change is ready.

```text
Akira observes.
SANYI governs.
Parallax judges the change from multiple perspectives.
```

## Product Definition

> **Parallax is an evidence-driven PR review system for general and agentic software changes.**

It applies a general software-engineering review to every pull request and conditionally adds agent-system review for changes involving LLMs, agents, tools, workflows, retrieval, memory, evaluation, or human-agent handoffs.

It can integrate findings from Akira and SANYI without replacing or rewriting their native output schemas.

## Core Philosophy

> **Different perspectives. Better judgment.**

Parallax should not maximize the number of review comments. It should:

- reconstruct the intent of the change;
- trace behavior from input to impact;
- gather evidence from multiple sources;
- distinguish verified findings from hypotheses;
- identify material risks;
- reduce duplicate and low-value review noise;
- support a clear, explainable merge decision;
- preserve human responsibility for approval.

## Suggested Taglines

Primary:

> **Different perspectives. Better judgment.**

Alternative:

> **See the change from more than one point of view.**

Alternative:

> **Evidence before merge.**

## Naming Guidance

Use **Parallax** as the project and product name.

Use **parallax-review** as the GitHub repository name to make the purpose discoverable.

Suggested short description:

> Evidence-driven PR review for general and agentic software changes.
