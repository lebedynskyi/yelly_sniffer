from typing import Literal, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    model_config = SettingsConfigDict(populate_by_name=True)

    provider: Literal["openai", "gemini", "ollama"] = Field(validation_alias="AI_PROVIDER")

    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    gemini_model: str = Field(default="gemini-2.0-flash", validation_alias="GEMINI_MODEL")
    ollama_model: str = Field(default="llama3", validation_alias="OLLAMA_MODEL")

    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    ollama_base_url: str = Field(
        default="http://localhost:11434", validation_alias="OLLAMA_BASE_URL"
    )
    ollama_startup_timeout_seconds: float = Field(
        default=15.0, validation_alias="OLLAMA_STARTUP_TIMEOUT"
    )

    @model_validator(mode="after")
    def _require_secret_for_selected_provider(self) -> "AISettings":
        if self.provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when AI_PROVIDER=openai")
        if self.provider == "gemini" and not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required when AI_PROVIDER=gemini")
        return self
