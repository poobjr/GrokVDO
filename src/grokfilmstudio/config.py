"""
Configuration management for GrokFilmStudio.

Loads settings from environment variables and .env files.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Grok credentials
    grok_username: str = ""
    grok_password: str = ""

    # ElevenLabs API key
    elevenlabs_api_key: str = ""

    # Project configuration
    projects_dir: Path = Path("./projects")
    browser_headless: bool = True
    browser_type: str = "chromium"

    # Grok URL
    grok_base_url: str = "https://grok.x.ai"

    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: int = 5

    # Video generation timeout (seconds)
    video_gen_timeout: int = 300

    @property
    def auth_state_dir(self) -> Path:
        """Return the directory for storing browser auth state."""
        return Path("./playwright/.auth")

    @property
    def browser_storage_state(self) -> Path:
        """Return the path to the browser storage state file."""
        return self.auth_state_dir / "user.json"

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.auth_state_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()
