from fastapi import APIRouter, Depends, Request, BackgroundTasks
from typing import Dict, Any, Optional
from datetime import datetime
import logging
import os
from backend.schemas.request_schema import AnalyzeRequest
from backend.schemas.response_schema import AnalyzeResponse
from backend.schemas.internal_models import RiskLevel
from backend.core.feature_engineering import preprocess_input
from backend.core.decision_fusion import fuse_risk, calculate_clinical_confidence
from backend.engines.rule_engine import RuleEngine
from backend.engines.ml_engine import MLEngine
from backend.engines.gemini_engine import GeminiEngine
from backend.services.supabase_service import SupabaseService
from backend.services.notification_service import NotificationService
from backend.services.alert_service import AlertService
from backend.services.audit_logger import AuditLogger
from backend.utils.auth import Auth, get_user_id
from backend.config import settings
from backend.services.metrics_service import MetricsService
import time
from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.services.conversation_service import ConversationService, ChatState

router = APIRouter()
logger = logging.getLogger("AnalyzeAPI")
limiter = Limiter(key_func=get_remote_address)

import asyncio
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)

rule_engine = RuleEngine()
supabase = SupabaseService()
audit_logger = AuditLogger()
notification_service = NotificationService(supabase)
alert_service = AlertService(supabase)
conv_service = ConversationService()

try:
    ml_engine = MLEngine()
    logger.info("ML Engine initialized.")
except Exception as e:
    logger.error(f"ML Engine failed: {e}")
    ml_engine = None

gemini_engine = None
if settings.GEMINI_API_KEY:
    try:
        gemini_engine = GeminiEngine(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini Engine initialized.")
    except Exception as e:
        logger.error(f"Gemini Engine failed: {e}")

async def async_clinical_augmentation(input_id: str, user_id: str, data: AnalyzeRequest, final_risk: RiskLevel, rule_res: Any, ml_res: Any):
    explanation = {"reasoning": "Generating..."}
    if gemini_engine:
        try:
            explanation = await asyncio.wait_for(
                asyncio.to_thread(gemini_engine.explain, data, final_risk, rule_res, ml_res),
                timeout=20.0 
            )
            supabase.client.table("engine_results").update({
                "gemini_explanation": explanation,
                "analysis_status": "completed"
            }).eq("input_id", input_id).execute()
        except asyncio.TimeoutError:
            logger.warning(f"Gemini Timeout for input {input_id}")
            explanation = {"reasoning": "Clinical explanation timed out."}
        except Exception as e:
            logger.error(f"Async Gemini failed: {e}")
    
    if final_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
        notification_service.check_and_alert(input_id, user_id, data, final_risk)
        alert_service.trigger_clinical_alert(input_id, user_id, final_risk)

@router.post("/analyze")
@limiter.limit("10/minute")
async def analyze(request: Request, data: AnalyzeRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_user_id)) -> AnalyzeResponse:
    correlation_id = getattr(request.state, "correlation_id", f"anl_{int(time.time())}") if request else f"chat_{int(time.time())}"
    
    r_start = time.time()
    rule_result = rule_engine.evaluate(data)
    MetricsService.record_latency("rule", time.time() - r_start)
    
    ml_result = None
    if ml_engine:
        try:
            m_start = time.time()
            loop = asyncio.get_event_loop()
            ml_result = await loop.run_in_executor(executor, ml_engine.predict, data)
            MetricsService.record_latency("ml", time.time() - m_start)
        except Exception as e:
            logger.error(f"[{correlation_id}] ML Prediction failed: {e}")
            MetricsService.record_error("ml", type(e).__name__)
    
    final_risk = fuse_risk(rule_result, ml_result)
    clinical_confidence = calculate_clinical_confidence(rule_result, ml_result)
    
    fusion_reason = "Aligned"
    if ml_result:
        if final_risk == rule_result.risk_level and final_risk != ml_result.predicted_risk:
            fusion_reason = "Rule Engine Authority override"
        elif final_risk == ml_result.predicted_risk and final_risk != rule_result.risk_level:
            fusion_reason = "ML Engine Escalation"
    elif not ml_result:
        fusion_reason = "Rule Engine Authority (ML Offline)"
    
    ip_address = request.client.host if request and request.client else "internal_bot"
    db_start = time.time()
    input_id = supabase.save_analysis_atomic(
        user_id=user_id,
        data=data,
        rule_res=rule_result,
        ml_res=ml_result,
        final_risk=final_risk.value,
        explanation={"status": "async_pending", "correlation_id": correlation_id},
        fusion_reason=fusion_reason,
        ip=ip_address
    )
    MetricsService.record_latency("db", time.time() - db_start)
    
    if input_id:
        background_tasks.add_task(async_clinical_augmentation, input_id, user_id, data, final_risk, rule_result, ml_result)
    else:
        MetricsService.record_error("db", "ATOMIC_SAVE_FAILED")
        
    MetricsService.record_request(200)
    
    disclaimer = (
        "LITTLEHEART AI SAFETY DISCLAIMER: This system is a SOFTWARE PROTOTYPE and has NOT been medically certified. "
        "All outputs are for research purposes. Always consult a human medical professional."
    )

    return AnalyzeResponse(
        input_id=input_id,
        final_risk=final_risk.value,
        clinical_confidence=clinical_confidence,
        explanation={"status": "generating_async", "correlation_id": correlation_id},
        engine_results={
            "rule": {
                "risk": rule_result.risk_level.value,
                "score": rule_result.score,
                "flags": rule_result.emergency_flags
            },
            "ml": {
                "risk": ml_result.predicted_risk.value if ml_result else None,
                "confidence": ml_result.confidence if ml_result else None,
                "probabilities": ml_result.probabilities if ml_result else {}
            }
        },
        metadata={
            "correlation_id": correlation_id,
            "latency": float(round(time.time() - r_start, 3)),
            "engine_versions": settings.VERSION_MANIFEST,
            "clinical_watermark": "DEEP_HARDENED_V4_PROTOTYPE"
        },
        certification_disclaimer=disclaimer
    )

@router.get("/history")
async def get_history(user_id: str = Depends(get_user_id)):
    """Fetches real assessment history for the user from Supabase."""
    try:
        # Pull from engine_results joined with patient_inputs if possible, or just engine_results
        # For simplicity, we query engine_results which contains final_risk and created_at
        res = supabase.client.table("engine_results").select(
            "id, final_risk, created_at, input_id"
        ).order("created_at", desc=True).limit(20).execute()
        
        history = []
        # Map RiskLevel strings to scores for the trend chart
        risk_scores = {"LOW": 10, "MEDIUM": 35, "HIGH": 70, "CRITICAL": 95}
        
        for item in (res.data or []):
            risk_label = item.get("final_risk", "LOW").upper()
            history.append({
                "date": item.get("created_at", "").split("T")[0],
                "risk_score": risk_scores.get(risk_label, 10),
                "risk_label": risk_label
            })
        return history[::-1] # Chronological order
    except Exception as e:
        logger.error(f"History Fetch Failed: {e}")
        return []

@router.get("/chat/init")
async def init_chat(user_id: str = Depends(get_user_id)):
    session = await conv_service.get_or_create_session(user_id)
    return {"session_id": session["id"], "state": session["current_state"], "data": session["collected_data"]}

@router.post("/chat/message")
async def chat_message(session_id: str, message: str, user_id: str = Depends(get_user_id)):
    response, next_state = await conv_service.process_message(user_id, session_id, message)
    return {"response": response, "next_state": next_state.value}
