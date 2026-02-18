import logging
from typing import Dict, Any, List, Optional
from backend.schemas.request_schema import AnalyzeRequest
from backend.schemas.internal_models import RuleEngineResult, RiskLevel

AGE_SCORE = [
    (16, 17, 2),
    (18, 34, 0),
    (35, 45, 2),
    (46, 60, 3)
]

BP_SCORE = {
    0: 0,
    1: 5,
    2: 10
}

HEADACHE_SCORE = {
    0: 0,
    1: 1,
    2: 2,
    3: 3
}

BINARY_SCORE = {
    "swelling": 2,
    "vaginal_bleeding": 5,
    "diabetes_history": 2,
    "previous_complications": 3,
    "fever": 2,
    "blurred_vision": 2,
    "reduced_fetal_movement": 4,
    "severe_abdominal_pain": 5
}

def match_score(value, rules):
    if isinstance(rules, dict):
        return rules.get(value, 0)
    for min_v, max_v, score in rules:
        if min_v <= value <= max_v:
            return score
    return 0

def get_hb_normal_range(trimester: int):
    if trimester == 2:
        return 10.5, 14.0
    return 11.0, 14.0

def get_hr_normal_range():
    return 60, 100

class RuleEngine:
    def evaluate(self, patient: AnalyzeRequest) -> RuleEngineResult:
        emergency_flags = []
        risk_breakdown = {}
        
        bp_cat = patient.blood_pressure
        if bp_cat == 2:
            emergency_flags.append("Severe Hypertension (High Category)")
        elif bp_cat >= 1 and (patient.blurred_vision == 1 or patient.headache_severity >= 2):
            emergency_flags.append("Hypertension with Neuro Symptoms")
        
        if patient.vaginal_bleeding == 1:
            emergency_flags.append("Vaginal Bleeding")
            
        if patient.severe_abdominal_pain == 1 and patient.trimester >= 2:
            emergency_flags.append("Severe Abdominal Pain")
            
        if patient.reduced_fetal_movement == 1 and patient.trimester == 3:
            emergency_flags.append("Reduced Fetal Movement (Late Pregnancy)")
            
        if patient.hemoglobin < 7.0:
            emergency_flags.append("Severe Anemia")
            
        risk_breakdown["age"] = match_score(patient.age, AGE_SCORE)
        risk_breakdown["blood_pressure"] = match_score(bp_cat, BP_SCORE)
        
        hb = patient.hemoglobin
        hb_min, _ = get_hb_normal_range(patient.trimester)
        
        if hb < 7:
            risk_breakdown["hemoglobin"] = 10
        elif hb < hb_min:
             risk_breakdown["hemoglobin"] = 4
        else:
             risk_breakdown["hemoglobin"] = 0
             
        risk_breakdown["headache"] = HEADACHE_SCORE.get(patient.headache_severity, 0)
        
        for field, points in BINARY_SCORE.items():
            val = getattr(patient, field, 0)
            if field == "reduced_fetal_movement":
                continue
            if val == 1:
                risk_breakdown[field] = points
                
        if patient.reduced_fetal_movement == 1:
            if patient.trimester == 2:
                 risk_breakdown["reduced_fetal_movement"] = 2
            else:
                 risk_breakdown["reduced_fetal_movement"] = 4
        
        hr_min, hr_max = get_hr_normal_range()
        if not (hr_min <= patient.heart_rate <= hr_max):
            risk_breakdown["heart_rate"] = 2
        
        if bp_cat >= 1 and patient.headache_severity >= 2:
            risk_breakdown["interaction_bp_headache"] = 2
            
        total_score = sum(risk_breakdown.values())
        
        if emergency_flags:
            risk_level = RiskLevel.CRITICAL
        elif total_score >= 10:
            risk_level = RiskLevel.HIGH
        elif total_score >= 5:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
            
        return RuleEngineResult(
            risk_level=risk_level,
            score=total_score,
            emergency_flags=emergency_flags,
            breakdown=risk_breakdown
        )
