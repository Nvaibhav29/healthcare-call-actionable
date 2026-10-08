"""
Audio preprocessor.
Converts any input audio to 16 kHz mono WAV using ffmpeg.
Required format for both Sarvam API and Vakyansh/Whisper.
"""
import subprocess
import tempfile
import os
from pathlib import Path


def preprocess_audio(input_path: str) -> str:
    """
    Convert audio file to 16kHz mono WAV.
    Returns path to the converted temp file.
    Caller is responsible for deleting the temp file.
    """
    suffix = ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.close()
    out_path = tmp.name

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-ac", "1",           # mono
        "-ar", "16000",       # 16 kHz
        "-c:a", "pcm_s16le",  # 16-bit PCM
        out_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        os.unlink(out_path)
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    return out_path


def get_duration_seconds(file_path: str) -> int:
    """Return audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return 0
    try:
        return int(float(result.stdout.strip()))
    except (ValueError, AttributeError):
        return 0
