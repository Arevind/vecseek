from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings
from app.deps import get_app_settings, get_db
from app.models import Setting
from app.schemas import SettingsResponse, SettingsUpdateRequest
from app.utils.errors import bad_request

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings_endpoint(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> SettingsResponse:
    setting = db.get(Setting, 1)
    if not setting:
        setting = Setting(
            default_top_k=settings.default_top_k,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return SettingsResponse(
        default_top_k=setting.default_top_k,
        max_top_k=settings.max_top_k,
        chunk_size=setting.chunk_size,
        chunk_overlap=setting.chunk_overlap,
    )


@router.patch("", response_model=SettingsResponse)
def update_settings(
    payload: SettingsUpdateRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> SettingsResponse:
    if payload.default_top_k > settings.max_top_k:
        raise bad_request(f"default_top_k must be between 1 and {settings.max_top_k}.")
    if payload.chunk_overlap >= payload.chunk_size:
        raise bad_request("chunk_overlap must be smaller than chunk_size.")
    setting = db.get(Setting, 1)
    if not setting:
        setting = Setting(
            default_top_k=payload.default_top_k,
            chunk_size=payload.chunk_size,
            chunk_overlap=payload.chunk_overlap,
        )
    else:
        setting.default_top_k = payload.default_top_k
        setting.chunk_size = payload.chunk_size
        setting.chunk_overlap = payload.chunk_overlap
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return SettingsResponse(
        default_top_k=setting.default_top_k,
        max_top_k=settings.max_top_k,
        chunk_size=setting.chunk_size,
        chunk_overlap=setting.chunk_overlap,
    )
