import logging
import httpx
from typing import Optional, Dict, Any, List
from uuid import uuid4
from datetime import datetime
try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None
from backend.schemas.request_schema import AnalyzeRequest
from backend.schemas.internal_models import RuleEngineResult, MLEngineResult, RiskLevel
from backend.services.metrics_service import MetricsService
from backend.config import settings

logger = logging.getLogger(__name__)

class SupabaseService:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.http_client: Optional[httpx.Client] = None
            self._init_client()
            self._initialized = True

    def _init_client(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self.client: Optional[Client] = None
        if create_client and self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
            except BaseException as e:
                logger.error(f"Failed to initialize Supabase: {e}")
        else:
            logger.warning(f"Supabase Init Skip")

    def get_scoped_client(self, access_token: str) -> Optional[Client]:
        if not self.url: return None
        try:
            http_client = httpx.Client(
                limits=httpx.Limits(max_connections=settings.POOL_MAX_SIZE, max_keepalive_connections=10),
                timeout=settings.POOL_TIMEOUT,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            return create_client(self.url, access_token, options={"http_client": http_client})
        except BaseException as e:
            logger.error(f"Failed to create scoped Supabase client: {e}")
            return None

    def _with_retry(self, func, *args, max_retries: int = 2, **kwargs):
        import time
        for attempt in range(max_retries + 1):
            try:
                res = func(*args, **kwargs)
                MetricsService.record_success("supabase")
                return res
            except BaseException as e:
                if attempt < max_retries:
                    wait = (2 ** attempt)
                    logger.warning(f"Retry {attempt+1}/{max_retries}: {e}")
                    time.sleep(wait)
                else:
                    MetricsService.record_error("supabase", type(e).__name__)
                    return None

    def save_patient_input(self, user_id: str, data: AnalyzeRequest, ip_address: Optional[str] = None, user_agent: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        if not self.client: return str(uuid4())
        try:
            input_record = {
                "user_id": user_id, "age": data.age, "trimester": data.trimester, "trimester_weeks": data.trimester_weeks,
                "blood_pressure": data.blood_pressure,
                "hemoglobin": data.hemoglobin, "heart_rate": data.heart_rate, "swelling": bool(data.swelling),
                "headache_severity": data.headache_severity, "vaginal_bleeding": bool(data.vaginal_bleeding),
                "diabetes_history": bool(data.diabetes_history), "previous_complications": bool(data.previous_complications),
                "fever": bool(data.fever), "blurred_vision": bool(data.blurred_vision), "reduced_fetal_movement": bool(data.reduced_fetal_movement),
                "severe_abdominal_pain": bool(data.severe_abdominal_pain), "ip_address": ip_address, "user_agent": user_agent,
                "request_metadata": metadata, "created_at": datetime.now().isoformat()
            }
            response = self._with_retry(lambda: self.client.table("patient_inputs").insert(input_record).execute())
            return response.data[0].get('id') if response and hasattr(response, 'data') and response.data else None
        except BaseException as e:
            logger.error(f"Supabase Input Error: {e}")
        return None

    def save_analysis_atomic(self, user_id: str, data: AnalyzeRequest, rule_res: RuleEngineResult, ml_res: Optional[MLEngineResult], final_risk: str, explanation: Dict[str, Any], fusion_reason: str, ip: str) -> Optional[str]:
        if not self.client: return str(uuid4())
        try:
            rpc_payload = {
                "p_user_id": user_id, "p_age": data.age, "p_trimester": data.trimester, "p_trimester_weeks": data.trimester_weeks,
                "p_blood_pressure": data.blood_pressure, "p_hb": data.hemoglobin,
                "p_hr": data.heart_rate, "p_swelling": bool(data.swelling), "p_headache": data.headache_severity,
                "p_bleeding": bool(data.vaginal_bleeding), "p_diabetes": bool(data.diabetes_history),
                "p_complications": bool(data.previous_complications), "p_fever": bool(data.fever),
                "p_blurred_vision": bool(data.blurred_vision), "p_rfm": bool(data.reduced_fetal_movement),
                "p_abdominal_pain": bool(data.severe_abdominal_pain), "p_ip": ip, "p_rule_risk": rule_res.risk_level.value,
                "p_rule_score": rule_res.score, "p_rule_flags": rule_res.emergency_flags,
                "p_ml_risk": ml_res.predicted_risk.value if ml_res else None,
                "p_ml_probs": ml_res.probabilities if ml_res else None,
                "p_ml_conf": ml_res.confidence if ml_res and hasattr(ml_res, 'confidence') else None,
                "p_final_risk": final_risk, "p_fusion_reason": fusion_reason, "p_explanation": explanation,
                "p_status": explanation.get("status", "completed")
            }
            try:
                try:
                    import postgrest
                    res = self.client.rpc("save_clinical_assessment_v3", rpc_payload).execute()
                    return res.data if res.data else None
                except (BaseException, postgrest.exceptions.APIError):
                    raise RuntimeError("Persistence Failure")
            except BaseException as rpc_err:
                logger.warning(f"RPC v3 Failed, using fallback: {rpc_err}")
                input_id = self.save_patient_input(user_id, data, ip)
                if input_id:
                     try:
                         self.client.table("engine_results").insert({
                             "input_id": input_id, "rule_risk": rule_res.risk_level.value, "rule_score": rule_res.score,
                             "rule_flags": rule_res.emergency_flags, "ml_risk": ml_res.predicted_risk.value if ml_res else None,
                             "ml_probabilities": ml_res.probabilities if ml_res else None,
                             "ml_confidence": ml_res.confidence if ml_res and hasattr(ml_res, 'confidence') else None,
                             "gemini_explanation": explanation, "final_risk": final_risk,
                             "analysis_status": explanation.get("status", "completed"), "fusion_reason": fusion_reason
                         }).execute()
                     except BaseException:
                         pass
                     return input_id
        except BaseException as e:
            logger.error(f"Supabase Atomic Error: {e}")
        return None

    def log_alert(self, input_id: str, user_id: str, alert_type: str, status: str = "pending") -> bool:
        if not self.client: return True
        try:
            self._with_retry(lambda: self.client.table("alerts").insert({
                "input_id": input_id,
                "user_id": user_id,
                "alert_type": alert_type,
                "status": status
            }).execute())
            return True
        except BaseException as e:
            logger.error(f"Alert Logging Error: {e}")
            return False

    def log_audit(self, user_id: Optional[str], action: str, metadata: Dict[str, Any], ip: str):
        if not self.client: return
        try:
            self._with_retry(lambda: self.client.table("audit_logs").insert({"user_id": user_id, "action": action, "metadata": metadata, "ip_address": ip, "created_at": datetime.now().isoformat()}).execute())
        except BaseException as e:
            logger.error(f"Audit Error: {e}")
