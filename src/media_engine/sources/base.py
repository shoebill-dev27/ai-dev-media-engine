"""Source adapter interface.

A source adapter reads development activity from somewhere (git for the MVP;
later: Claude transcripts, GitHub PRs/Issues) and yields ``RawCommit``-shaped
material. The interface is deliberately small so that cognitive-memory can later
implement the same contract and be swapped in (loose coupling, see design).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from media_engine.models import RawCommit


class SourceAdapter(ABC):
    """Reads raw development activity for a project."""

    @abstractmethod
    def collect(self, since: str, max_items: int) -> list[RawCommit]:
        """Return raw activity items, newest first.

        ``since`` is a human/git-friendly window (e.g. ``"7 days ago"``).
        """
        raise NotImplementedError
