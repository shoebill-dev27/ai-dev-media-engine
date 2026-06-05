"""Write a Draft to a reviewable Markdown file with YAML front-matter."""

from __future__ import annotations

from pathlib import Path

import yaml

from media_engine.models import Draft

_DEFAULT_DRAFTS_DIR = Path(__file__).resolve().parents[3] / "drafts"


def write_draft(draft: Draft, drafts_dir: Path | None = None) -> Path:
    """Write ``draft`` to ``drafts/<project>-<type>-<timestamp>.md`` and return it."""
    directory = drafts_dir or _DEFAULT_DRAFTS_DIR
    directory.mkdir(parents=True, exist_ok=True)

    stamp = draft.created_at.strftime("%Y%m%d-%H%M%S")
    path = directory / f"{draft.project}-{draft.content_type}-{stamp}.md"

    front_matter = yaml.safe_dump(
        {
            "project": draft.project,
            "content_type": draft.content_type,
            "status": draft.status,
            "created_at": draft.created_at.isoformat(),
            "themes": draft.themes,
            "source_refs": draft.source_refs,
        },
        sort_keys=False,
        allow_unicode=True,
    )

    lines = ["---", front_matter.strip(), "---", ""]
    lines.append(f"# {draft.project} — X post candidates\n")

    if draft.themes:
        lines.append("**Experience themes:**\n")
        for theme in draft.themes:
            lines.append(f"- {theme}")
        lines.append("")

    # The post text already includes its hashtags inline; do not append them again.
    for i, c in enumerate(draft.candidates, start=1):
        lines.append(f"## Candidate {i}: {c.angle}\n")
        lines.append(c.text)
        lines.append(f"\n_{len(c.text)} chars_\n")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
