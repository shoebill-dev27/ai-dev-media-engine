"""Core data models for the pipeline.

The flow is: ``RawCommit`` -> ``DevEvent`` -> ``Story`` -> (design: ``LaunchAsset``)
-> ``Draft``. Everything is plain pydantic so it stays serializable and testable.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RawCommit(BaseModel):
    """A single commit as read from git, before normalization/redaction."""

    sha: str
    author: str
    date: datetime
    subject: str
    body: str = ""
    files_changed: list[str] = Field(default_factory=list)
    diff: str = ""


class DevEvent(BaseModel):
    """A normalized, redacted unit of development activity.

    For the MVP the only ``type`` is ``commit``; the field exists so transcript
    and github events can be added later without changing the shape.
    """

    project: str
    type: Literal["commit"] = "commit"
    timestamp: datetime
    refs: list[str] = Field(default_factory=list)
    summary: str
    detail: str = ""


class Story(BaseModel):
    """A bundle of DevEvents over a window — the material handed to generation."""

    project: str
    period_start: datetime
    period_end: datetime
    event_refs: list[str] = Field(default_factory=list)
    # The theme/why is synthesized by the model; left empty by the MVP builder.
    theme: str = ""
    material: str = ""


class LaunchAsset(BaseModel):
    """Design-only placeholder (NOT used by the MVP pipeline).

    The intended layer between ``Story`` and ``Draft``: it captures *what was
    achieved* and *why it was built*, rather than a list of commits. Readers care
    about this unit, not the raw activity. Documented here so the data flow is
    explicit; generation does not depend on it yet.
    """

    project: str
    headline: str = ""
    what_achieved: str = ""
    why_built: str = ""
    source_story_refs: list[str] = Field(default_factory=list)


class XPostCandidate(BaseModel):
    """One candidate X post."""

    angle: str
    text: str
    hashtags: list[str] = Field(default_factory=list)


class Draft(BaseModel):
    """A reviewable draft. For the MVP this holds X post candidates."""

    project: str
    content_type: Literal["x_post"] = "x_post"
    status: Literal["draft", "approved", "published"] = "draft"
    created_at: datetime
    source_refs: list[str] = Field(default_factory=list)
    # Headlines of the Launch Assets the posts were derived from (for transparency).
    themes: list[str] = Field(default_factory=list)
    candidates: list[XPostCandidate] = Field(default_factory=list)
