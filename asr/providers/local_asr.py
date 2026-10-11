"""
Local ASR fallback using OpenAI Whisper.

Uses large-v3 for significantly better Indian-language accuracy.
Hindi audio gets a Devanagari initial_prompt so Whisper prefers
Hindi script over Urdu/Arabic Nastaliq, which base models confuse.
"""
import re
import whisper
import threading
import logging

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()

# Urdu Nastaliq range — same guard used in sarvam_api.py
_URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")

# Whisper model to load — large-v3 gives far better Hindi/Kannada accuracy.
# Falls back to "medium" if VRAM is too small.
WHISPER_MODEL = "large-v3"

# Seed prompt for Hindi: anchors Whisper to Devanagari script context
# so it outputs Hindi (हिन्दी) rather than Urdu (اردو).
_HINDI_INITIAL_PROMPT = (
    "यह एक अस्पताल कॉल सेंटर की बातचीत है। "
    "मरीज हिन्दी और अंग्रेज़ी में बात कर रहे हैं।"
)


def _load_model():
    global _model
    with _lock:
        if _model is None:
            try:
                logger.info(f"Loading Whisper model: {WHISPER_MODEL}")
                _model = whisper.load_model(WHISPER_MODEL)
                logger.info(f"Whisper {WHISPER_MODEL} loaded.")
            except Exception as e:
                logger.warning(f"Failed to load {WHISPER_MODEL}: {e} — falling back to medium")
                _model = whisper.load_model("medium")
    return _model


def transcribe(audio_path: str, language: str = None) -> dict:
    model = _load_model()

    # Build decode options
    options = {
        "fp16": False,
        "task": "transcribe",
        "beam_size": 5,
        "best_of": 5,
        "no_speech_threshold": 0.4,
        "condition_on_previous_text": True,
    }

    # If language is explicitly given, use it
    if language and language not in ("auto", "unknown"):
        options["language"] = language

    # For Hindi (or unknown), anchor the prompt so Whisper outputs Devanagari
    if not language or language in ("auto", "unknown", "hi", "hi-IN"):
        options["initial_prompt"] = _HINDI_INITIAL_PROMPT

    result = model.transcribe(audio_path, **options)
    transcript = result.get("text", "").strip()
    detected = result.get("language", language or "unknown")

    if not transcript:
        raise RuntimeError("Whisper returned empty transcript")

    # If Whisper still returns Urdu script, retry with language forced to "hi"
    if _URDU_SCRIPT_RE.search(transcript) and detected in ("ur", "unknown", None):
        logger.warning("Whisper returned Urdu script — retrying with language=hi forced.")
        options["language"] = "hi"
        options["initial_prompt"] = _HINDI_INITIAL_PROMPT
        result2 = model.transcribe(audio_path, **options)
        transcript2 = result2.get("text", "").strip()
        if transcript2 and not _URDU_SCRIPT_RE.search(transcript2):
            transcript = transcript2
            detected = "hi"

    return {"transcript": transcript, "language_code": detected, "provider": "whisper"}

