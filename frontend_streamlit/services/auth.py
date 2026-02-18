import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client globally if possible to reuse connection
try:
    from supabase import create_client, Client
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
except Exception as e:
    supabase = None
    print(f"Supabase init error: {e}")

def login_user(email, password):
    """
    Authenticates user with Supabase and returns their role.
    Returns None if authentication fails.
    """
    if not supabase:
        return None
        
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user:
            # Fetch role from user_profiles table
            profile = supabase.table("user_profiles").select("role").eq("id", res.user.id).single().execute()
            
            role = "patient"
            if profile.data:
                role = profile.data.get("role", "patient")
                
            token = res.session.access_token if res.session else None
            return role, token
    except Exception as e:
        print(f"Login failed: {e}")
        return None, None
    return None, None

def sign_up_user(email, password, role="patient"):
    """
    Registers a new user and creates a profile.
    """
    if not supabase:
        return False, "Supabase not initialized"
    
    try:
        # 1. Sign up user
        res = supabase.auth.sign_up({"email": email, "password": password})
        
        if res.user and res.user.id:
            # 2. Key Step: Create Profile for Role
            # Note: Verify if your DB has a trigger. If not, this is needed.
            # We try to insert, ignoring duplicates if trigger exists.
            try:
                supabase.table("user_profiles").insert([
                    {"id": res.user.id, "email": email, "role": role}
                ]).execute()
            except Exception as e:
                # Often triggers auto-create profile, so this might fail harmlessly
                print(f"Profile creation note: {e}")
                
            return True, "Account created! Please check your email to confirm."
        return False, "Sign up failed."
    except Exception as e:
        return False, str(e)

def reset_password(email):
    """
    Sends a password reset email.
    """
    if not supabase:
        return False, "Supabase not initialized"
        
    try:
        supabase.auth.reset_password_email(email)
        return True, "Password reset email sent!"
    except Exception as e:
        return False, str(e)
