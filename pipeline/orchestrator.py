"""
Pipeline orchestrator — the single entry point for the entire pipeline.

Flow:
  audio file path
    → preprocess (ffmpeg → 16kHz mono WAV)
    → ASR dual-mode (Sarvam → Whisper)
    → LLM dual-mode (Gemini → Qwen)
    → Router (validate dept + priority + explainability)
    → Supabase (save call + actions)
    → return full result dict
"""
import os
import logging
from datetime import datetime

from asr import dual_mode as asr
from asr.preprocess_audio import preprocess_audio, get_duration_seconds
from llm import extract_actions
from routing import router
from database.supabase_client import get_client

logger = logging.getLogger(__name__)


def run(audio_path: str, original_filename: str = "") -> dict:
    """
    Run the full pipeline on an audio file.

    Args:
        audio_path:        Absolute path to uploaded audio file.
        original_filename: Original filename for logging.

    Returns:
        Full result dict including call_id, actions, summary, etc.
    """
    wav_path = None

    try:
        # ── 1. Preprocess ───────────────────────────────────────────────
        logger.info(f"Pipeline: Preprocessing {original_filename}")
        wav_path = preprocess_audio(audio_path)
        duration = get_duration_seconds(wav_path)
        logger.info(f"Pipeline: Duration = {duration}s")

        # ── 2. ASR ──────────────────────────────────────────────────────
        logger.info("Pipeline: Starting ASR...")
        asr_result = asr.transcribe(wav_path, language="auto")
        transcript = asr_result["transcript"]
        language_code = asr_result["language_code"]
        asr_provider = asr_result["provider"]
        logger.info(f"Pipeline: ASR done. Provider={asr_provider}, lang={language_code}")

        # ── 3. LLM Extraction ───────────────────────────────────────────
        logger.info("Pipeline: Starting LLM extraction...")
        extracted = extract_actions.extract(transcript)
        logger.info(f"Pipeline: LLM done. Actions={len(extracted['actions'])}")

        # ── 4. Routing ──────────────────────────────────────────────────
        logger.info("Pipeline: Routing actions...")
        routed_actions = router.route(extracted)

        # ── 5. Save to Supabase ─────────────────────────────────────────
        logger.info("Pipeline: Saving to Supabase...")
        db = get_client()

        call_record = {
            "audio_filename": original_filename,
            "duration_seconds": duration,
            "language_detected": extracted.get("language_detected", language_code),
            "sentiment": extracted.get("sentiment", "neutral"),
            "sentiment_score": extracted.get("sentiment_score", 0.5),
            "raw_transcript": transcript,
            "ai_summary": extracted.get("summary", ""),
            "asr_provider": asr_provider,
            "llm_provider": extracted.get("llm_provider", "unknown"),
            "confidence_score": _avg_confidence(routed_actions),
            "needs_review": extracted.get("needs_review", False),
            "status": "needs_review" if extracted.get("needs_review") else "routed",
        }

        call_resp = db.table("calls").insert(call_record).execute()
        call_id = call_resp.data[0]["id"]
        logger.info(f"Pipeline: Call saved with id={call_id}")

        # Insert actions linked to this call
        for action in routed_actions:
            action["call_id"] = call_id

        if routed_actions:
            db.table("actions").insert(routed_actions).execute()
            logger.info(f"Pipeline: {len(routed_actions)} actions saved.")

        return {
            "call_id": call_id,
            "duration_seconds": duration,
            "language_detected": call_record["language_detected"],
            "sentiment": call_record["sentiment"],
            "sentiment_score": call_record["sentiment_score"],
            "summary": call_record["ai_summary"],
            "transcript": transcript,
            "asr_provider": asr_provider,
            "llm_provider": call_record["llm_provider"],
            "needs_review": call_record["needs_review"],
            "actions": routed_actions,
            "action_count": len(routed_actions),
        }

    finally:
        # Always clean up temp WAV file
        if wav_path and os.path.exists(wav_path):
            os.unlink(wav_path)
            logger.debug(f"Pipeline: Cleaned up temp file {wav_path}")


def _avg_confidence(actions: list[dict]) -> float:
    if not actions:
        return 1.0
    return round(
        sum(float(a.get("confidence", 1.0)) for a in actions) / len(actions), 3
    )
