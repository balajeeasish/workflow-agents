"""Email triage agent: classify inbox items and draft replies."""

from __future__ import annotations

from typing import Any

from ..base import Agent
from ..llm import LLMClient


class EmailTriageAgent(Agent):
    """Sorts emails into URGENT / ACTION / FYI with a one-line reason.

    For ACTION and URGENT items it also drafts a short reply the user can
    review and send. FYI items get no draft.
    """

    def __init__(self, llm: LLMClient, **kwargs: Any):
        super().__init__(llm, **kwargs)
        self.name = "EmailTriageAgent"

    def classify(self, email: dict) -> dict:
        """Classify one email dict with from/subject/body keys."""
        prompt = (
            "[TASK: EMAIL_TRIAGE]\n"
            "Classify this email as URGENT, ACTION, or FYI.\n"
            "Reply with exactly three lines:\n"
            "CATEGORY: <URGENT|ACTION|FYI>\n"
            "REASON: <one-line reason>\n"
            "DRAFT: <short reply draft, or N/A for FYI>\n"
            "[EMAIL]\n"
            f"From: {email.get('from', '')}\n"
            f"Subject: {email.get('subject', '')}\n"
            f"Body: {email.get('body', '')}\n"
            "[/EMAIL]"
        )
        response = self.llm.complete(prompt)
        result = {
            "from": email.get("from", ""),
            "subject": email.get("subject", ""),
            "category": "FYI",
            "reason": "",
            "draft_reply": None,
        }
        for line in response.splitlines():
            key, _, value = line.partition(":")
            key = key.strip().upper()
            value = value.strip()
            if key == "CATEGORY":
                result["category"] = value
            elif key == "REASON":
                result["reason"] = value
            elif key == "DRAFT" and value.upper() != "N/A":
                result["draft_reply"] = value
        return result

    def run(self, emails: list[dict]) -> list[dict]:
        """Classify a list of emails, one LLM call each."""
        return [self.classify(email) for email in emails]
