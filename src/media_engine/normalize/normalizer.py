"""Normalize RawCommits into redacted DevEvents."""

from __future__ import annotations

from media_engine.models import DevEvent, RawCommit
from media_engine.normalize.redaction import redact


def to_dev_events(project: str, commits: list[RawCommit]) -> list[DevEvent]:
    """Convert raw commits into redacted DevEvents.

    Subject, body, and diff are all passed through redaction before being stored
    on the event, so nothing downstream (including the LLM) sees raw secrets.
    """
    events: list[DevEvent] = []
    for c in commits:
        detail_parts = []
        if c.body:
            detail_parts.append(redact(c.body))
        if c.files_changed:
            detail_parts.append("Files: " + ", ".join(c.files_changed))
        if c.diff:
            detail_parts.append("Diff:\n" + redact(c.diff))
        events.append(
            DevEvent(
                project=project,
                type="commit",
                timestamp=c.date,
                refs=[c.sha],
                summary=redact(c.subject),
                detail="\n\n".join(detail_parts),
            )
        )
    return events
