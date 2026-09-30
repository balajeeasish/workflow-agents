"""workflow-agents: small, readable custom agents for everyday workflows."""

from .agents import DocSummarizerAgent, EmailTriageAgent, MeetingNotesAgent
from .base import Agent
from .llm import LLMClient, MockLLM, OpenAICompatibleClient
from .tools import ToolError, make_file_tools

__all__ = [
    "Agent",
    "DocSummarizerAgent",
    "EmailTriageAgent",
    "LLMClient",
    "MeetingNotesAgent",
    "MockLLM",
    "OpenAICompatibleClient",
    "ToolError",
    "make_file_tools",
]

__version__ = "0.1.0"
