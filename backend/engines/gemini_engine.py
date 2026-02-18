import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Dict, Any, Optional, List

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

from backend.schemas.internal_models import RiskLevel, GeminiOutput
from backend.schemas.request_schema import AnalyzeRequest
from backend.services.metrics_service import MetricsService

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TIMEOUT_SECONDS = 3.0
logger = logging.getLogger(__name__)

class GeminiEngine:
    HALLUCINATION_WATCHLIST = [
        "proteinuria", "seizure", "bleeding", "visual disturbances", 
        "epigastric pain", "fetal movement", "contractions", "leaking"
    ]
    FORBIDDEN_MEDS = [
        "aspirin", "labetalol", "magnesium", "nifedipine", "methyldopa", 
        "prescribe", "dosage", "mg", "tablet", "injection"
    ]

    _failure_count = 0
    _last_failure_time = 0.0
    _circuit_open = False
    CIRCUIT_THRESHOLD = 3
    COOLDOWN_PERIOD = 300

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key) if genai and api_key else None
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = os.path.join(BASE_DIR, "prompt_template.txt")
        if not os.path.exists(prompt_path):
             return "Explain the risk level {RISK_LEVEL} for symptoms: {SYMPTOM_TEXT}. Return JSON."
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _format_symptoms(self, data: AnalyzeRequest, rule_result: Any, ml_result: Any, final_risk: RiskLevel) -> str:
        bp_label = {0: "Low", 1: "Medium", 2: "High"}.get(data.blood_pressure, "Unknown")
        lines = [
            f"Patient Age: {data.age}",
            f"Trimester: {data.trimester}",
            f"Trimester Weeks: {data.trimester_weeks}",
            f"Blood Pressure: {bp_label} Category",
            f"Heart Rate: {data.heart_rate} bpm",
            f"Hemoglobin: {data.hemoglobin}",
            "Complaints:",
        ]
        if data.swelling: lines.append("- Swelling")
        if data.headache_severity > 0: lines.append(f"- Headache (Severity {data.headache_severity})")
        if data.vaginal_bleeding: lines.append("- Vaginal Bleeding")
        if data.severe_abdominal_pain: lines.append("- Severe Abdominal Pain")
        if data.reduced_fetal_movement: lines.append("- Reduced Fetal Movement")
        if data.blurred_vision: lines.append("- Blurred Vision")
        if data.fever: lines.append("- Fever")
        if data.diabetes_history: lines.append("- History of Diabetes")
        if data.previous_complications: lines.append("- Previous Pregnancy Complications")
        lines.append(f"\nTechnical Assessment:\nRule Engine Risk: {rule_result.risk_level.value}")
        lines.append(f"Rule Flags: {', '.join(rule_result.emergency_flags)}")
        lines.append(f"ML Predicted Risk: {ml_result.predicted_risk.value if ml_result else 'N/A'}")
        if ml_result and hasattr(ml_result, 'probabilities') and ml_result.probabilities:
             lines.append(f"ML Probabilities: {', '.join([f'{k}: {v:.2f}' for k, v in ml_result.probabilities.items()])}")
        lines.append(f"\nFINAL DETERMINED RISK LEVEL: {final_risk.value}")
        return "\n".join(lines)

    def _check_circuit(self) -> bool:
        if GeminiEngine._circuit_open:
            if time.time() - GeminiEngine._last_failure_time > GeminiEngine.COOLDOWN_PERIOD:
                GeminiEngine._circuit_open = False
                GeminiEngine._failure_count = 0
                logger.info("Gemini Circuit CLOSED (Resetting)")
                return True
            return False
        return True

    def _handle_failure(self):
        GeminiEngine._failure_count += 1
        GeminiEngine._last_failure_time = time.time()
        if GeminiEngine._failure_count >= GeminiEngine.CIRCUIT_THRESHOLD:
            GeminiEngine._circuit_open = True
            logger.critical("GEMINI_CIRCUIT_OPEN: Too many failures. Entering cooldown.")

    def _call_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        for attempt in range(max_retries + 1):
            try:
                if not self.client: raise RuntimeError("Gemini Client not ready.")
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=400, response_mime_type="application/json")
                )
                GeminiEngine._failure_count = 0 
                MetricsService.record_success("gemini")
                return response.text
            except Exception as e:
                err_msg = str(e).lower()
                is_retryable = "429" in err_msg or "500" in err_msg or "timeout" in err_msg or "deadline" in err_msg
                if attempt < max_retries and is_retryable:
                    wait = (2 ** attempt) + (0.1 * attempt)
                    logger.warning(f"Gemini Retry {attempt+1}/{max_retries} after {wait}s due to: {e}")
                    time.sleep(wait)
                else:
                    self._handle_failure()
                    MetricsService.record_error("gemini", type(e).__name__)
                    raise

    def explain(self, data: AnalyzeRequest, final_risk: RiskLevel, rule_result: Any, ml_result: Any) -> Dict[str, Any]:
        if not self.client:
            return self._fallback(final_risk, "Gemini Infrastructure Offline: Missing API Key")
            
        if not self._check_circuit():
            return self._fallback(final_risk, "Circuit Breaker Open: Infrastructure Cooldown")

        symptom_text = self._format_symptoms(data, rule_result, ml_result, final_risk)
        final_prompt = self.prompt_template.replace("{SYMPTOM_TEXT}", symptom_text)
        executor = ThreadPoolExecutor(max_workers=1)
        from backend.services.audit_logger import AuditLogger
        try:
            future = executor.submit(self._call_with_retry, final_prompt)
            json_str = future.result(timeout=TIMEOUT_SECONDS + 17)
            cleaned = json_str.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:-3]
            elif cleaned.startswith("```"): cleaned = cleaned[3:-3]
            
            try:
                parsed_json = json.loads(cleaned)
                validated_output = GeminiOutput.model_validate(parsed_json)
                parsed = validated_output.model_dump()
            except Exception as format_err:
                AuditLogger.log_action(None, "llm_format_violation", {"error": str(format_err), "raw_output": cleaned})
                raise

            if parsed.get("severity_alignment", "").upper() != final_risk.value:
                parsed["severity_alignment"] = final_risk.value
            combined = f"{parsed.get('reasoning', '')} {parsed.get('recommended_action', '')}".lower()
            if any(med in combined for med in self.FORBIDDEN_MEDS):
                AuditLogger.log_action(None, "llm_safety_violation", {"violation": "forbidden_content", "content": combined})
                return self._fallback(final_risk, "Safety Violation: Prohibited Medical Content")
            return parsed
        except Exception as e:
            return self._fallback(final_risk, f"AI Component Unavailable: {str(e)}")
        finally:
            executor.shutdown(wait=False)

    def _fallback(self, final_risk: RiskLevel, reason: str) -> Dict[str, Any]:
        return {
            "possible_conditions": ["Analysis limited due to infrastructure safety protocols."],
            "reasoning": f"Automated stability fallback triggered. Risk consistency verified at: {final_risk.value}. ({reason})",
            "severity_alignment": final_risk.value,
            "recommended_action": "Seek professional medical evaluation immediately if symptoms are severe.",
            "disclaimer": "LITTLEHEART AI: This is a software fallback analysis. Not a medical diagnosis."
        }
