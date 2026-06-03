"""Secret redaction.

Runs on every piece of text before it reaches the LLM or is written out. This is
the MVP-level redaction baseline (commit messages + diffs); it is intentionally
conservative — it prefers to over-mask rather than leak. Transcript-grade
redaction is expanded in M1.
"""

from __future__ import annotations

import re

_PLACEHOLDER = "[REDACTED]"

# Order matters a little: block patterns (private keys) first.
_PATTERNS: list[re.Pattern[str]] = [
    # PEM private key blocks (multi-line).
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
    # Anthropic / OpenAI style keys.
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    # AWS access key id.
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # GitHub tokens.
    re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"),
    # Slack tokens.
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"),
    # Bearer tokens in headers.
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
]

# key = value / key: value where the key name looks sensitive.
_KV_PATTERN = re.compile(
    r"(?i)\b("
    r"api[_-]?key|secret[_-]?key|secret|token|access[_-]?token|"
    r"password|passwd|pwd|private[_-]?key|client[_-]?secret|auth[_-]?token"
    r")\b(\s*[:=]\s*)(['\"]?)([^\s'\"]{6,})\3"
)


def redact(text: str) -> str:
    """Return ``text`` with likely secrets replaced by ``[REDACTED]``."""
    if not text:
        return text
    for pattern in _PATTERNS:
        text = pattern.sub(_PLACEHOLDER, text)
    text = _KV_PATTERN.sub(rf"\1\2\3{_PLACEHOLDER}\3", text)
    return text
