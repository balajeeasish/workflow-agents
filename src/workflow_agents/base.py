"""A minimal tool-using agent loop."""

from __future__ import annotations

import ast
import re
from typing import Any, Callable

from .llm import LLMClient

TOOL_CALL_PATTERN = re.compile(r"^CALL:\s*([A-Za-z_][A-Za-z0-9_]*)\((.*)\)\s*$")


def parse_args(arg_string: str) -> list:
    """Parse a comma-separated argument string into Python values.

    Tries literal evaluation first (so numbers, strings, and lists work),
    and falls back to treating the whole string as one argument.
    """
    arg_string = arg_string.strip()
    if not arg_string:
        return []
    try:
        return list(ast.literal_eval(f"({arg_string},)"))
    except (SyntaxError, ValueError):
        return [arg_string]


class Agent:
    """Base class for tool-using agents.

    The loop is deliberately small so the whole thing fits in your head:

      build prompt -> ask LLM -> parse tool calls -> execute -> observe

    It repeats until the LLM returns a final answer or max_steps is hit.
    Subclasses usually override run() with task-specific logic.
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: dict[str, Callable[..., Any]] | None = None,
        max_steps: int = 8,
    ):
        self.llm = llm
        self.tools = tools or {}
        self.max_steps = max_steps
        self.name = "Agent"

    def describe_tools(self) -> str:
        if not self.tools:
            return "No tools available."
        lines = [
            "Available tools (call one with a line like CALL: tool_name(arg1, arg2)):"
        ]
        for name, fn in self.tools.items():
            doc = (fn.__doc__ or "").strip().splitlines()
            lines.append(f"- {name}: {doc[0] if doc else 'no description'}")
        return "\n".join(lines)

    def build_prompt(self, task: str, history: list[tuple[str, list, Any]]) -> str:
        parts = [
            "[TASK: AGENT_LOOP]",
            f"You are {self.name}.",
            self.describe_tools(),
            f"Task: {task}",
            "Think step by step. To use a tool, write CALL: name(args) on its own line.",
            "When you are done, write your final answer starting with FINAL:.",
        ]
        for tool_name, args, observation in history:
            parts.append(f"OBSERVATION: {tool_name}{tuple(args)} -> {observation}")
        return "\n".join(parts)

    def parse_tool_calls(self, response: str) -> list[tuple[str, list]]:
        calls = []
        for line in response.splitlines():
            match = TOOL_CALL_PATTERN.match(line.strip())
            if match:
                calls.append((match.group(1), parse_args(match.group(2))))
        return calls

    def execute_tool(self, name: str, args: list) -> Any:
        if name not in self.tools:
            return f"Error: unknown tool '{name}'"
        try:
            return self.tools[name](*args)
        except Exception as exc:  # keep the loop alive on tool errors
            return f"Error: {exc}"

    def run(self, task: str) -> str:
        """Run the generic prompt -> tool -> observe loop on a task."""
        history: list[tuple[str, list, Any]] = []
        for _ in range(self.max_steps):
            prompt = self.build_prompt(task, history)
            response = self.llm.complete(prompt).strip()
            calls = self.parse_tool_calls(response)
            if not calls:
                return response
            for name, args in calls:
                history.append((name, args, self.execute_tool(name, args)))
        return "Stopped: reached max_steps without a final answer."
