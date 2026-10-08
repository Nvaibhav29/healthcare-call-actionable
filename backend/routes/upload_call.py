"""
Upload call route.
POST /api/calls/upload  — accepts audio file, runs pipeline, returns result.
"""
import os
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import aiofiles

from pipeline.orchestrator import run
from config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm"}


@router.post("/upload")
async def upload_call(file: UploadFile = File(...)):
    """
    Upload an audio file and process it through the full pipeline.
    Returns extracted summary, actions, and routing decisions.
    """
    settings = get_settings()

    # Validate extension
    _, ext = os.path.splitext(file.filename or "")
    if ext.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Validate size
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_audio_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max: {settings.max_audio_size_mb} MB",
        )

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    try:
        async with aiofiles.open(tmp.name, "wb") as f:
            await f.write(contents)
        tmp.close()

        logger.info(f"Received file: {file.filename} ({size_mb:.2f} MB)")

        result = run(tmp.name, original_filename=file.filename or "upload")
        return JSONResponse(content=result, status_code=200)

    except RuntimeError as e:
        logger.error(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.exception("Unexpected error during call processing")
        raise HTTPException(status_code=500, detail="Internal processing error")

    finally:
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
