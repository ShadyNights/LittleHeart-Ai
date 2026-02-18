import math
from typing import Optional
from backend.schemas.internal_models import RiskLevel, RuleEngineResult, MLEngineResult

SEVERITY_ORDER = {
    RiskLevel.LOW: 1,
    RiskLevel.MEDIUM: 2,
    RiskLevel.HIGH: 3,
    RiskLevel.CRITICAL: 4
}

def calculate_clinical_confidence(rule_result: RuleEngineResult, ml_result: Optional[MLEngineResult]) -> float:
    if not ml_result:
        return 0.7
    
    probs = ml_result.probabilities.values()
    entropy = -sum(p * math.log2(p) for p in probs if p > 0)
    max_entropy = math.log2(len(ml_result.probabilities))
    normalized_confidence = 1 - (entropy / max_entropy) if max_entropy > 0 else 1.0
    
    alignment_factor = 1.0
    if rule_result.risk_level == ml_result.predicted_risk:
        alignment_factor = 1.1
    elif abs(SEVERITY_ORDER[rule_result.risk_level] - SEVERITY_ORDER[ml_result.predicted_risk]) >= 2:
        alignment_factor = 0.7
        
    return max(0.1, min(1.0, normalized_confidence * alignment_factor))

def fuse_risk(rule_result: RuleEngineResult, ml_result: MLEngineResult) -> RiskLevel:
    rule_level = rule_result.risk_level
    ml_level = ml_result.predicted_risk if ml_result else RiskLevel.LOW
    
    if rule_level == RiskLevel.CRITICAL:
        return RiskLevel.CRITICAL
        
    rule_score = SEVERITY_ORDER.get(rule_level, 0)
    ml_score = SEVERITY_ORDER.get(ml_level, 0)
    
    if ml_score > rule_score:
        return ml_level
    else:
        return rule_level
