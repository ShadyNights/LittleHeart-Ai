from backend.schemas.internal_models import RiskLevel

SEVERITY_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4
}

def get_severity_score(risk_level: RiskLevel) -> int:
    return SEVERITY_ORDER.get(risk_level, 0)

def is_escalation(base_risk: RiskLevel, target_risk: RiskLevel) -> bool:
    return get_severity_score(target_risk) > get_severity_score(base_risk)
