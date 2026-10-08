"""
Gemini LLM provider — primary cloud LLM.
Uses gemini-1.5-flash for speed and cost efficiency.
"""
import google.generativeai as genai
from config import get_settings


def _get_model():
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def complete(prompt: str) -> str:
    """
    Send prompt to Gemini and return raw text response.
    Raises on API failure — caller handles fallback.
    """
    model = _get_model()

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.1,        # low temp = deterministic extraction
            max_output_tokens=2048,
        ),
    )

    text = response.text.strip()
    if not text:
        raise RuntimeError("Gemini returned empty response")

    return text
