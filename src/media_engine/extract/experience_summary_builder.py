"""Experience Summary layer.

Sits between Story and post generation: instead of going commit -> post (which
yields commit summaries), the model first synthesizes the activity into a few
"experience summaries" — single user-facing changes, each expressed as a
``before`` -> ``after`` shift and the experience it unlocks for the audience.
Posts are then written from these summaries, not from raw commits.

This is the minimal, MVP-level realization of ``Commit群 -> Experience Summary
-> Post``: the launch-asset grouping (group related commits, drop noise) survives
as the front half of this single synthesis step, so no extra model call is added.
"""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from media_engine.models import ExperienceSummary, Story
from media_engine.profiles import ProjectProfile, render_profile_block

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_env = Environment(
    loader=FileSystemLoader(str(_PROMPTS_DIR)),
    autoescape=select_autoescape(enabled_extensions=()),
    trim_blocks=True,
    lstrip_blocks=True,
)

_SYSTEM_INSTRUCTIONS = (
    "You turn a developer's raw commit history into a few user-facing CHANGES, "
    "each framed as experience rather than implementation. You group related "
    "commits, discard noise, and adopt the project's audience lens (player / "
    "user / decision-maker). For every change you make the shift explicit as a "
    "before -> after pair and name the experience it unlocks. If a change cannot "
    "be translated into audience value, you drop it. You never invent "
    "capabilities that are not supported by the activity."
)


def build_messages(
    story: Story, profile: ProjectProfile
) -> tuple[list[dict], list[dict]]:
    """Return (system_blocks, messages) for the experience-summary synthesis step."""
    system_blocks = [
        {
            "type": "text",
            "text": _SYSTEM_INSTRUCTIONS,
            "cache_control": {"type": "ephemeral"},
        },
        {
            "type": "text",
            "text": render_profile_block(profile),
            "cache_control": {"type": "ephemeral"},
        },
    ]
    template = _env.get_template("experience_summary.md.j2")
    user_text = template.render(
        period_start=story.period_start.isoformat(),
        period_end=story.period_end.isoformat(),
        material=story.material,
    )
    return system_blocks, [{"role": "user", "content": user_text}]


def build_experience_summaries(
    story: Story,
    profile: ProjectProfile,
    *,
    model: str,
    api_key: str,
    client: object | None = None,
) -> list[ExperienceSummary]:
    """Call Claude to synthesize the Story into a few ExperienceSummaries."""
    system_blocks, messages = build_messages(story, profile)

    if client is None:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=model,
        max_tokens=2048,
        system=system_blocks,
        messages=messages,
    )
    text = "".join(b.text for b in response.content if getattr(b, "type", "") == "text")
    return parse_summaries(text, project=story.project)


def parse_summaries(text: str, project: str) -> list[ExperienceSummary]:
    """Parse the model's JSON array of experience summaries, tolerantly."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"Model did not return a JSON array:\n{text}")
    data = json.loads(text[start : end + 1])
    return [ExperienceSummary(project=project, **item) for item in data]
