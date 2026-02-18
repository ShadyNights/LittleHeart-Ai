import logging
from typing import Optional
from backend.services.supabase_service import SupabaseService
from backend.schemas.internal_models import RiskLevel

logger = logging.getLogger("AlertService")


class AlertService:
    def __init__(self, db_service: SupabaseService):
        self.db = db_service

    async def trigger_clinical_alert(self, input_id: str, user_id: str, risk_level: RiskLevel) -> bool:
        if risk_level not in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return False

        result = self.db.log_alert(
            input_id=input_id,
            user_id=user_id,
            alert_type=f"{risk_level.value}_RISK_DETECTED",
            status="pending"
        )

        try:
            from backend.websocket_manager import manager
            await manager.broadcast({
                "type": "HIGH_RISK_ALERT",
                "patient_id": user_id,
                "input_id": input_id,
                "risk": risk_level.value,
                "alert_type": f"{risk_level.value}_RISK_DETECTED",
                "status": "pending"
            })
            logger.info(f"Broadcast alert for {risk_level.value} risk to {manager.connection_count} clients")
        except Exception as e:
            logger.error(f"WebSocket broadcast failed: {e}")

        return result
