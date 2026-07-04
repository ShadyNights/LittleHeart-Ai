import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.services.supabase_service import SupabaseService
from backend.config import settings

async def verify_db():
    print(f"Checking Supabase connection to: {settings.SUPABASE_URL}")
    db = SupabaseService()
    if not db.client:
        print("❌ Supabase client failed to initialize. Check URL and Key.")
        return False
        
    try:
        # Try to select from patient_inputs to verify table exists
        response = db.client.table("patient_inputs").select("id", count="exact").limit(1).execute()
        print("✅ Database connection successful!")
        
        # Now try to insert a dummy row to test schema compliance, but wait we can't rollback easily 
        # with supabase client. Instead, let's just do a select asking for the new columns.
        try:
            db.client.table("patient_inputs").select("blood_pressure_systolic, blood_pressure_diastolic").limit(1).execute()
            print("✅ Database schema is up-to-date (raw BP columns exist).")
        except Exception as e:
            print(f"⚠️ Database schema mismatch! Error: {e}")
            print("❌ Have you run the updated database_schema.sql in your Supabase SQL Editor?")
            return False
            
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_db())
