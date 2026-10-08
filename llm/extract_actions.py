"""
Action extractor — core intelligence module.
Loads the prompt, injects transcript, calls LLM, parses JSON output.
"""
import json
import re
import logging
from pathlib import Path
from llm import dual_mode
from config import get_settings

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "action_extraction.txt"


def _load_prompt(transcript: str) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.replace("{transcript}", transcript)


def _clean_json(raw: str) -> str:
    """Strip markdown fences if LLM wraps in ```json ... ```"""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def extract(transcript: str) -> dict:
    """
    Run the full extraction pipeline on a transcript.

    Returns:
        {
            "summary": str,
            "sentiment": str,
            "sentiment_score": float,
            "language_detected": str,
            "actions": [...],
            "llm_provider": str,
            "needs_review": bool        # True if any action confidence < threshold
        }
    """
    settings = get_settings()
    prompt = _load_prompt(transcript)
    raw, provider = dual_mode.complete(prompt)

    try:
        cleaned = _clean_json(raw)
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"LLM returned invalid JSON: {e}\nRaw:\n{raw}")
        raise ValueError(f"LLM did not return valid JSON: {e}")

    # Validate & normalise required fields
    data.setdefault("summary", "")
    data.setdefault("sentiment", "neutral")
    data.setdefault("sentiment_score", 0.5)
    data.setdefault("language_detected", "unknown")
    data.setdefault("actions", [])

    # Check if any action needs human review
    threshold = settings.confidence_threshold
    needs_review = any(
        float(a.get("confidence", 1.0)) < threshold
        for a in data["actions"]
    )

    data["llm_provider"] = provider
    data["needs_review"] = needs_review

    logger.info(
        f"Extraction complete: {len(data['actions'])} actions, "
        f"provider={provider}, needs_review={needs_review}"
    )

    return data
