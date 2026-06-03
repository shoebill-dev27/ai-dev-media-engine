"""Runtime configuration.

Settings are read from the environment (and a local ``.env`` file). Secrets must
never be hard-coded; ``ANTHROPIC_API_KEY`` is required only when actually calling
the model (not for ``--dry-run``).
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration loaded from environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_prefix="MEDIA_ENGINE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Read from the standard ANTHROPIC_API_KEY name (the env_prefix does not apply
    # to fields with an explicit alias).
    anthropic_api_key: str | None = Field(
        default=None, validation_alias="ANTHROPIC_API_KEY"
    )

    # Default generation model. Sonnet is the default for short, frequently
    # generated X posts (good quality at lower cost); override per run via
    # MEDIA_ENGINE_MODEL.
    model: str = "claude-sonnet-4-6"

    # Hard cap on diff characters per commit sent to the model (token control).
    max_diff_chars: int = 4000


def load_settings() -> Settings:
    """Return process settings."""
    return Settings()
