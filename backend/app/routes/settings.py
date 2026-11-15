"""Settings endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings(db: Session = Depends(get_db)):
    """Get all current settings."""
    settings = db.query(Settings).order_by(Settings.key).all()
    return [
        {
            "id": s.id,
            "key": s.key,
            "value": s.value,
            "description": s.description,
        }
        for s in settings
    ]


@router.put("")
def update_settings(data: dict, db: Session = Depends(get_db)):
    """Update settings. Accepts a dict of key: value pairs."""
    updated = []
    for key, value in data.items():
        setting = db.query(Settings).filter(Settings.key == key).first()
        if setting:
            setting.value = str(value)
            updated.append(key)
        else:
            new_setting = Settings(key=key, value=str(value), description=key.replace("_", " ").title())
            db.add(new_setting)
            updated.append(key)
    db.commit()
    return {"updated": updated, "message": f"Updated {len(updated)} setting(s)"}
