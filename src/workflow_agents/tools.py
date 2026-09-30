"""Sandboxed tools: file reads/writes confined to a workspace directory.

The point is safety by construction: an agent can read and write files,
but only inside the workspace you hand it. Anything that tries to escape
(absolute paths, ".." tricks) is rejected with a ToolError.
"""

from __future__ import annotations

import os
from typing import Any, Callable


class ToolError(Exception):
    """Raised when a tool call is unsafe or invalid."""


def make_file_tools(workspace: str) -> dict[str, Callable[..., Any]]:
    """Build read_file/write_file tools sandboxed to a workspace directory.

    Paths are resolved inside the workspace; anything escaping it
    (for example "../secret.txt" or an absolute path) is rejected.
    Also includes a word_count helper for the loop demos.
    """
    root = os.path.abspath(workspace)
    os.makedirs(root, exist_ok=True)

    def _resolve(path: str) -> str:
        full = os.path.abspath(os.path.join(root, path))
        if full != root and not full.startswith(root + os.sep):
            raise ToolError(f"Blocked: {path!r} escapes the workspace")
        return full

    def read_file(path: str) -> str:
        """Read a text file inside the workspace and return its contents."""
        with open(_resolve(path), encoding="utf-8") as handle:
            return handle.read()

    def write_file(path: str, content: str) -> str:
        """Write text to a file inside the workspace, creating folders as needed."""
        full = _resolve(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(content)
        return f"Wrote {len(content)} characters to {path}"

    def word_count(text: str) -> int:
        """Count the words in a string."""
        return len(text.split())

    return {
        "read_file": read_file,
        "write_file": write_file,
        "word_count": word_count,
    }
