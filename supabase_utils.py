from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = "https://bqolqgyjlankyxbkxsxb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJxb2xxZ3lqbGFua3l4Ymt4c3hiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDkyNjIyNCwiZXhwIjoyMDY2NTAyMjI0fQ.2oNrmnQxdvKUJ72sRnHJ0wmC1mDtyVjTVkmCNv4D2HU"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- USER PROFILES TABLE ----------
def insert_user_data(name: str, status: str, website: str):
    data = {
        "name": name,
        "status": status,
        "website": website
    }
    response = supabase.table("user_profiles").insert(data).execute()
    return response.data

def fetch_user_data():
    response = supabase.table("user_profiles").select("*").execute()
    return response.data

# ---------- BUSINESS TABLE ----------
def insert_business_data(name: str, status: str, website: str):
    data = {
        "name": name,
        "status": status,
        "website": website
    }
    response = supabase.table("business").insert(data).execute()
    return response.data

def fetch_business_data():
    response = supabase.table("business").select("*").execute()
    return response.data
