"""Project profiles.

A profile gives a project its voice: positioning, audience, key messages, and
hashtags. The same git diff is pitched differently per project, so this context
is injected into generation (and is a good prompt-cache target, since it is
stable across runs of the same project).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

# profiles/ lives at the repository root, two levels up from this file
# (src/media_engine/profiles.py -> repo root).
_DEFAULT_PROFILES_DIR = Path(__file__).resolve().parents[2] / "profiles"


class ProjectProfile(BaseModel):
    """Per-project context used to tailor generated content."""

    name: str
    positioning: str
    target_audience: str
    key_messages: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    # Language the generated content should be written in.
    language: str = "ja"
    tone: str | None = None


def render_profile_block(profile: ProjectProfile) -> str:
    """Render the profile as a system-prompt block (shared by generation steps)."""
    block = (
        "Project profile (use this to tailor tone and positioning):\n"
        f"- Name: {profile.name}\n"
        f"- Positioning: {profile.positioning}\n"
        f"- Target audience: {profile.target_audience}\n"
        "- Key messages:\n"
        + "".join(f"    - {m}\n" for m in profile.key_messages)
        + f"- Hashtags: {' '.join(profile.hashtags)}\n"
    )
    if profile.tone:
        block += f"- Tone: {profile.tone}\n"
    return block


def load_profile(project: str, profiles_dir: Path | None = None) -> ProjectProfile:
    """Load ``profiles/<project>.yaml``.

    Raises ``FileNotFoundError`` with a helpful message if the profile is missing.
    """
    directory = profiles_dir or _DEFAULT_PROFILES_DIR
    path = directory / f"{project}.yaml"
    if not path.exists():
        raise FileNotFoundError(
            f"No profile for project '{project}'. Expected: {path}. "
            f"Create it (see profiles/overseer.yaml for the format)."
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return ProjectProfile(**data)
