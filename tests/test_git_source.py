"""Tests for the git source adapter against a real temporary repo."""

import subprocess
from pathlib import Path

import pytest

from media_engine.normalize.normalizer import to_dev_events
from media_engine.sources.git_source import GitSource


def _run(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _run(tmp_path, "init", "-q")
    _run(tmp_path, "config", "user.email", "t@example.com")
    _run(tmp_path, "config", "user.name", "Tester")
    (tmp_path / "file.txt").write_text("hello\n")
    _run(tmp_path, "add", ".")
    _run(tmp_path, "commit", "-q", "-m", "Add greeting feature")
    return tmp_path


def test_rejects_non_repo(tmp_path: Path):
    with pytest.raises(ValueError):
        GitSource(tmp_path / "nope")


def test_collect_reads_commit(repo: Path):
    commits = GitSource(repo).collect(since="1 year ago", max_items=10)
    assert len(commits) == 1
    c = commits[0]
    assert c.subject == "Add greeting feature"
    assert "file.txt" in c.files_changed
    assert c.sha


def test_diff_is_truncated(repo: Path):
    (repo / "big.txt").write_text("x" * 10000 + "\n")
    _run(repo, "add", ".")
    _run(repo, "commit", "-q", "-m", "Add big file")
    commits = GitSource(repo, max_diff_chars=200).collect(
        since="1 year ago", max_items=10
    )
    big = next(c for c in commits if c.subject == "Add big file")
    assert "[diff truncated]" in big.diff


def test_normalizer_produces_events(repo: Path):
    commits = GitSource(repo).collect(since="1 year ago", max_items=10)
    events = to_dev_events("demo", commits)
    assert len(events) == 1
    assert events[0].summary == "Add greeting feature"
    assert events[0].project == "demo"
