from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from uuid import UUID
import json
import logging
from datetime import datetime, timedelta
from backend.services.supabase_service import SupabaseService
from backend.schemas.request_schema import AnalyzeRequest
from backend.engines.rule_engine import RuleEngine

logger = logging.getLogger(__name__)

class ChatState(Enum):
    START = "START"
    ASK_AGE = "ASK_AGE"
    ASK_TRIMESTER = "ASK_TRIMESTER"
    ASK_WEEKS = "ASK_WEEKS"
    ASK_BP = "ASK_BP"
    ASK_HB = "ASK_HB"
    ASK_HR = "ASK_HR"
    ASK_SWELLING = "ASK_SWELLING"
    ASK_HEADACHE = "ASK_HEADACHE"
    ASK_BLEEDING = "ASK_BLEEDING"
    ASK_DIABETES = "ASK_DIABETES"
    ASK_COMPLICATIONS = "ASK_COMPLICATIONS"
    ASK_FEVER = "ASK_FEVER"
    ASK_VISION = "ASK_VISION"
    ASK_FETAL_MOVEMENT = "ASK_FETAL_MOVEMENT"
    ASK_ABDOMINAL_PAIN = "ASK_ABDOMINAL_PAIN"
    ANALYZING = "ANALYZING"
    COMPLETE = "COMPLETE"
    ESCALATED = "ESCALATED"

STATE_SEQUENCE = [
    ChatState.ASK_AGE, ChatState.ASK_TRIMESTER, ChatState.ASK_WEEKS,
    ChatState.ASK_BP, ChatState.ASK_HB,
    ChatState.ASK_HR, ChatState.ASK_SWELLING, ChatState.ASK_HEADACHE,
    ChatState.ASK_BLEEDING, ChatState.ASK_DIABETES, ChatState.ASK_COMPLICATIONS,
    ChatState.ASK_FEVER, ChatState.ASK_VISION, ChatState.ASK_FETAL_MOVEMENT,
    ChatState.ASK_ABDOMINAL_PAIN
]

EMERGENCY_SYMPTOMS = ["bleeding", "vision", "fetal_movement", "abdominal_pain"]

