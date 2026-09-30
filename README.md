# workflow-agents

[![CI](https://github.com/balajeeasish/workflow-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/balajeeasish/workflow-agents/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Small, readable custom agents for everyday workflows: email triage, meeting notes, and document summarization. Python standard library only, no third-party dependencies.

## Quickstart (under 5 minutes)

Clone, run the demo. No API key, no network, no install step beyond Python 3.10:

```bash
git clone https://github.com/balajeeasish/workflow-agents.git
cd workflow-agents
python examples/demo.py
```

The demo runs all three agents on the sample inputs in `examples/sample_inputs/` using `MockLLM`, a deterministic offline stand-in for a real model.

You can also use the package from your own code:

```python
import sys
sys.path.insert(0, "src")

from workflow_agents import EmailTriageAgent, MockLLM

agent = EmailTriageAgent(MockLLM())
results = agent.run([
    {"from": "oncall@example.com", "subject": "SEV1: checkout is down", "body": "Payments are failing for all users."},
])
print(results[0]["category"])  # URGENT
```

## Example output

```
============================================================
EMAIL TRIAGE
============================================================

[URGENT] SEV1: checkout is down in prod
  Why: signals an incident or outage that needs immediate attention
  Draft reply: Acknowledged, investigating now and will post an update within 15 minutes.

[ACTION] Please review the Q4 launch plan
  Why: asks for a review, approval, or delivery by a deadline
  Draft reply: On it. I will review this and get back to you with an update.

[FYI] Weekly tech digest
  Why: informational, no action required

============================================================
MEETING NOTES
============================================================

Summary: Morning everyone. Quick standup. The deploy is still blocked on the load test results from last night. ...

Decisions:
  - We will rerun the load tests tonight and deploy Thursday morning.
  - We will tune the alert thresholds before the next deploy so the on-call stops getting woken up.

Action items:
  - Meera to publish the release notes by end of day.
  - Priya to confirm the rollback plan with the infra team before Thursday.

============================================================
DOCUMENT SUMMARY
============================================================

TL;DR: The Phoenix cache refresh project replaces our nightly batch cache rebuild with an event-driven refresh pipeline, cutting stale data windows from 6 hours to under 5 minutes.

Key points:
  - Goals
  - Risks
  - Timeline
  - Cut the stale data window to under 5 minutes.
  - Remove the nightly batch job entirely.

Open questions:
  - Open questions: Who owns the on-call rotation for the new pipeline? Should we backfill historical data or start fresh?
```

## Architecture

```
src/workflow_agents/
  base.py        Agent base class: build prompt -> LLM -> parse tool calls -> execute -> observe
  llm.py         LLMClient protocol, OpenAICompatibleClient (stdlib urllib), MockLLM (offline)
  tools.py       read_file / write_file sandboxed to a workspace dir, plus word_count
  agents/
    email_triage.py    URGENT / ACTION / FYI classification with reasons and reply drafts
    meeting_notes.py   transcript -> summary, decisions, action items with owners
    doc_summarizer.py  long text -> TL;DR, key points, open questions
```

The loop is intentionally small. `Agent.run()` builds a prompt from the task and the tool descriptions, asks the LLM for the next step, and executes lines like `CALL: word_count(some text)`. Observations go back into the prompt until the model returns a final answer or `max_steps` is reached. The concrete agents build on the same `LLMClient` protocol, so every agent works with any model client.

`MockLLM` dispatches on `[TASK: ...]` markers and answers with simple keyword heuristics. It is deterministic: the same prompt always returns the same answer, which makes the demo, the docs, and the regression tests reproducible.

## Plugging in a real model

`MockLLM` is for demos and tests. For real answers, use `OpenAICompatibleClient`:

```python
from workflow_agents import EmailTriageAgent, OpenAICompatibleClient

llm = OpenAICompatibleClient(model="gpt-4o-mini")  # reads OPENAI_API_KEY
agent = EmailTriageAgent(llm)
```

Any OpenAI-compatible endpoint works by overriding `base_url` and `model`. To use a different provider, implement the `LLMClient` protocol: one method, `complete(prompt) -> str`.

## Roadmap

- Priority inbox agent that reads a mailbox and produces a morning brief
- Calendar agent that turns a week of invites into a prep sheet
- A small eval harness so agent changes are tested before they ship (see the sibling `agent-evals` repo)
- Streaming output for long documents

## Contributing

Issues and pull requests are welcome. Keep the stdlib-only rule: if a feature needs a third-party package, open an issue first so we can discuss it. Add a test in `tests/` for every new agent behavior and run `python -m pytest -q` before pushing.

## License

MIT. See [LICENSE](LICENSE).
