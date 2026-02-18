import httpx
import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger("APIClient")

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_supabase_client = None


def _get_supabase():
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase import create_client
            if SUPABASE_URL and SUPABASE_KEY:
                _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception as e:
            logger.error(f"Supabase init error: {e}")
    return _supabase_client


def check_health() -> Dict[str, Any]:
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=5)
        return r.json()
    except Exception:
        return {"status": "unreachable"}


def run_analysis(data: Dict[str, Any], token: str = "") -> Optional[Dict]:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = httpx.post(f"{API_BASE}/analyze", json=data, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return None


def init_chat(user_id: str, token: str = "") -> Optional[str]:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = httpx.post(f"{API_BASE}/chat/init", json={"user_id": user_id}, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json().get("session_id")
    except Exception as e:
        logger.error(f"Chat init error: {e}")
        return None


def send_chat(session_id: str, message: str, token: str = "") -> Optional[Dict]:
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = httpx.post(f"{API_BASE}/chat/message",
                       json={"session_id": session_id, "message": message},
                       headers=headers, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return None


def fetch_risk_history(user_id: str = "") -> List[Dict]:
    db = _get_supabase()
    if not db:
        return []
    try:
        q = db.table("patient_risk_history").select("*").order("recorded_at", desc=True).limit(50)
        if user_id:
            q = q.eq("user_id", user_id)
        return q.execute().data or []
    except Exception as e:
        logger.error(f"History fetch error: {e}")
        return []


def fetch_alerts(limit: int = 20) -> List[Dict]:
    db = _get_supabase()
    if not db:
        return []
    try:
        return db.table("alerts").select("*").order("created_at", desc=True).limit(limit).execute().data or []
    except Exception as e:
        logger.error(f"Alerts fetch error: {e}")
        return []


def fetch_assigned_patients(doctor_id: str) -> List[Dict]:
    db = _get_supabase()
    if not db:
        return []
    try:
        assignments = db.table("patient_assignments").select("patient_id").eq("doctor_id", doctor_id).execute().data or []
        patient_ids = [a["patient_id"] for a in assignments]
        if not patient_ids:
            return []
        patients = []
        for pid in patient_ids:
            profile = db.table("user_profiles").select("id, full_name, role").eq("id", pid).single().execute()
            history = db.table("patient_risk_history").select("risk_level, recorded_at").eq("user_id", pid).order("recorded_at", desc=True).limit(1).execute()
            alerts = db.table("alerts").select("id").eq("user_id", pid).eq("status", "pending").execute()
            latest = history.data[0] if history.data else {}
            patients.append({
                "id": pid,
                "full_name": profile.data.get("full_name", "Unknown") if profile.data else "Unknown",
                "latest_risk": latest.get("risk_level", "N/A"),
                "last_assessed": latest.get("recorded_at", "Never")[:16] if latest.get("recorded_at") else "Never",
                "pending_alerts": len(alerts.data) if alerts.data else 0
            })
        return patients
    except Exception as e:
        logger.error(f"Patients fetch error: {e}")
        return []


def fetch_admin_stats() -> Dict[str, Any]:
    db = _get_supabase()
    if not db:
        return {}
    try:
        results = db.table("engine_results").select("final_risk, created_at").execute().data or []
        alerts = db.table("alerts").select("id").execute().data or []
        total = len(results)
        high = sum(1 for r in results if r.get("final_risk") in ["HIGH", "CRITICAL"])
        pct = round((high / total * 100), 1) if total > 0 else 0
        drift = db.table("model_drift_logs").select("*").order("created_at", desc=True).limit(20).execute().data or []
        return {
            "total_assessments": total,
            "high_risk_count": high,
            "high_risk_pct": pct,
            "total_alerts": len(alerts),
            "drift_logs": drift
        }
    except Exception as e:
        logger.error(f"Admin stats error: {e}")
        return {}


def fetch_recent_assessments(limit: int = 25) -> List[Dict]:
    db = _get_supabase()
    if not db:
        return []
    try:
        return db.table("engine_results").select("*").order("created_at", desc=True).limit(limit).execute().data or []
    except Exception as e:
        logger.error(f"Assessments fetch error: {e}")
        return []
