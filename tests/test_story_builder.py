"""Tests for Story building, experience-summary synthesis, and post assembly.

All offline — no network is used (the LLM calls are not exercised here).
"""

from datetime import datetime, timezone

import pytest

from media_engine.extract import experience_summary_builder
from media_engine.extract.story_builder import build_story
from media_engine.generate.generator import build_messages, parse_candidates
from media_engine.models import DevEvent, ExperienceSummary
from media_engine.profiles import ProjectProfile


def _events():
    return [
        DevEvent(
            project="overseer",
            timestamp=datetime(2026, 6, 1, tzinfo=timezone.utc),
            refs=["aaa111"],
            summary="Add WebSocket transport",
            detail="Files: agent/ws.py",
        ),
        DevEvent(
            project="overseer",
            timestamp=datetime(2026, 6, 2, tzinfo=timezone.utc),
            refs=["bbb222"],
            summary="Redact secrets in snapshots",
            detail="Files: backend/redact.py",
        ),
    ]


def _profile():
    return ProjectProfile(
        name="Overseer",
        positioning="Remote console",
        target_audience="devs",
        key_messages=["no terminal babysitting"],
        hashtags=["#ClaudeCode"],
        language="ja",
    )


def _summaries():
    return [
        ExperienceSummary(
            project="overseer",
            audience_lens="operator experience",
            headline="Confident remote use",
            before="You had to walk back to the PC to answer approval prompts.",
            after="You approve sessions from your phone, wherever you are.",
            experience="Glance at your phone, tap Y, stay in flow.",
            supporting_detail="OAuth retry, secure cookie, loopback restriction.",
            source_refs=["aaa111", "bbb222"],
        )
    ]


def test_build_story_bundles_events():
    story = build_story("overseer", _events())
    assert story.event_refs == ["aaa111", "bbb222"]
    assert "WebSocket" in story.material
    assert "Redact secrets" in story.material
    assert story.period_start < story.period_end


def test_build_story_rejects_empty():
    with pytest.raises(ValueError):
        build_story("overseer", [])


def test_experience_summary_messages_include_profile_and_caching():
    story = build_story("overseer", _events())
    system_blocks, messages = experience_summary_builder.build_messages(
        story, _profile()
    )
    assert any(b.get("cache_control") for b in system_blocks)
    assert any("Overseer" in b["text"] for b in system_blocks)
    assert "WebSocket" in messages[0]["content"]
    # The synthesis step must instruct grouping and a before -> after framing.
    assert "GROUP" in messages[0]["content"]
    assert "before -> after" in messages[0]["content"]


def test_parse_summaries_extracts_json():
    text = (
        'noise [{"headline": "h", "before": "b", "after": "a", '
        '"experience": "e", "supporting_detail": "d", '
        '"source_refs": ["aaa111"]}] tail'
    )
    summaries = experience_summary_builder.parse_summaries(text, project="overseer")
    assert len(summaries) == 1
    assert summaries[0].headline == "h"
    assert summaries[0].before == "b"
    assert summaries[0].after == "a"
    assert summaries[0].project == "overseer"


def test_post_messages_built_from_summaries():
    system_blocks, messages = build_messages(_summaries(), _profile(), count=3)
    assert any(b.get("cache_control") for b in system_blocks)
    content = messages[0]["content"]
    assert "Confident remote use" in content
    # The before -> after shift must reach the post prompt.
    assert "You had to walk back to the PC" in content
    assert "approve sessions from your phone" in content.lower()
    assert "3" in content


def test_parse_candidates_extracts_json():
    text = 'prose [{"angle": "a", "text": "t #x", "hashtags": ["#x"]}] trailing'
    out = parse_candidates(text)
    assert len(out) == 1
    assert out[0].text == "t #x"


def test_parse_candidates_rejects_non_json():
    with pytest.raises(ValueError):
        parse_candidates("no array here")
