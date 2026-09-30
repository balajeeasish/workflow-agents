"""Meeting notes agent: turn a transcript into summary, decisions, actions."""

from __future__ import annotations

from typing import Any

from ..base import Agent
from ..llm import LLMClient


class MeetingNotesAgent(Agent):
    """Converts a meeting transcript into structured notes.

    Expects decisions marked with DECISION: and action items marked with
    ACTION: in the transcript. Returns a dict with summary, decisions,
    and action_items (with owners).
    """

    def __init__(self, llm: LLMClient, **kwargs: Any):
        super().__init__(llm, **kwargs)
        self.name = "MeetingNotesAgent"

    def run(self, transcript: str) -> dict:
        """Summarize one meeting transcript into structured notes."""
        prompt = (
            "[TASK: MEETING_NOTES]\n"
            "Turn this meeting transcript into notes with exactly these sections:\n"
            "SUMMARY: <one or two sentences>\n"
            "DECISIONS:\n"
            "- <each decision>\n"
            "ACTION ITEMS:\n"
            "- <each action item with owner>\n"
            "The transcript marks decisions with DECISION: and actions with ACTION:.\n"
            "[TRANSCRIPT]\n" + transcript + "\n[/TRANSCRIPT]"
        )
        return self._parse(self.llm.complete(prompt))

    def _parse(self, response: str) -> dict:
        notes: dict = {"summary": "", "decisions": [], "action_items": []}
        section = None
        for line in response.splitlines():
            stripped = line.strip()
            if stripped.startswith("SUMMARY:"):
                notes["summary"] = stripped.partition(":")[2].strip()
                section = None
            elif stripped.startswith("DECISIONS:"):
                section = "decisions"
            elif stripped.startswith("ACTION ITEMS:"):
                section = "action_items"
            elif stripped.startswith("- ") and section:
                notes[section].append(stripped[2:].strip())
        return notes