class ConversationService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.rule_engine = RuleEngine()

    async def get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        session = self.supabase.client.table("chat_sessions").select("*").eq("user_id", user_id).eq("is_completed", False).order("updated_at", desc=True).limit(1).execute()
        
        if session.data:
            s_data = session.data[0]
            if s_data.get("timeout_at"):
                timeout = datetime.fromisoformat(s_data["timeout_at"].replace("Z", "+00:00"))
                if datetime.now().astimezone() > timeout:
                    self.supabase.client.table("chat_sessions").update({
                        "is_completed": True,
                        "current_state": ChatState.COMPLETE.value,
                        "updated_at": datetime.now().isoformat()
                    }).eq("id", s_data["id"]).execute()
                else:
                    return s_data
            else:
                return s_data
            
        new_session = {
            "user_id": user_id,
            "current_state": ChatState.START.value,
            "collected_data": {},
            "timeout_at": (datetime.now() + timedelta(hours=1)).isoformat()
        }
        res = self.supabase.client.table("chat_sessions").insert(new_session).execute()
        return res.data[0]

    async def process_message(self, user_id: str, session_id: str, message: str) -> Tuple[str, ChatState]:
        session = self.supabase.client.table("chat_sessions").select("*").eq("id", session_id).single().execute()
        if not session.data:
            return "Session not found.", ChatState.COMPLETE

        state = ChatState(session.data["current_state"])
        data = session.data["collected_data"] or {}
        
        self.supabase.client.table("chat_messages").insert({
            "session_id": session_id,
            "sender": "user",
            "content": message
        }).execute()

        next_state, response = self._transition(state, message, data)
        
        emergency_detected = any(kw in message.lower() for kw in ["bleeding", "severe pain", "vision", "movement"])
        if emergency_detected and next_state not in [ChatState.ANALYZING, ChatState.COMPLETE, ChatState.ESCALATED]:
             response = "🚨 EMERGENCY DETECTED: I am notifying our clinical team immediately while we finish the assessment. Please tell me more about your symptoms."

        if next_state == ChatState.ANALYZING:
            response = await self.finalize_assessment(user_id, session_id, data)
            next_state = ChatState.COMPLETE

        self.supabase.client.table("chat_sessions").update({
            "current_state": next_state.value,
            "collected_data": data,
            "updated_at": datetime.now().isoformat()
        }).eq("id", session_id).execute()

        self.supabase.client.table("chat_messages").insert({
            "session_id": session_id,
            "sender": "system",
            "content": response
        }).execute()

        return response, next_state

    def _transition(self, current_state: ChatState, message: str, data: Dict[str, Any]) -> Tuple[ChatState, str]:
        if current_state == ChatState.START:
            return ChatState.ASK_AGE, "Hello! I am LittleHeart AI. I'll help assess your health today. How old are you?"

        val = message.strip()
        
        if current_state == ChatState.ASK_AGE:
            data["age"] = self._parse_int(val)
            return ChatState.ASK_TRIMESTER, "What trimester are you in? (1, 2, or 3)"
            
        if current_state == ChatState.ASK_TRIMESTER:
            data["trimester"] = self._parse_int(val)
            return ChatState.ASK_WEEKS, "How many weeks into your pregnancy are you?"
            
        if current_state == ChatState.ASK_WEEKS:
            data["trimester_weeks"] = self._parse_int(val)
            return ChatState.ASK_BP, "How would you describe your blood pressure? (0 = Low/Normal, 1 = Medium/Elevated, 2 = High)"

        if current_state == ChatState.ASK_BP:
            data["blood_pressure"] = self._parse_int(val)
            return ChatState.ASK_HB, "What is your Hemoglobin level? (e.g. 11.5)"

        if current_state == ChatState.ASK_HB:
            data["hemoglobin"] = self._parse_float(val)
            return ChatState.ASK_HR, "What is your Heart Rate (BPM)?"

        if current_state == ChatState.ASK_HR:
            data["heart_rate"] = self._parse_int(val)
            return ChatState.ASK_SWELLING, "Are you experiencing any swelling in your hands or feet? (Yes/No)"

        if current_state == ChatState.ASK_SWELLING:
            data["swelling"] = self._parse_bool(val)
            return ChatState.ASK_HEADACHE, "Experience any headaches? Rate severity 0-3."

        if current_state == ChatState.ASK_HEADACHE:
            data["headache_severity"] = self._parse_int(val)
            return ChatState.ASK_BLEEDING, "Are you experiencing any vaginal bleeding? (Yes/No)"

        if current_state == ChatState.ASK_BLEEDING:
            data["vaginal_bleeding"] = self._parse_bool(val)
            return ChatState.ASK_DIABETES, "Any history of diabetes? (Yes/No)"

        if current_state == ChatState.ASK_DIABETES:
            data["diabetes_history"] = self._parse_bool(val)
            return ChatState.ASK_COMPLICATIONS, "Any previous pregnancy complications? (Yes/No)"

        if current_state == ChatState.ASK_COMPLICATIONS:
            data["previous_complications"] = self._parse_bool(val)
            return ChatState.ASK_FEVER, "Do you have a fever? (Yes/No)"

        if current_state == ChatState.ASK_FEVER:
            data["fever"] = self._parse_bool(val)
            return ChatState.ASK_VISION, "Any blurred vision or spots? (Yes/No)"

        if current_state == ChatState.ASK_VISION:
            data["blurred_vision"] = self._parse_bool(val)
            return ChatState.ASK_FETAL_MOVEMENT, "Is fetal movement reduced? (Yes/No)"

        if current_state == ChatState.ASK_FETAL_MOVEMENT:
            data["reduced_fetal_movement"] = self._parse_bool(val)
            return ChatState.ASK_ABDOMINAL_PAIN, "Are you in severe abdominal pain? (Yes/No)"

        if current_state == ChatState.ASK_ABDOMINAL_PAIN:
            data["severe_abdominal_pain"] = self._parse_bool(val)
            return ChatState.ANALYZING, "Thank you. I have collected all symptoms. I am now performing a clinical analysis. Please wait..."

        return ChatState.COMPLETE, "Assessment complete. Thank you for using LittleHeart."

    async def finalize_assessment(self, user_id: str, session_id: str, data: Dict[str, Any], request: Optional[Any] = None) -> str:
        """
        Triggers the real clinical analysis once chat data collection is complete.
        """
        from backend.api.analyze import analyze, AnalyzeRequest
        from fastapi import BackgroundTasks
        
        try:
            # 1. Validate data structure
            # Handle potential type mismatches from chat parsing
            processed_data = {
                "age": int(data.get("age", 30)),
                "trimester": int(data.get("trimester", 1)),
                "trimester_weeks": int(data.get("trimester_weeks", 20)),
                "blood_pressure": int(data.get("blood_pressure", 0)),
                "hemoglobin": float(data.get("hemoglobin", 11.0)),
                "heart_rate": int(data.get("heart_rate", 80)),
                "swelling": 1 if data.get("swelling") else 0,
                "headache_severity": int(data.get("headache_severity", 0)),
                "vaginal_bleeding": 1 if data.get("vaginal_bleeding") else 0,
                "diabetes_history": 1 if data.get("diabetes_history") else 0,
                "previous_complications": 1 if data.get("previous_complications") else 0,
                "fever": 1 if data.get("fever") else 0,
                "blurred_vision": 1 if data.get("blurred_vision") else 0,
                "reduced_fetal_movement": 1 if data.get("reduced_fetal_movement") else 0,
                "severe_abdominal_pain": 1 if data.get("severe_abdominal_pain") else 0
            }
            
            # 2. Convert to Pydantic
            analyze_req = AnalyzeRequest(**processed_data)
            
            # 3. Trigger analysis (Background tasks for Gemini/Persistence)
            bg = BackgroundTasks()
            
            # We mock a Request object or pass None if analyze function handles it
            result = await analyze(None, analyze_req, bg, user_id=user_id)
            
            risk = result.final_risk
            
            # 4. Mark session complete
            self.supabase.client.table("chat_sessions").update({
                "is_completed": True,
                "current_state": ChatState.COMPLETE.value,
                "updated_at": datetime.now().isoformat()
            }).eq("id", session_id).execute()
            
            return f"Analysis Complete! Your determined risk level is {risk}. You can view the full clinical breakdown on your dashboard now."
            
        except Exception as e:
            logger.error(f"Chat Finalize Failed: {e}")
            return f"I've collected your data, but there was an error running the final analysis: {str(e)}. Please check your dashboard manually."

    def _parse_int(self, s: str) -> int:
        try:
             import re
             matches = re.findall(r'\d+', s)
             return int(matches[0]) if matches else 0
        except: return 0
        
    def _parse_float(self, s: str) -> float:
        try: 
            import re
            matches = re.findall(r'\d+\.\d+|\d+', s)
            return float(matches[0]) if matches else 0.0
        except: return 0.0
        
    def _parse_bool(self, s: str) -> bool:
        norm = s.lower().strip()
        if norm in ["yes", "y", "true", "1", "yep", "sure"]: return True
        return False
