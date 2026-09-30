"""Run all three agents on the sample inputs.

Uses MockLLM, so this works fully offline with no API key:

    python examples/demo.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from workflow_agents import (
    DocSummarizerAgent,
    EmailTriageAgent,
    MeetingNotesAgent,
    MockLLM,
)

SAMPLES = Path(__file__).resolve().parent / "sample_inputs"


def section(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def main() -> None:
    llm = MockLLM()

    emails = json.loads((SAMPLES / "emails.json").read_text(encoding="utf-8"))
    triage = EmailTriageAgent(llm).run(emails)
    section("EMAIL TRIAGE")
    for item in triage:
        print(f"\n[{item['category']}] {item['subject']}")
        print(f"  Why: {item['reason']}")
        if item["draft_reply"]:
            print(f"  Draft reply: {item['draft_reply']}")

    transcript = (SAMPLES / "meeting.txt").read_text(encoding="utf-8")
    notes = MeetingNotesAgent(llm).run(transcript)
    section("MEETING NOTES")
    print(f"\nSummary: {notes['summary']}")
    print("\nDecisions:")
    for decision in notes["decisions"]:
        print(f"  - {decision}")
    print("\nAction items:")
    for action in notes["action_items"]:
        print(f"  - {action}")

    doc = (SAMPLES / "doc.md").read_text(encoding="utf-8")
    summary = DocSummarizerAgent(llm).run(doc)
    section("DOCUMENT SUMMARY")
    print(f"\nTL;DR: {summary['tldr']}")
    print("\nKey points:")
    for point in summary["key_points"]:
        print(f"  - {point}")
    print("\nOpen questions:")
    for question in summary["open_questions"]:
        print(f"  - {question}")

    print()


if __name__ == "__main__":
    main()
