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
            # Fetch role from user_profiles table - gracefully handle if not found yet
            try:
                profile = supabase.table("user_profiles").select("role").eq("id", res.user.id).single().execute()
                role = profile.data.get("role", "patient") if profile.data else "patient"
            except Exception as e:
                print(f"Profile lookup note: {e}")
                role = "patient" # Default fallback
                
            token = res.session.access_token if res.session else None
            return role, token
    except Exception as e:
        print(f"Login failed: {e}")
        return None, None
    return None, None

def sign_up_user(email, password, full_name, role="patient"):
    """
    Registers a new user. The DB trigger 'on_auth_user_created' 
    handles profile creation using full_name from user_metadata.
    """
    if not supabase:
        return False, "Supabase not initialized"
    
    try:
        # Sign up user with full_name in metadata so trigger can pick it up
        res = supabase.auth.sign_up({
            "email": email, 
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "role": role
                }
            }
        })
        
        if res.user:
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
