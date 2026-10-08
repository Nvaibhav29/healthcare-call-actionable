"""
LLM dual-mode manager.
Tries Gemini first. Falls back to local Qwen2.5 via Ollama.
"""
import logging
from llm.providers import gemini, qwen_ollama

logger = logging.getLogger(__name__)


def complete(prompt: str) -> tuple[str, str]:
    """
    Get LLM completion with automatic fallback.

    Returns:
        (response_text, provider_name)
    """
    # ── Primary: Gemini ─────────────────────────────────────────────────
    try:
        logger.info("LLM: Trying Gemini...")
        text = gemini.complete(prompt)
        logger.info("LLM: Gemini succeeded.")
        return text, "gemini-1.5-flash"

    except Exception as e:
        logger.warning(f"LLM: Gemini failed ({e}). Falling back to Qwen via Ollama...")

    # ── Fallback: Local Qwen ────────────────────────────────────────────
    try:
        text = qwen_ollama.complete(prompt)
        logger.info("LLM: Qwen (Ollama) succeeded.")
        return text, "qwen2.5-7b-ollama"

    except Exception as e:
        logger.error(f"LLM: Both providers failed. Last error: {e}")
        raise RuntimeError(
            "LLM extraction failed: both Gemini and Qwen-Ollama are unavailable."
        )
