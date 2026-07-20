"""Diff-relevance / Agent-System Extension signal detection tests
(Section 27.1: 'diff relevance').

This module is Section 9.2's *fallback* path only — these tests check the
mechanical scanner, not the (preferred) human-declared-profile path, which
has no code to test since it's just accepting what Stage 0 was told.
"""

from __future__ import annotations

from parallax.orchestration.profile_detection import detect_agent_system_signals


def test_plain_crud_change_does_not_trigger():
    files = {
        "src/orders/repository.py": (
            "def get_order(order_id):\n"
            "    return db.query(Order).filter_by(id=order_id).first()\n"
        )
    }
    result = detect_agent_system_signals(files)
    assert not result.triggered
    assert result.matched_signals == []


def test_llm_sdk_import_triggers():
    files = {"backend/agents/router.py": "import anthropic\n\nclient = anthropic.Anthropic()\n"}
    result = detect_agent_system_signals(files)
    assert result.triggered
    assert "llm_sdk_import" in result.matched_signals


def test_agent_framework_import_triggers():
    files = {"backend/graph.py": "from langgraph.graph import StateGraph\n"}
    result = detect_agent_system_signals(files)
    assert "agent_framework_import" in result.matched_signals


def test_prompt_file_path_triggers():
    files = {"backend/agents/prompts.py": "SEARCH_AGENT_PROMPT = 'You are a helpful agent.'\n"}
    result = detect_agent_system_signals(files)
    assert "prompt_file" in result.matched_signals


def test_retrieval_and_vector_db_signal_triggers():
    files = {"backend/rag/index.py": "from pinecone import Index\n\nretriever = Index('docs')\n"}
    result = detect_agent_system_signals(files)
    assert "retrieval_or_vector_db" in result.matched_signals


def test_matched_files_records_which_file_matched():
    files = {"backend/agents/router.py": "import openai\n"}
    result = detect_agent_system_signals(files)
    assert "backend/agents/router.py" in result.matched_files["llm_sdk_import"]


def test_multiple_files_multiple_signals():
    files = {
        "backend/agents/prompts.py": "ROUTER_PROMPT = '...'\n",
        "backend/mcp/server.py": "# implements an MCP tool server\n",
        "frontend/components/Button.tsx": "export function Button() { return null; }\n",
    }
    result = detect_agent_system_signals(files)
    # backend/agents/prompts.py matches both path-based signals (it's
    # under /agents/ AND named prompts.py); backend/mcp/server.py's
    # comment matches the MCP content signal. frontend/components/Button
    # matches nothing.
    assert {"prompt_file", "agent_file", "mcp"} <= set(result.matched_signals)
    assert "frontend/components/Button.tsx" not in [
        f for files in result.matched_files.values() for f in files
    ]
