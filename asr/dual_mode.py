"""
ASR dual-mode manager.
Tries Sarvam API first. Falls back to local Whisper on any failure.
Returns unified result dict regardless of which provider was used.
"""
import logging
from asr.providers import sarvam_api, local_asr

logger = logging.getLogger(__name__)


def transcribe(audio_path: str, language: str = "auto") -> dict:
    """
    Attempt transcription with Sarvam API.
    On failure, fall back to local Whisper automatically.

    Returns:
        {
            "transcript": str,
            "language_code": str,
            "provider": "sarvam" | "whisper",
            "fallback_used": bool
        }
    """
    # ── Primary: Sarvam API ─────────────────────────────────────────────
    try:
        logger.info("ASR: Trying Sarvam API...")
        result = sarvam_api.transcribe(audio_path, language)
        result["fallback_used"] = False
        logger.info(f"ASR: Sarvam succeeded. Language: {result['language_code']}")
        return result

    except Exception as e:
        logger.warning(f"ASR: Sarvam failed ({e}). Falling back to Whisper...")

    # ── Fallback: Local Whisper ─────────────────────────────────────────
    try:
        lang_hint = None if language == "auto" else language
        result = local_asr.transcribe(audio_path, lang_hint)
        result["fallback_used"] = True
        logger.info(f"ASR: Whisper succeeded. Language: {result['language_code']}")
        return result

    except Exception as e:
        logger.error(f"ASR: Both providers failed. Last error: {e}")
        raise RuntimeError(
            "Transcription failed: both Sarvam and Whisper could not process this audio."
        )
