"""
Tickets / calls read routes.
GET /api/calls          — list all calls (paginated)
GET /api/calls/{id}     — single call with all actions
PATCH /api/actions/{id} — update action status
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from database.supabase_client import get_client
from pydantic import BaseModel

router = APIRouter()


# ── List all calls ───────────────────────────────────────────────────────────
@router.get("/calls")
async def list_calls(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    db = get_client()
    offset = (page - 1) * per_page

    resp = (
        db.table("calls")
        .select("id, created_at, audio_filename, duration_seconds, language_detected, sentiment, ai_summary, asr_provider, llm_provider, needs_review, status")
        .order("created_at", desc=True)
        .range(offset, offset + per_page - 1)
        .execute()
    )
    return JSONResponse(content={"calls": resp.data, "page": page, "per_page": per_page})


# ── Single call with actions ─────────────────────────────────────────────────
@router.get("/calls/{call_id}")
async def get_call(call_id: str):
    db = get_client()

    call_resp = db.table("calls").select("*").eq("id", call_id).execute()
    if not call_resp.data:
        raise HTTPException(status_code=404, detail="Call not found")

    actions_resp = (
        db.table("actions")
        .select("*")
        .eq("call_id", call_id)
        .order("priority", desc=True)
        .execute()
    )

    return JSONResponse(content={
        "call": call_resp.data[0],
        "actions": actions_resp.data,
    })


# ── Update action status ─────────────────────────────────────────────────────
class ActionUpdate(BaseModel):
    status: str       # open | in_progress | resolved
    assigned_to: str | None = None


@router.patch("/actions/{action_id}")
async def update_action(action_id: str, body: ActionUpdate):
    db = get_client()

    update_data = {"status": body.status}
    if body.assigned_to is not None:
        update_data["assigned_to"] = body.assigned_to

    resp = db.table("actions").update(update_data).eq("id", action_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="Action not found")

    return JSONResponse(content={"updated": resp.data[0]})
