import streamlit as st
import os
from typing import Optional, Dict, Any

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


def _get_or_create_client():
    if "supabase_client" not in st.session_state:
        try:
            from supabase import create_client
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            st.session_state["supabase_client"] = client
            return client
        except Exception as e:
            st.error(f"Failed to initialize Supabase: {e}")
            return None
    return st.session_state["supabase_client"]


def sign_in(email: str, password: str) -> Dict[str, Any]:
    client = _get_or_create_client()
    if not client:
        return {"error": "Supabase client not available"}
    try:
        res = client.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            st.session_state["access_token"] = res.session.access_token
            st.session_state["user_id"] = res.user.id
            st.session_state["user_email"] = res.user.email
            st.session_state["authenticated"] = True

            profile = client.table("user_profiles").select("role, full_name").eq("id", res.user.id).single().execute()
            if profile.data:
                st.session_state["user_role"] = profile.data.get("role", "patient")
                st.session_state["user_name"] = profile.data.get("full_name", "User")
            else:
                st.session_state["user_role"] = "patient"
                st.session_state["user_name"] = "User"

            return {"success": True, "role": st.session_state["user_role"]}
        return {"error": "Authentication failed"}
    except Exception as e:
        error_msg = str(e)
        if "Invalid login" in error_msg or "invalid" in error_msg.lower():
            return {"error": "Invalid email or password"}
        return {"error": error_msg}


def sign_up(email: str, password: str, full_name: str) -> Dict[str, Any]:
    client = _get_or_create_client()
    if not client:
        return {"error": "Supabase client not available"}
    try:
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"full_name": full_name}},
        })
        if res.user:
            return {"success": True, "message": "Account created. Please check your email to verify, then log in."}
        return {"error": "Sign up failed"}
    except Exception as e:
        return {"error": str(e)}


def sign_out():
    client = _get_or_create_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass
    for key in ["access_token", "user_id", "user_email", "user_role", "user_name", "authenticated", "supabase_client"]:
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False) and st.session_state.get("access_token") is not None


def get_role() -> str:
    return st.session_state.get("user_role", "patient")


def get_user_name() -> str:
    return st.session_state.get("user_name", "User")


def require_auth():
    if not is_authenticated():
        st.warning("🔒 Please log in to access this page.")
        st.stop()


def require_role(allowed_roles: list):
    require_auth()
    role = get_role()
    if role not in allowed_roles:
        st.error(f"⛔ Access denied. This page requires one of: {', '.join(allowed_roles)}")
        st.stop()
