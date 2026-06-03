"""Generate X post candidates from Launch Assets using the Claude API.

Posts are written from value themes (Launch Assets), not from raw commits — this
is what keeps the output from degrading into commit summaries.

Prompt caching is used on the system block (role instructions + the project
profile), which is stable across runs of the same project.
"""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from media_engine.models import LaunchAsset, XPostCandidate
from media_engine.profiles import ProjectProfile, render_profile_block

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_env = Environment(
    loader=FileSystemLoader(str(_PROMPTS_DIR)),
    autoescape=select_autoescape(enabled_extensions=()),
    trim_blocks=True,
    lstrip_blocks=True,
)

_SYSTEM_INSTRUCTIONS = (
    "You are a developer-marketing copywriter who writes X (Twitter) posts for "
    "individual developers announcing their own projects. You write in the voice "
    "of the developer: practical, confident, peer-to-peer, never hype. You lead "
    "with the value a feature unlocks or the pain it removes, never with "
    "implementation detail. You never invent features that are not supported by "
    "the provided launch assets."
)


def build_messages(
    assets: list[LaunchAsset], profile: ProjectProfile, count: int
) -> tuple[list[dict], list[dict]]:
    """Return (system_blocks, messages) for the Claude API.

    Separated from the API call so it can be inspected and tested without network.
    """
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

    template = _env.get_template("x_post.md.j2")
    user_text = template.render(
        assets=assets,
        count=count,
        language=profile.language,
        hashtags=profile.hashtags,
    )
    return system_blocks, [{"role": "user", "content": user_text}]


def generate_x_posts(
    assets: list[LaunchAsset],
    profile: ProjectProfile,
    count: int,
    *,
    model: str,
    api_key: str,
    client: object | None = None,
) -> list[XPostCandidate]:
    """Call Claude and return parsed X post candidates derived from the assets."""
    system_blocks, messages = build_messages(assets, profile, count)

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
    return parse_candidates(text)


def parse_candidates(text: str) -> list[XPostCandidate]:
    """Parse the model's JSON array of candidates, tolerantly."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"Model did not return a JSON array:\n{text}")
    data = json.loads(text[start : end + 1])
    return [XPostCandidate(**item) for item in data]
