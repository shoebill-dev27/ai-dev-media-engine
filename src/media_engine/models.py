"""Core data models for the pipeline.

The flow is: ``RawCommit`` -> ``DevEvent`` -> ``Story`` -> ``ExperienceSummary``
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


class ExperienceSummary(BaseModel):
    """The unit between ``Story`` and ``Draft``: one user-facing change, framed
    as experience rather than implementation.

    Each summary expresses a single change as a ``before`` -> ``after`` shift and
    the ``experience`` it unlocks for the audience (player / user /
    decision-maker, per the project's audience lens). The implementation behind
    it is kept only as a subordinate ``supporting_detail``. Changes that cannot be
    translated into audience value are dropped before this stage, so every summary
    here is worth communicating.
    """

    project: str
    audience_lens: str = ""
    headline: str = ""
    before: str = ""
    after: str = ""
    experience: str = ""
    supporting_detail: str = ""
    source_refs: list[str] = Field(default_factory=list)


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
