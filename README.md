# AI Development Media Engine

Turn development activity into reviewable social-media drafts. The human approves
only — the machine collects, extracts, and drafts.

> This is **not** an article-generation tool. The goal is to automatically convert
> the knowledge, decisions, and implementation produced by development into content
> assets, so that the developer only performs the final approval.

## Why this exists

Development output exists (code, READMEs, designs) but it is rarely turned into
posts (X, Zenn, note, release notes, weekly reports). The result is real work that
nobody knows about. This engine closes that gap.

The differentiator is **WHY**, not **WHAT**. A normal AI writing tool only sees a
diff (what changed). This engine is designed to also use commit messages, PRs, and
Claude Code transcripts (the *why* and the trial-and-error) — so it can write posts
that explain what was achieved and why it was built.

## Pipeline

```
[Sources]        [Core]                                  [Output]
 git ──┐
 (M1) transcript ─┤→ collect → normalize → DevEvent → Story → (design: Launch Asset) → generate → Draft → Review
 (M2) github ─────┘            (redaction)                                              (Claude)  (Markdown) (human)
```

- **DevEvent**: a normalized unit of activity (one commit, for MVP).
- **Story**: a bundle of DevEvents over a window — material for generation.
- **Launch Asset** *(design only, not in MVP)*: the "what was achieved / why it was
  built" unit derived from a Story. Readers care about this, not a list of commits.
- **Draft**: a reviewable Markdown file with front-matter and candidate posts.

`normalize` always runs **redaction** before any text reaches the LLM.

## MVP scope

The MVP success condition is: **"can generate X post drafts from a project's git
history."** Concretely, from the Overseer repository.

Generation priority: **1) X posts → 2) Daily Summary → 3) Weekly Summary.**

- Input: `git log` / `git diff` / commit messages of one project.
- Project context comes from `profiles/<project>.yaml`.
- Output: `drafts/<project>-x-<timestamp>.md` (front-matter + candidate posts).
- The MVP runs the pipeline in memory (no database yet).

Out of MVP (later milestones): transcript ingestion, GitHub PR/Issue, multi-platform
posting, a database-backed review workflow, performance feedback.

## Usage

```sh
# Install (editable, with dev tools)
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

# Configure
cp .env.example .env   # set ANTHROPIC_API_KEY

# Generate X post drafts from Overseer's last 7 days of commits
media-engine generate-x \
    --project overseer \
    --repo /path/to/overseer \
    --since "7 days ago" \
    --count 3

# Inspect the assembled material without calling the API
media-engine generate-x --project overseer --repo ../overseer --dry-run
```

## Project profiles

Each project has a profile under `profiles/`. The same diff is pitched differently
for Overseer vs. Agent Pager vs. MarketMythos, so the profile carries positioning,
audience, key messages, and hashtags. See `profiles/overseer.yaml`.

## Roadmap

| Milestone | Content |
|-----------|---------|
| **M0 (MVP)** | git → **X post drafts** (then Daily / Weekly), single project, CLI, redaction on |
| **M1 (moat)** | Transcript / design-discussion ingestion → Zenn drafts that carry the *why* |
| **M2** | GitHub PR/Issue → Release Notes / Project Timeline |
| **M3** | Multi-project + DB-backed review workflow (draft/approved/published) |
| **M4** | Integrations: cognitive-memory as a source, agent-pager triggers collection, overseer hosts the approval UI |
| **M5** | Auto-publish approved content (X / Zenn / note APIs) |
| **M6** | **Performance feedback**: record which posts/themes performed, feed back into generation |

## Development

```sh
ruff check . && black --check . && pytest
```

## Status

Early MVP. The git → X post path works end-to-end; transcript/GitHub sources,
auto-publishing, and a database-backed review workflow are on the roadmap above.

## License

MIT — see [LICENSE](LICENSE).
