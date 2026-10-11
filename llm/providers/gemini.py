"""
Gemini LLM provider — primary cloud LLM.
Uses gemini-1.5-flash via the new google-genai SDK.
"""
from google import genai
from google.genai import types
from config import get_settings


def _get_client():
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)


def complete(prompt: str) -> str:
    """
    Send prompt to Gemini and return raw text response.
    Raises on API failure — caller handles fallback.
    """
    if not get_settings().gemini_api_key:
        raise ValueError("GEMINI_API_KEY not set — falling back to local LLM")

    client = _get_client()
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=2048,
        ),
    )

    text = response.text.strip() if response.text else ""
    if not text:
        raise RuntimeError("Gemini returned empty response")

    return text
