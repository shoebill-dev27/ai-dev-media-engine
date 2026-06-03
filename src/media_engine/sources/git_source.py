"""Git source adapter.

Reads commit metadata and (truncated) diffs from a local repository using the
``git`` CLI. Diffs are capped per commit to keep token usage bounded.
"""

from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path

from media_engine.models import RawCommit
from media_engine.sources.base import SourceAdapter

# Field separator (unit sep) and record separator within the log format.
_FS = "\x1f"
_RS = "\x1e"
_LOG_FORMAT = _FS.join(["%H", "%an", "%aI", "%s", "%b"]) + _RS


class GitSource(SourceAdapter):
    """Reads commits from a local git repository."""

    def __init__(self, repo_path: str | Path, max_diff_chars: int = 4000) -> None:
        self.repo_path = Path(repo_path).expanduser().resolve()
        self.max_diff_chars = max_diff_chars
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.repo_path), *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def collect(self, since: str, max_items: int) -> list[RawCommit]:
        out = self._git(
            "log",
            f"--since={since}",
            f"--max-count={max_items}",
            f"--pretty=format:{_LOG_FORMAT}",
        )
        commits: list[RawCommit] = []
        for record in out.split(_RS):
            record = record.strip("\n")
            if not record:
                continue
            sha, author, date_iso, subject, body = record.split(_FS)
            files, diff = self._show(sha)
            commits.append(
                RawCommit(
                    sha=sha,
                    author=author,
                    date=datetime.fromisoformat(date_iso),
                    subject=subject,
                    body=body.strip(),
                    files_changed=files,
                    diff=diff,
                )
            )
        return commits

    def _show(self, sha: str) -> tuple[list[str], str]:
        """Return (files_changed, truncated_diff) for a commit."""
        files_out = self._git(
            "show", "--no-color", "--name-only", "--pretty=format:", sha
        )
        files = [line for line in files_out.splitlines() if line.strip()]

        diff_out = self._git("show", "--no-color", "--pretty=format:", sha)
        if len(diff_out) > self.max_diff_chars:
            diff_out = diff_out[: self.max_diff_chars] + "\n... [diff truncated]"
        return files, diff_out
