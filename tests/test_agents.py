"""Regression tests for the workflow agents.

Everything runs against MockLLM, so the suite is deterministic,
offline, and fast.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from workflow_agents import (
    Agent,
    DocSummarizerAgent,
    EmailTriageAgent,
    MeetingNotesAgent,
    MockLLM,
    ToolError,
    make_file_tools,
)

SAMPLES = Path(__file__).resolve().parent.parent / "examples" / "sample_inputs"


@pytest.fixture
def llm() -> MockLLM:
    return MockLLM()


# --- email triage -------------------------------------------------------


def test_email_triage_classifies_samples(llm: MockLLM) -> None:
    emails = json.loads((SAMPLES / "emails.json").read_text(encoding="utf-8"))
    results = EmailTriageAgent(llm).run(emails)
    by_subject = {item["subject"]: item for item in results}
    assert len(results) == 5
    assert by_subject["SEV1: checkout is down in prod"]["category"] == "URGENT"
    assert by_subject["Please review the Q4 launch plan"]["category"] == "ACTION"
    assert by_subject["Weekly tech digest"]["category"] == "FYI"
    assert by_subject["Invoice #4821 due next week"]["category"] == "ACTION"
    assert by_subject["Moved our 1:1 to Thursday"]["category"] == "FYI"


def test_email_triage_reasons_and_drafts(llm: MockLLM) -> None:
    emails = json.loads((SAMPLES / "emails.json").read_text(encoding="utf-8"))
    results = EmailTriageAgent(llm).run(emails)
    by_subject = {item["subject"]: item for item in results}

    urgent = by_subject["SEV1: checkout is down in prod"]
    assert urgent["reason"], "urgent email should have a reason"
    assert urgent["draft_reply"], "urgent email should get a draft reply"

    action = by_subject["Please review the Q4 launch plan"]
    assert action["reason"], "action email should have a reason"
    assert action["draft_reply"], "action email should get a draft reply"

    fyi = by_subject["Weekly tech digest"]
    assert fyi["reason"], "fyi email should have a reason"
    assert fyi["draft_reply"] is None, "fyi email should not get a draft reply"


# --- meeting notes ------------------------------------------------------


def test_meeting_notes_extracts_sections(llm: MockLLM) -> None:
    transcript = (SAMPLES / "meeting.txt").read_text(encoding="utf-8")
    notes = MeetingNotesAgent(llm).run(transcript)
    assert notes["summary"], "notes should include a summary"
    assert len(notes["decisions"]) == 2
    assert any("load tests" in d for d in notes["decisions"])
    assert any("alert thresholds" in d for d in notes["decisions"])
    assert len(notes["action_items"]) == 2
    assert any("Meera" in a for a in notes["action_items"])
    assert any("Priya" in a for a in notes["action_items"])


# --- document summarizer ------------------------------------------------


def test_doc_summarizer_extracts_sections(llm: MockLLM) -> None:
    doc = (SAMPLES / "doc.md").read_text(encoding="utf-8")
    summary = DocSummarizerAgent(llm).run(doc)
    assert summary["tldr"].startswith("The Phoenix cache refresh project")
    assert any("5 minutes" in point for point in summary["key_points"])
    assert summary["open_questions"], "doc should surface open questions"


# --- tools --------------------------------------------------------------


def test_tool_roundtrip(tmp_path: Path) -> None:
    tools = make_file_tools(str(tmp_path))
    tools["write_file"]("notes/todo.txt", "hello world")
    assert tools["read_file"]("notes/todo.txt") == "hello world"
    assert tools["word_count"]("hello world") == 2


def test_tool_sandbox_blocks_escape(tmp_path: Path) -> None:
    tools = make_file_tools(str(tmp_path))
    with pytest.raises(ToolError):
        tools["read_file"]("../secret.txt")
    with pytest.raises(ToolError):
        tools["write_file"]("/etc/evil.txt", "nope")


# --- base agent loop ----------------------------------------------------


def test_base_agent_loop_uses_tools(llm: MockLLM, tmp_path: Path) -> None:
    agent = Agent(llm, tools=make_file_tools(str(tmp_path)))
    result = agent.run("How many words are in 'hello world test'?")
    assert "3" in result
    assert len(llm.calls) >= 2, "loop should make at least one tool round trip"


def test_base_agent_loop_respects_max_steps(tmp_path: Path) -> None:
    class ChattyLLM:
        def complete(self, prompt: str) -> str:
            return "CALL: word_count(never stops)"

    agent = Agent(ChattyLLM(), tools=make_file_tools(str(tmp_path)), max_steps=3)
    result = agent.run("Count words forever.")
    assert "max_steps" in result
