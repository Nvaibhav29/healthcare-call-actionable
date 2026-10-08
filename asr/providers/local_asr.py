"""
Local ASR fallback using OpenAI Whisper.
Used when Sarvam API is unavailable or returns an error.
Whisper large-v3 handles Hindi, Kannada, English reasonably well.
"""
import whisper
import threading

_model = None
_lock = threading.Lock()


def _load_model(model_size: str = "large-v3"):
    """Load Whisper model once and cache it."""
    global _model
    with _lock:
        if _model is None:
            _model = whisper.load_model(model_size)
    return _model


def transcribe(audio_path: str, language: str = None) -> dict:
    """
    Transcribe audio using local Whisper model.

    Args:
        audio_path: Path to preprocessed 16kHz mono WAV.
        language:   ISO language code hint ("hi", "kn", "en") or None for auto.

    Returns:
        {
            "transcript": str,
            "language_code": str,
            "provider": "whisper"
        }
    """
    model = _load_model("large-v3")

    options = {
        "fp16": False,          # safe for CPU inference
        "task": "transcribe",   # keep original language, do not translate
    }
    if language and language != "auto":
        options["language"] = language

    result = model.transcribe(audio_path, **options)

    transcript = result.get("text", "").strip()
    detected = result.get("language", language or "unknown")

    if not transcript:
        raise RuntimeError("Whisper returned empty transcript")

    return {
        "transcript": transcript,
        "language_code": detected,
        "provider": "whisper",
    }
