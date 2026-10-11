"""
Sarvam AI ASR provider.
Primary ASR — handles Indian languages + code-mixing natively.
Docs: https://docs.sarvam.ai/api-reference-docs/speech-to-text
"""
import re
import httpx
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

# Urdu-specific Nastaliq script range (U+0600–U+06FF) — not Devanagari
# If Sarvam returns Urdu script for a Hindi audio, we re-request with hi-IN forced.
_URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")


def _is_urdu_script(text: str) -> bool:
    """Return True if the text contains Arabic/Urdu Nastaliq characters."""
    return bool(_URDU_SCRIPT_RE.search(text))


def _call_sarvam(api_key: str, audio_bytes: bytes, lang_code: str) -> dict:
    """Make one Sarvam API call and return parsed JSON."""
    headers = {"api-subscription-key": api_key}
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
    data = {
        "language_code": lang_code,
        "model": "saarika:v2",
        "with_timestamps": "false",
        "with_disfluencies": "false",
    }
    with httpx.Client(timeout=60.0) as client:
        response = client.post(SARVAM_ASR_URL, headers=headers, files=files, data=data)
    if response.status_code != 200:
        raise RuntimeError(f"Sarvam API error {response.status_code}: {response.text}")
    return response.json()


def transcribe(audio_path: str, language: str = "auto") -> dict:
    """
    Transcribe audio using Sarvam AI API.

    Fix: If Sarvam auto-detects Urdu script for what is clearly Hindi audio,
    we retry with language_code=hi-IN to force Devanagari output.

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

    result = _call_sarvam(api_key, audio_bytes, lang_code)
    transcript = result.get("transcript", "").strip()

    if not transcript:
        raise RuntimeError("Sarvam returned empty transcript")

    detected_lang = result.get("language_code", lang_code)

    # ── Urdu-script guard ────────────────────────────────────────────────
    # If auto-detect returned Urdu Nastaliq script but this is Indian hospital
    # audio (almost certainly Hindi), retry with hi-IN forced.
    if _is_urdu_script(transcript) and lang_code == "unknown":
        import logging
        logging.getLogger(__name__).warning(
            "Sarvam returned Urdu script — retrying with hi-IN forced."
        )
        result2 = _call_sarvam(api_key, audio_bytes, "hi-IN")
        transcript2 = result2.get("transcript", "").strip()
        if transcript2 and not _is_urdu_script(transcript2):
            transcript = transcript2
            detected_lang = "hi-IN"

    return {
        "transcript": transcript,
        "language_code": detected_lang,
        "provider": "sarvam",
    }
