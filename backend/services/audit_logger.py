import logging
from typing import Dict, Any, Optional
from backend.schemas.internal_models import RuleEngineResult, MLEngineResult, RiskLevel

logger = logging.getLogger("ClinicalAudit")

class AuditLogger:
    @staticmethod
    def log_assessment(rule_result: RuleEngineResult, ml_result: MLEngineResult, final_risk: RiskLevel):
        audit_entry = {
            "event": "RISK_ASSESSMENT",
            "rule_risk": rule_result.risk_level.value,
            "rule_score": rule_result.score,
            "ml_risk": ml_result.predicted_risk.value if ml_result else None,
            "final_risk": final_risk.value,
            "emergency_flags": rule_result.emergency_flags
        }
    @staticmethod
    def log_action(user_id: Optional[str], action: str, metadata: Dict[str, Any], ip: str = "0.0.0.0"):
        from backend.services.supabase_service import SupabaseService
        SupabaseService().log_audit(user_id, action, metadata, ip)
        logger.info(f"AUDIT_ACTION: {action} | User: {user_id} | Metadata: {metadata}")
