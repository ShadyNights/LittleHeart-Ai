import os
import joblib
import pandas as pd
import logging
from typing import Dict, Any, List
from backend.schemas.request_schema import AnalyzeRequest
from backend.schemas.internal_models import MLEngineResult, RiskLevel

class MLEngine:
    def __init__(self, model_path: str = None):
        self.logger = logging.getLogger(__name__)
        if model_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = os.path.join(base_dir, "..", "model", "maternal_health_model_50k.pkl")
        else:
            self.model_path = model_path
        self.model_package = None
        self.pipeline = None
        self.feature_names = []
        self.label_encoder = None
        self._load_model()

    def _load_model(self):
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"ML Model not found at: {self.model_path}")
            self.model_package = joblib.load(self.model_path)
            self.pipeline = self.model_package['pipeline']
            self.feature_names = self.model_package['feature_names']
            self.label_encoder = self.model_package['label_encoder']
            if self.pipeline and hasattr(self.pipeline, "steps"):
                 if self.pipeline.steps and hasattr(self.pipeline.steps[-1][1], "feature_names_in_"):
                      model_features = self.pipeline.steps[-1][1].feature_names_in_
                      if list(self.feature_names) != list(model_features):
                           raise ValueError("Feature names mismatch with trained model.")
        except Exception as e:
            self.logger.critical(f"Failed to load ML model: {str(e)}")
            raise e


    def _preprocess(self, patient: AnalyzeRequest) -> pd.DataFrame:
        data = {
            "Age": patient.age,
            "Trimester": patient.trimester,
            "Blood Pressure": patient.blood_pressure,
            "Hemoglobin (Hb)": patient.hemoglobin,
            "Swelling": patient.swelling,
            "Headache Severity": patient.headache_severity,
            "Vaginal Bleeding": patient.vaginal_bleeding,
            "Severe Abdominal Pain": patient.severe_abdominal_pain,
            "Reduced Fetal Movement": patient.reduced_fetal_movement,
            "Diabetes History": patient.diabetes_history,
            "Previous Pregnancy Complications": patient.previous_complications,
            "Fever": patient.fever,
            "Blurred Vision": patient.blurred_vision,
            "Heart Rate": patient.heart_rate,
            "Trimester Weeks": patient.trimester_weeks
        }
        for m in [f for f in self.feature_names if f not in data]:
            data[m] = 0
        df = pd.DataFrame([data], columns=self.feature_names)
        if list(df.columns) != self.feature_names:
            raise ValueError("Feature alignment mismatch.")
        return df

    def predict(self, patient: AnalyzeRequest) -> MLEngineResult:
        if not self.pipeline:
             raise RuntimeError("ML Pipeline is not loaded.")
        X = self._preprocess(patient)
        probs = self.pipeline.predict_proba(X)[0]
        pred_idx = self.pipeline.predict(X)[0]
        pred_label = self.label_encoder.inverse_transform([pred_idx])[0]
        prob_dict = {cls: float(probs[i]) for i, cls in enumerate(self.label_encoder.classes_)}
        risk_map = {"Low": RiskLevel.LOW, "Medium": RiskLevel.MEDIUM, "High": RiskLevel.HIGH}
        return MLEngineResult(
            predicted_risk=risk_map.get(pred_label, RiskLevel.LOW),
            probabilities=prob_dict,
            confidence=float(max(probs))
        )
