from backend.schemas.request_schema import AnalyzeRequest
import pandas as pd

def preprocess_input(data: AnalyzeRequest) -> pd.DataFrame:
    feature_dict = {
        "Age": data.age,
        "Trimester": data.trimester,
        "Blood Pressure": data.blood_pressure,
        "Hemoglobin (Hb)": data.hemoglobin,
        "Swelling": data.swelling,
        "Headache Severity": data.headache_severity,
        "Vaginal Bleeding": data.vaginal_bleeding,
        "Severe Abdominal Pain": data.severe_abdominal_pain,
        "Reduced Fetal Movement": data.reduced_fetal_movement,
        "Diabetes History": data.diabetes_history,
        "Previous Pregnancy Complications": data.previous_complications,
        "Fever": data.fever,
        "Blurred Vision": data.blurred_vision,
        "Heart Rate": data.heart_rate,
        "Trimester Weeks": data.trimester_weeks
    }
    return pd.DataFrame([feature_dict])
