from pydantic import BaseModel, Field
from typing import Optional
from backend.utils.constants import (
    AGE_MIN, AGE_MAX, TRIMESTER_MIN, TRIMESTER_MAX, WEEKS_MIN, WEEKS_MAX,
    HR_MIN, HR_MAX, HB_MIN, HB_MAX, BP_CAT_MIN, BP_CAT_MAX
)

class AnalyzeRequest(BaseModel):
    age: int = Field(..., ge=AGE_MIN, le=AGE_MAX)
    trimester: int = Field(..., ge=TRIMESTER_MIN, le=TRIMESTER_MAX)
    trimester_weeks: int = Field(..., ge=WEEKS_MIN, le=WEEKS_MAX)
    blood_pressure: int = Field(..., ge=BP_CAT_MIN, le=BP_CAT_MAX)
    heart_rate: int = Field(..., ge=HR_MIN, le=HR_MAX)
    hemoglobin: float = Field(..., ge=HB_MIN, le=HB_MAX)
    swelling: int = Field(..., ge=0, le=1)
    headache_severity: int = Field(..., ge=0, le=3)
    vaginal_bleeding: int = Field(..., ge=0, le=1)
    severe_abdominal_pain: int = Field(..., ge=0, le=1)
    reduced_fetal_movement: int = Field(..., ge=0, le=1)
    blurred_vision: int = Field(..., ge=0, le=1)
    fever: int = Field(..., ge=0, le=1)
    diabetes_history: int = Field(..., ge=0, le=1)
    previous_complications: int = Field(..., ge=0, le=1)
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None

class ChatRequest(BaseModel):
    session_id: str
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "age": 30, "trimester": 3, "trimester_weeks": 32,
                "blood_pressure": 0,
                "heart_rate": 80, "hemoglobin": 11.5, "swelling": 0,
                "headache_severity": 0, "vaginal_bleeding": 0,
                "severe_abdominal_pain": 0, "reduced_fetal_movement": 0,
                "blurred_vision": 0, "fever": 0, "diabetes_history": 0,
                "previous_complications": 0
            }
        }
