"""Document summarizer agent: long text in, TL;DR plus key points out."""

from __future__ import annotations

from typing import Any

from ..base import Agent
from ..llm import LLMClient


class DocSummarizerAgent(Agent):
    """Summarizes a long document into TL;DR, key points, and open questions.

    Returns a dict with tldr, key_points, and open_questions.
    """

    def __init__(self, llm: LLMClient, **kwargs: Any):
        super().__init__(llm, **kwargs)
        self.name = "DocSummarizerAgent"

    def run(self, doc: str) -> dict:
        """Summarize one document."""
        prompt = (
            "[TASK: DOC_SUMMARY]\n"
            "Summarize this document with exactly these sections:\n"
            "TL;DR: <one sentence>\n"
            "KEY POINTS:\n"
            "- <each key point>\n"
            "OPEN QUESTIONS:\n"
            "- <each open question>\n"
            "[DOC]\n" + doc + "\n[/DOC]"
        )
        return self._parse(self.llm.complete(prompt))

    def _parse(self, response: str) -> dict:
        summary: dict = {"tldr": "", "key_points": [], "open_questions": []}
        section = None
        for line in response.splitlines():
            stripped = line.strip()
            if stripped.startswith("TL;DR:"):
                summary["tldr"] = stripped.partition(":")[2].strip()
                section = None
            elif stripped.startswith("KEY POINTS:"):
                section = "key_points"
            elif stripped.startswith("OPEN QUESTIONS:"):
                section = "open_questions"
            elif stripped.startswith("- ") and section:
                summary[section].append(stripped[2:].strip())
        return summary
