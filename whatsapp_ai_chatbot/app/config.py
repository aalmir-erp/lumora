from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Meta WhatsApp Cloud API
    meta_access_token: str = ""
    meta_phone_number_id: str = ""
    meta_waba_id: str = ""
    meta_app_secret: str = ""
    meta_verify_token: str = "change-me"
    meta_graph_version: str = "v21.0"

    # AI provider selection
    ai_provider: Literal["anthropic", "openai"] = "anthropic"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_max_tokens: int = 1024

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1"
    openai_max_tokens: int = 1024

    # App behaviour
    allowed_numbers: str = ""
    handoff_whatsapp: str = ""
    handoff_email: str = ""
    history_turns: int = Field(default=12, ge=1, le=64)
    redis_url: str = ""
    log_level: str = "info"

    @property
    def allowed_number_set(self) -> set[str]:
        return {n.strip().lstrip("+") for n in self.allowed_numbers.split(",") if n.strip()}


settings = Settings()
