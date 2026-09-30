"""LLM clients: a protocol, a real API client, and an offline mock.

The package is stdlib-only, so the real client uses urllib and the mock
uses plain keyword heuristics. Swap the mock for the real client when you
have an API key and want real answers.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol


class LLMClient(Protocol):
    """Anything with a complete() method can drive an agent."""

    def complete(self, prompt: str) -> str: ...


class OpenAICompatibleClient:
    """Minimal chat-completions client built on stdlib urllib.

    Reads the key from OPENAI_API_KEY. Works with any OpenAI-compatible
    endpoint by overriding base_url and model.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        api_key: str | None = None,
        timeout: int = 60,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout

    def complete(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
        ).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode())
        return body["choices"][0]["message"]["content"]


class MockLLM:
    """Deterministic, scripted LLM for offline demos and tests.

    Dispatches on [TASK: ...] markers in the prompt and answers with
    simple keyword heuristics. Not smart, just predictable: every prompt
    with the same marker and content returns the same answer, which is
    exactly what you want for demos, docs, and regression tests.
    """

    def __init__(self):
        self.calls: list[str] = []

    def complete(self, prompt: str) -> str:
        self.calls.append(prompt)
        if "[TASK: EMAIL_TRIAGE]" in prompt:
            return self._email_triage(prompt)
        if "[TASK: MEETING_NOTES]" in prompt:
            return self._meeting_notes(prompt)
        if "[TASK: DOC_SUMMARY]" in prompt:
            return self._doc_summary(prompt)
        if "[TASK: AGENT_LOOP]" in prompt:
            return self._agent_loop(prompt)
        return "FINAL: mock received a prompt without a known task marker"

    # --- email triage ---------------------------------------------------

    _URGENT = ("outage", "sev1", "urgent", "critical", "down", "incident", "breach")
    _ACTION = (
        "please",
        "review",
        "action",
        "due",
        "deadline",
        "invoice",
        "approve",
        "request",
    )

    def _email_triage(self, prompt: str) -> str:
        if "[EMAIL]" in prompt:
            body = prompt.split("[EMAIL]", 1)[1].rsplit("[/EMAIL]", 1)[0]
        else:
            body = prompt
        text = body.lower()
        if any(keyword in text for keyword in self._URGENT):
            category = "URGENT"
            reason = "signals an incident or outage that needs immediate attention"
            draft = (
                "Acknowledged, investigating now and will post an update "
                "within 15 minutes."
            )
        elif any(keyword in text for keyword in self._ACTION):
            category = "ACTION"
            reason = "asks for a review, approval, or delivery by a deadline"
            draft = "On it. I will review this and get back to you with an update."
        else:
            category = "FYI"
            reason = "informational, no action required"
            draft = "N/A"
        return f"CATEGORY: {category}\nREASON: {reason}\nDRAFT: {draft}"

    # --- meeting notes --------------------------------------------------

    def _meeting_notes(self, prompt: str) -> str:
        if "[TRANSCRIPT]" in prompt:
            transcript = prompt.split("[TRANSCRIPT]", 1)[1].rsplit("[/TRANSCRIPT]", 1)[0]
        else:
            transcript = prompt
        lines = [line.strip() for line in transcript.splitlines() if line.strip()]
        decisions = [
            line.split("DECISION:", 1)[1].strip() for line in lines if "DECISION:" in line
        ]
        actions = [
            line.split("ACTION:", 1)[1].strip() for line in lines if "ACTION:" in line
        ]
        topics = []
        for line in lines:
            if "DECISION:" in line or "ACTION:" in line:
                continue
            topics.append(line.split(":", 1)[1].strip() if ":" in line else line)
        out = ["SUMMARY: " + ("; ".join(topics[:3]) or "No discussion topics found.")]
        out.append("DECISIONS:")
        out.extend(f"- {decision}" for decision in decisions)
        out.append("ACTION ITEMS:")
        out.extend(f"- {action}" for action in actions)
        return "\n".join(out)

    # --- document summary -----------------------------------------------

    def _doc_summary(self, prompt: str) -> str:
        if "[DOC]" in prompt:
            doc = prompt.split("[DOC]", 1)[1].rsplit("[/DOC]", 1)[0]
        else:
            doc = prompt
        lines = [line.strip() for line in doc.splitlines()]
        first = next(
            (line for line in lines if line and not line.startswith("#")), ""
        )
        tldr = first.split(". ")[0].strip()
        if tldr and not tldr.endswith("."):
            tldr += "."
        headers = [line.lstrip("# ").strip() for line in lines if line.startswith("## ")]
        bullets = [line.lstrip("- ").strip() for line in lines if line.startswith("- ")]
        questions = [line for line in lines if line.endswith("?")]
        out = [f"TL;DR: {tldr or 'No summary available.'}", "KEY POINTS:"]
        for point in (headers + bullets)[:5]:
            out.append(f"- {point}")
        out.append("OPEN QUESTIONS:")
        for question in questions:
            out.append(f"- {question}")
        return "\n".join(out)

    # --- generic agent loop ----------------------------------------------

    def _agent_loop(self, prompt: str) -> str:
        if "OBSERVATION:" in prompt:
            return "FINAL: The text contains 3 words."
        return "CALL: word_count(hello world test)"
