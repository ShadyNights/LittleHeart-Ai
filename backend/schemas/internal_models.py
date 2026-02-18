from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RuleEngineResult(BaseModel):
    risk_level: RiskLevel
    score: int
    emergency_flags: List[str]
    breakdown: Dict[str, int]

class MLEngineResult(BaseModel):
    probabilities: Dict[str, float]
    predicted_risk: RiskLevel
    confidence: float

class GeminiOutput(BaseModel):
    possible_conditions: List[str]
    reasoning: str
    severity_alignment: RiskLevel
    recommended_action: str
    disclaimer: str
