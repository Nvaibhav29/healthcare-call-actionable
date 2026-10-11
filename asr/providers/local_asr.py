"""
Local ASR fallback using faster-whisper (CTranslate2 INT8).

Uses existing 'small' model with 8-bit quantization for high accuracy
on Indian accents while using minimal RAM (~350MB) and low CPU.
Hindi audio gets a Devanagari initial_prompt so Whisper prefers
Hindi script over Urdu/Arabic Nastaliq.
"""
import os
import re
import threading
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()

# Urdu Nastaliq range — same guard used in sarvam_api.py
_URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")

# Model name — defaults to cached "small" model
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

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
            logger.info(f"Loading faster-whisper model '{WHISPER_MODEL}' (INT8 on CPU)...")
            try:
                _model = WhisperModel(
                    WHISPER_MODEL,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                )
                logger.info(f"faster-whisper '{WHISPER_MODEL}' loaded successfully.")
            except Exception as e:
                logger.warning(f"Failed to load {WHISPER_MODEL}: {e} — falling back to base")
                _model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)
    return _model


def transcribe(audio_path: str, language: str = None) -> dict:
    model = _load_model()

    lang_param = language if language and language not in ("auto", "unknown") else None
    prompt_param = (
        _HINDI_INITIAL_PROMPT
        if not language or language in ("auto", "unknown", "hi", "hi-IN")
        else None
    )

    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language=lang_param,
        initial_prompt=prompt_param,
        condition_on_previous_text=True,
        no_speech_threshold=0.4,
    )
    transcript = " ".join([segment.text for segment in segments]).strip()
    detected = info.language or (language or "unknown")

    if not transcript:
        raise RuntimeError("Whisper returned empty transcript")

    # If Whisper still returns Urdu script, retry with language forced to "hi"
    if _URDU_SCRIPT_RE.search(transcript) and detected in ("ur", "unknown", None):
        logger.warning("Whisper returned Urdu script — retrying with language=hi forced.")
        segments2, info2 = model.transcribe(
            audio_path,
            beam_size=5,
            language="hi",
            initial_prompt=_HINDI_INITIAL_PROMPT,
            condition_on_previous_text=True,
        )
        transcript2 = " ".join([segment.text for segment in segments2]).strip()
        if transcript2 and not _URDU_SCRIPT_RE.search(transcript2):
            transcript = transcript2
            detected = "hi"

    return {"transcript": transcript, "language_code": detected, "provider": "whisper"}

