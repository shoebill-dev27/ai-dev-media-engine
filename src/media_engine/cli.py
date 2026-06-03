"""Command-line interface.

The MVP exposes one command, ``generate-x``: read a project's recent git history,
normalize + redact it, build a Story, and generate X post candidates as a
reviewable Markdown draft.
"""

from __future__ import annotations

from datetime import datetime, timezone

import typer

from media_engine.config import load_settings
from media_engine.extract import launch_asset_builder
from media_engine.extract.story_builder import build_story
from media_engine.generate.generator import generate_x_posts
from media_engine.models import Draft
from media_engine.normalize.normalizer import to_dev_events
from media_engine.profiles import load_profile
from media_engine.review.draft_writer import write_draft
from media_engine.sources.git_source import GitSource

app = typer.Typer(
    add_completion=False,
    help="Turn development activity into reviewable social-media drafts.",
)


@app.callback()
def _main() -> None:
    """Force subcommand mode so commands like ``generate-x`` are used by name."""


@app.command("generate-x")
def generate_x(
    project: str = typer.Option(
        ..., help="Project name (matches profiles/<name>.yaml)."
    ),
    repo: str = typer.Option(..., help="Path to the project's git repository."),
    since: str = typer.Option("7 days ago", help="Git time window for commits."),
    count: int = typer.Option(3, help="Number of X post candidates to generate."),
    max_commits: int = typer.Option(50, help="Max commits to read from the window."),
    dry_run: bool = typer.Option(
        False, help="Assemble and print the prompt without calling the API."
    ),
) -> None:
    """Generate X post candidates from a project's recent git history."""
    settings = load_settings()
    profile = load_profile(project)

    source = GitSource(repo, max_diff_chars=settings.max_diff_chars)
    commits = source.collect(since=since, max_items=max_commits)
    if not commits:
        typer.secho(
            f"No commits found in '{repo}' since '{since}'. Nothing to generate.",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(code=1)

    events = to_dev_events(project, commits)
    story = build_story(project, events)

    if dry_run:
        # Show the first step (Commit群 -> Launch Asset); posts are written from
        # the assets, which require a live call.
        system_blocks, messages = launch_asset_builder.build_messages(story, profile)
        typer.echo("=== SYSTEM (launch-asset step) ===")
        for block in system_blocks:
            typer.echo(block["text"])
            typer.echo("")
        typer.echo("=== USER (launch-asset step) ===")
        typer.echo(messages[0]["content"])
        typer.secho(
            f"\n[dry-run] {len(commits)} commit(s) bundled; no API call made.",
            fg=typer.colors.CYAN,
        )
        return

    if not settings.anthropic_api_key:
        typer.secho(
            "ANTHROPIC_API_KEY is not set. Set it in .env (see .env.example) or "
            "use --dry-run.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    # Step 1: Commit群 -> Launch Asset (value themes).
    assets = launch_asset_builder.build_launch_assets(
        story,
        profile,
        model=settings.model,
        api_key=settings.anthropic_api_key,
    )
    # Step 2: Launch Asset -> Post.
    candidates = generate_x_posts(
        assets,
        profile,
        count,
        model=settings.model,
        api_key=settings.anthropic_api_key,
    )

    draft = Draft(
        project=project,
        content_type="x_post",
        created_at=datetime.now(timezone.utc),
        source_refs=story.event_refs,
        themes=[a.headline for a in assets],
        candidates=candidates,
    )
    path = write_draft(draft)
    typer.secho(
        f"Wrote {len(candidates)} X post candidate(s) to {path}", fg=typer.colors.GREEN
    )


if __name__ == "__main__":
    app()
