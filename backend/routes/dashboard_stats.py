"""
Dashboard stats route.
GET /api/stats — aggregated numbers for the dashboard header cards + dept load.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from database.supabase_client import get_client
from datetime import datetime, timezone

router = APIRouter()


@router.get("/stats")
async def get_stats():
    db = get_client()

    # Today's date range (UTC)
    today = datetime.now(timezone.utc).date().isoformat()

    # Total calls today
    calls_today = (
        db.table("calls")
        .select("id", count="exact")
        .gte("created_at", f"{today}T00:00:00Z")
        .execute()
    )

    # Total open actions
    open_actions = (
        db.table("actions")
        .select("id", count="exact")
        .eq("status", "open")
        .execute()
    )

    # Needs review count
    needs_review = (
        db.table("calls")
        .select("id", count="exact")
        .eq("needs_review", True)
        .eq("status", "needs_review")
        .execute()
    )

    # Avg processing duration today (duration_seconds)
    calls_with_duration = (
        db.table("calls")
        .select("duration_seconds")
        .gte("created_at", f"{today}T00:00:00Z")
        .execute()
    )
    durations = [c["duration_seconds"] for c in calls_with_duration.data if c["duration_seconds"]]
    avg_duration = round(sum(durations) / len(durations)) if durations else 0

    # Department load — open actions per department
    all_open = (
        db.table("actions")
        .select("department")
        .eq("status", "open")
        .execute()
    )
    dept_counts: dict[str, int] = {}
    for row in all_open.data:
        d = row["department"]
        dept_counts[d] = dept_counts.get(d, 0) + 1

    dept_load = [
        {"department": dept, "open_count": count}
        for dept, count in sorted(dept_counts.items(), key=lambda x: -x[1])
    ]

    return JSONResponse(content={
        "calls_today": calls_today.count or 0,
        "open_actions": open_actions.count or 0,
        "needs_review": needs_review.count or 0,
        "avg_duration_seconds": avg_duration,
        "department_load": dept_load,
    })
