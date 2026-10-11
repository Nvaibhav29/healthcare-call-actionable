"""
Local ASR fallback using OpenAI Whisper.

Uses large-v3 for significantly better Indian-language accuracy.
Hindi audio gets a Devanagari initial_prompt so Whisper prefers
Hindi script over Urdu/Arabic Nastaliq, which base models confuse.
"""
import os
import re
import whisper
import threading
import logging

import torch

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()

# Urdu Nastaliq range — same guard used in sarvam_api.py
_URDU_SCRIPT_RE = re.compile(r"[\u0600-\u06FF]")

# Whisper model to load — default to existing lightweight "base" model
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Seed prompt for Hindi: anchors Whisper to Devanagari script context
# so it outputs Hindi (हिन्दी) rather than Urdu (اردو).
_HINDI_INITIAL_PROMPT = (
    "यह एक अस्पताल कॉल सेंटर की बातचीत है। "
    "मरीज हिन्दी और अंग्रेज़ी में बात कर रहे हैं।"
)


def _get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _load_model():
    global _model
    with _lock:
        if _model is None:
            device = _get_device()
            gpu_name = torch.cuda.get_device_name(0) if device == "cuda" else "CPU"
            logger.info(f"Loading Whisper model '{WHISPER_MODEL}' on {device} ({gpu_name})")
            try:
                _model = whisper.load_model(WHISPER_MODEL, device=device)
                logger.info(f"Whisper {WHISPER_MODEL} loaded successfully on {device} ({gpu_name}).")
            except Exception as e:
                logger.warning(f"Failed to load {WHISPER_MODEL} on {device}: {e} — falling back to base")
                _model = whisper.load_model("base", device=device)
    return _model


def transcribe(audio_path: str, language: str = None) -> dict:
    device = _get_device()
    model = _load_model()

    # Build decode options — enable fp16 on CUDA for maximum speed and 3GB VRAM footprint
    options = {
        "fp16": (device == "cuda"),
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

