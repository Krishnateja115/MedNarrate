import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.system_setting import SystemSetting
from app.core.config import settings
from app.core.admin_auth import AdminContext, require_permission
from app.services.audit import log_admin_action

router = APIRouter()

def mask_secret(value: str | None) -> str:
    if not value or len(value) < 6:
        return "********"
    return f"{value[:3]}****{value[-3:]}"

class AIConfigUpdate(BaseModel):
    primary_provider: Optional[str] = Field(None, example="gemini")
    model_name: Optional[str] = Field(None, example="gemini-1.5-pro")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=32000)
    fallback_provider: Optional[str] = Field(None, example="ollama")
    api_key: Optional[str] = Field(None, description="Secret API key. Will be stored securely and never returned in plain text.")

@router.get("/ai-config")
async def get_ai_configuration(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("ai_config:read"))
):
    # Retrieve system settings for AI
    stmt = select(SystemSetting).where(SystemSetting.category == "ai_config")
    res = await db.execute(stmt)
    settings_records = {s.key: s.value for s in res.scalars().all()}

    primary_provider = settings_records.get("ai_primary_provider", getattr(settings, "AI_PRIMARY_PROVIDER", "gemini"))
    model_name = settings_records.get("ai_model_name", getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash"))
    temperature = float(settings_records.get("ai_temperature", "0.2"))
    max_tokens = int(settings_records.get("ai_max_tokens", "2048"))
    fallback_provider = settings_records.get("ai_fallback_provider", "ollama")

    raw_key = settings_records.get("ai_api_key", getattr(settings, "GEMINI_API_KEY", None))
    key_is_set = bool(raw_key and raw_key.strip())
    masked_key = mask_secret(raw_key) if key_is_set else None

    return {
        "primary_provider": primary_provider,
        "model_name": model_name,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "fallback_provider": fallback_provider,
        "api_key_status": {
            "is_set": key_is_set,
            "masked_key": masked_key,
        }
    }

@router.put("/ai-config")
async def update_ai_configuration(
    payload: AIConfigUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin_ctx: AdminContext = Depends(require_permission("ai_config:manage"))
):
    async def _upsert_setting(key: str, val: str, is_sensitive: bool = False, description: str = ""):
        res = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
        record = res.scalar_one_or_none()
        if not record:
            record = SystemSetting(
                id=uuid.uuid4(),
                key=key,
                value=val,
                category="ai_config",
                is_sensitive=is_sensitive,
                description=description,
                updated_by_id=admin_ctx.user_id
            )
            db.add(record)
        else:
            record.value = val
            record.is_sensitive = is_sensitive
            record.updated_by_id = admin_ctx.user_id

    changes = {}
    if payload.primary_provider is not None:
        await _upsert_setting("ai_primary_provider", payload.primary_provider, False, "Primary AI Provider")
        changes["primary_provider"] = payload.primary_provider

    if payload.model_name is not None:
        await _upsert_setting("ai_model_name", payload.model_name, False, "AI Model Name")
        changes["model_name"] = payload.model_name

    if payload.temperature is not None:
        await _upsert_setting("ai_temperature", str(payload.temperature), False, "Sampling Temperature")
        changes["temperature"] = payload.temperature

    if payload.max_tokens is not None:
        await _upsert_setting("ai_max_tokens", str(payload.max_tokens), False, "Max Tokens output limit")
        changes["max_tokens"] = payload.max_tokens

    if payload.fallback_provider is not None:
        await _upsert_setting("ai_fallback_provider", payload.fallback_provider, False, "Fallback AI Provider")
        changes["fallback_provider"] = payload.fallback_provider

    if payload.api_key is not None and payload.api_key.strip():
        await _upsert_setting("ai_api_key", payload.api_key.strip(), True, "AI Provider API Key")
        changes["api_key"] = "[UPDATED_SENSITIVE]"

    await db.commit()

    # Log action (automatically sanitizes sensitive keys)
    await log_admin_action(
        db=db,
        actor_admin_id=admin_ctx.user_id,
        action="ai_config_update",
        resource_type="system_setting",
        resource_id="ai_config",
        permission_used="ai_config:manage",
        result="success",
        reason="Updated AI operational configuration",
        request=request,
        metadata={"changes": changes},
        sensitive_access_flag=True if "api_key" in changes else False
    )

    return {"message": "AI configuration updated successfully", "updated_fields": list(changes.keys())}
