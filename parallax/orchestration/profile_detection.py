"""Deterministic fallback signal detection for the Agent-System Extension.

Implements Evidence_Driven_PR_Review_System_Spec.md Section 9.2's *second*
detection path — "high-confidence repository/PR signals, when no explicit
declaration was given." The *first* and preferred path is asking the human
directly at Stage 0 (Section 10); this module only runs when that wasn't
given, and only ever produces a fallback recommendation for the
orchestrator, never an authoritative decision the human didn't make.

This is deliberately a plain regex/substring scanner, not an LLM call — the
value it adds is a reproducible, testable first pass over the changed
files' paths and contents, per the signal list in Section 9.2.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Section 9.2's signal list, grouped by what each pattern actually detects.
# Patterns are matched against file contents; SIGNAL_PATH_HINTS are matched
# against file paths.
_SIGNAL_CONTENT_PATTERNS: dict[str, re.Pattern[str]] = {
    "llm_sdk_import": re.compile(
        r"^\s*(?:import|from)\s+(anthropic|openai|google\.generativeai|"
        r"mistralai|cohere)\b",
        re.MULTILINE,
    ),
    "agent_framework_import": re.compile(
        r"^\s*(?:import|from)\s+(langchain|langgraph|llama_index|"
        r"crewai|autogen|semantic_kernel)\b",
        re.MULTILINE,
    ),
    "mcp": re.compile(r"\bMCP\b|model[_-]context[_-]protocol", re.IGNORECASE),
    "retrieval_or_vector_db": re.compile(
        r"\b(retriever|retrieval|embeddings?|vector[_-]?store|"
        r"pinecone|weaviate|chroma|qdrant|faiss)\b",
        re.IGNORECASE,
    ),
    "memory": re.compile(r"\bmemory[_-]?(write|store|state)\b", re.IGNORECASE),
    "workflow_orchestration": re.compile(
        r"\b(state[_-]?graph|workflow|orchestrat\w*)\b", re.IGNORECASE
    ),
    "graders_or_eval": re.compile(
        r"\b(grader|eval[_-]?scenario|llm[_-]?judge|eval[_-]?set)\b",
        re.IGNORECASE,
    ),
    "model_configuration": re.compile(
        r"\b(model[_-]?name|temperature\s*=|top_p\s*=|max_tokens)\b",
        re.IGNORECASE,
    ),
    "tool_schema": re.compile(
        r"\b(tool[_-]?schema|function[_-]?calling|@tool\b)\b", re.IGNORECASE
    ),
    "human_agent_handoff": re.compile(
        r"\bhuman[_-]?(handoff|escalation|approval|in[_-]the[_-]loop)\b",
        re.IGNORECASE,
    ),
    "agent_traces": re.compile(r"\b(agent[_-]?trace|trace[_-]?id)\b", re.IGNORECASE),
}

_SIGNAL_PATH_PATTERNS: dict[str, re.Pattern[str]] = {
    "prompt_file": re.compile(r"prompt[s]?\.py$|/prompts?/", re.IGNORECASE),
    "agent_file": re.compile(r"/agents?/|agent[s]?\.py$", re.IGNORECASE),
}


@dataclass
class DetectionResult:
    matched_signals: list[str] = field(default_factory=list)
    matched_files: dict[str, list[str]] = field(default_factory=dict)

    @property
    def triggered(self) -> bool:
        """Section 9.2: any matched signal is treated as high-confidence
        enough to recommend activating the Agent-System Extension — the
        human (or a corrective follow-up, Section 16.6) still has the
        final say, this is a recommendation, not an authoritative gate."""
        return bool(self.matched_signals)


def detect_agent_system_signals(
    files: dict[str, str],
) -> DetectionResult:
    """Scan changed files for Section 9.2 signals.

    `files` maps changed file path -> file content (the orchestrator
    supplies this from the diff scope, Section 10 Stage 1). Returns which
    signal categories matched and in which files, so the recommendation is
    explainable rather than a bare boolean.
    """
    result = DetectionResult()
    matched: set[str] = set()

    for path, content in files.items():
        for name, pattern in _SIGNAL_PATH_PATTERNS.items():
            if pattern.search(path):
                matched.add(name)
                result.matched_files.setdefault(name, []).append(path)
        for name, pattern in _SIGNAL_CONTENT_PATTERNS.items():
            if pattern.search(content):
                matched.add(name)
                result.matched_files.setdefault(name, []).append(path)

    result.matched_signals = sorted(matched)
    return result
