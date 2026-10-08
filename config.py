from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ASR
    sarvam_api_key: str = ""

    # LLM
    gemini_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b-instruct-q4_K_M"

    # Supabase
    supabase_url: str = ""
    supabase_key: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    confidence_threshold: float = 0.70
    max_audio_size_mb: int = 50

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
