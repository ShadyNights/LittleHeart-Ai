import httpx
import os
import websocket
import threading
import json
import streamlit as st
from typing import Dict, Any, List

# Hardcode to 127.0.0.1 for stability on local Windows
API_BASE = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/alerts"

def analyze_patient(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sends patient data to the backend risk assessment engine."""
    try:
        headers = {}
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        # Increased timeout to 60s for deep clinical analysis
        response = httpx.post(f"{API_BASE}/analyze", json=data, headers=headers, timeout=60.0)
        
        if response.status_code == 401:
            return {
                "final_risk": "ERROR", 
                "confidence": 0, 
                "explanation": {"reasoning": "Authentication token expired. Please reload the page and log in again."}, 
                "engine_results": {"ml": {}}
            }
            
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {
            "final_risk": "ERROR", 
            "confidence": 0, 
            "explanation": {"reasoning": str(e)}, 
            "engine_results": {"ml": {}}
        }

def fetch_risk_history() -> List[Dict]:
    """Fetches real past assessments from the backend."""
    try:
        headers = {}
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        response = httpx.get(f"{API_BASE}/history", headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Fallback to empty list or minimal log
        return []

def init_chat_session() -> Dict[str, Any]:
    """Initializes a new or existing chat session for the user."""
    try:
        headers = {}
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = httpx.get(f"{API_BASE}/chat/init", headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"session_id": "fallback", "state": "START", "error": str(e)}

def call_chatbot_api(session_id: str, message: str) -> Dict[str, Any]:
    """Sends a message to the backend conversation service."""
    try:
        headers = {}
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = {"session_id": session_id, "message": message}
        response = httpx.post(f"{API_BASE}/chat/message", json=data, headers=headers, timeout=20.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"response": f"Assistant is having connection issues: {str(e)}", "next_state": "START"}

def fetch_admin_metrics() -> Dict[str, Any]:
    """Fetches system-wide metrics for admin dashboard."""
    # Mocking for immediate UI rendering if backend endpoint differs
    return {
        "total": 1240, 
        "high_percent": 14.5, 
        "latency": 0.45,
        "distribution": [
            {"risk": "LOW", "count": 800}, 
            {"risk": "MEDIUM", "count": 300}, 
            {"risk": "HIGH", "count": 100}, 
            {"risk": "CRITICAL", "count": 40}
        ],
        "weekly_alerts": [
            {"day": "Mon", "count": 12},
            {"day": "Tue", "count": 19},
            {"day": "Wed", "count": 3},
            {"day": "Thu", "count": 5},
            {"day": "Fri", "count": 2},
            {"day": "Sat", "count": 20},
            {"day": "Sun", "count": 15}
        ]
    }

def fetch_alerts() -> List[Dict]:
    """Fetches recent alerts (polling fallback or WS buffer)."""
    if "live_alerts" in st.session_state:
        return st.session_state["live_alerts"]
    return []

# --- WebSocket Logic ---

def _on_message(ws, message):
    try:
        data = json.loads(message)
        if "live_alerts" not in st.session_state:
            st.session_state["live_alerts"] = []
        st.session_state["live_alerts"].insert(0, data)
        # Keep only last 50
        if len(st.session_state["live_alerts"]) > 50:
            st.session_state["live_alerts"].pop()
    except Exception:
        pass

def _on_error(ws, error):
    pass

def _on_close(ws, close_status_code, close_msg):
    pass

def _start_listener():
    ws = websocket.WebSocketApp(WS_URL,
                                on_message=_on_message,
                                on_error=_on_error,
                                on_close=_on_close)
    ws.run_forever()

def init_websocket():
    """Starts the WebSocket listener in a background thread if not already running."""
    if "ws_thread_started" not in st.session_state:
        t = threading.Thread(target=_start_listener)
        t.daemon = True
        t.start()
        st.session_state["ws_thread_started"] = True
