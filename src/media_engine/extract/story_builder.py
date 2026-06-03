"""Build a Story from DevEvents.

For the MVP this bundles all events in the window into a single Story; the model
performs the "what/why" synthesis at generation time. The design intent is that a
``LaunchAsset`` layer (see models) later sits between Story and Draft to make the
"what was achieved / why" explicit — that is out of MVP scope.
"""

from __future__ import annotations

from media_engine.models import DevEvent, Story


def build_story(project: str, events: list[DevEvent]) -> Story:
    """Bundle DevEvents (newest first) into one Story for the window."""
    if not events:
        raise ValueError("Cannot build a Story from zero events.")

    timestamps = [e.timestamp for e in events]
    refs: list[str] = []
    blocks: list[str] = []
    for e in events:
        refs.extend(e.refs)
        header = f"- {e.summary}"
        if e.detail:
            header += "\n" + _indent(e.detail)
        blocks.append(header)

    return Story(
        project=project,
        period_start=min(timestamps),
        period_end=max(timestamps),
        event_refs=refs,
        material="\n\n".join(blocks),
    )


def _indent(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())
