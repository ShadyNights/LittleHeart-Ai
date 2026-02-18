import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@hospital.com")
    ENV = os.getenv("ENV", "development")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
    
    POOL_MAX_SIZE = int(os.getenv("POOL_MAX_SIZE", "50"))
    POOL_TIMEOUT = float(os.getenv("POOL_TIMEOUT", "30.0"))
    GEMINI_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT", "20.0"))
    
    VERSION_MANIFEST = {
        "api": "4.0.0-dev",
        "rule_engine": "v2.1-clinical-prototype",
        "ml_engine": "xgb-maternal-v1.4-dev",
        "build_id": os.getenv("BUILD_ID", "DEV-RESEARCH-HARNESS")
    }

settings = Config()
