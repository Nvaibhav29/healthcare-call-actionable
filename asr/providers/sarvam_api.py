"""
Sarvam AI ASR provider.
Primary ASR — handles Indian languages + code-mixing natively.
Docs: https://docs.sarvam.ai/api-reference-docs/speech-to-text
"""
import httpx
import os
from config import get_settings


SARVAM_ASR_URL = "https://api.sarvam.ai/speech-to-text"

# Language codes supported by Sarvam
# Use "unknown" to let Sarvam auto-detect
LANGUAGE_MAP = {
    "hi": "hi-IN",
    "kn": "kn-IN",
    "en": "en-IN",
    "ta": "ta-IN",
    "te": "te-IN",
    "ml": "ml-IN",
    "auto": "unknown",
}


def transcribe(audio_path: str, language: str = "auto") -> dict:
    """
    Transcribe audio using Sarvam AI API.

    Returns:
        {
            "transcript": str,
            "language_code": str,
            "provider": "sarvam"
        }

    Raises:
        Exception on API failure (caller handles fallback).
    """
    settings = get_settings()
    api_key = settings.sarvam_api_key

    if not api_key:
        raise ValueError("SARVAM_API_KEY not set in environment")

    lang_code = LANGUAGE_MAP.get(language, "unknown")

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    headers = {"api-subscription-key": api_key}

    files = {
        "file": ("audio.wav", audio_bytes, "audio/wav"),
    }
    data = {
        "language_code": lang_code,
        "model": "saarika:v2",         # Sarvam's multilingual model
        "with_timestamps": "false",
        "with_disfluencies": "false",
    }

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            SARVAM_ASR_URL,
            headers=headers,
            files=files,
            data=data,
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Sarvam API error {response.status_code}: {response.text}"
        )

    result = response.json()
    transcript = result.get("transcript", "").strip()

    if not transcript:
        raise RuntimeError("Sarvam returned empty transcript")

    # Detect language from response
    detected_lang = result.get("language_code", lang_code)

    return {
        "transcript": transcript,
        "language_code": detected_lang,
        "provider": "sarvam",
    }
