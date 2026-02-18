from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from backend.schemas.internal_models import RiskLevel

class AnalyzeResponse(BaseModel):
    input_id: Optional[str] = None
    final_risk: str
    clinical_confidence: float
    explanation: Dict[str, Any]
    engine_results: Dict[str, Any]
    metadata: Dict[str, Any]
    certification_disclaimer: str
