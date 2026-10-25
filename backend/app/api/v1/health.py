import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.services.llm_provider_service import llm_provider_service

router = APIRouter(tags=["Health & Runtime Config"])

START_TIME = time.time()


class LLMConfigUpdateRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model_name: Optional[str] = None


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """System health check verifying database connectivity, round-trip latency, and active LLM engine."""
    t0 = time.perf_counter()
    try:
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        db_status = "healthy"
    except Exception as e:
        db_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        db_status = f"unhealthy: {str(e)}"

    llm_cfg = llm_provider_service.get_config()
    uptime_sec = round(time.time() - START_TIME, 1)

    return {
        "status": "online",
        "service": "VersionRAG API",
        "version": "1.0.0",
        "database": db_status,
        "database_latency_ms": db_latency_ms,
        "uptime_seconds": uptime_sec,
        "active_llm_provider": llm_cfg["active_provider"],
        "active_llm_model": llm_cfg["active_model"],
    }


@router.get("/health/llm-config")
def get_runtime_llm_config():
    """Return current runtime LLM provider, model, masked API key status, and supported providers."""
    return llm_provider_service.get_config()


@router.post("/health/llm-config")
def update_runtime_llm_config(req: LLMConfigUpdateRequest):
    """Dynamically switch active LLM provider (Local, Gemini, OpenAI, Anthropic, Groq) and API key at runtime."""
    try:
        return llm_provider_service.update_config(
            provider=req.provider,
            api_key=req.api_key,
            model_name=req.model_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

