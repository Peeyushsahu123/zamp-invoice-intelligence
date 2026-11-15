"""Dashboard statistics endpoint."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ProcessingRun, DecisionStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Return real dashboard statistics from the database."""
    completed_runs = (
        db.query(ProcessingRun)
        .filter(ProcessingRun.decision.isnot(None))
        .all()
    )

    total = len(completed_runs)
    approved = sum(1 for r in completed_runs if r.decision and r.decision.get("status") == DecisionStatus.APPROVED.value)
    review = sum(1 for r in completed_runs if r.decision and r.decision.get("status") == DecisionStatus.REVIEW_REQUIRED.value)
    rejected = sum(1 for r in completed_runs if r.decision and r.decision.get("status") == DecisionStatus.REJECTED.value)

    # Recent runs
    recent = (
        db.query(ProcessingRun)
        .order_by(ProcessingRun.created_at.desc())
        .limit(10)
        .all()
    )

    recent_list = []
    for r in recent:
        recent_list.append({
            "id": r.id,
            "status": r.status.value if r.status else "unknown",
            "decision": r.decision,
            "extracted_data": r.extracted_data,
            "extraction_method": r.extraction_method,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        })

    return {
        "total_processed": total,
        "approved_count": approved,
        "review_count": review,
        "rejected_count": rejected,
        "recent_runs": recent_list,
    }
