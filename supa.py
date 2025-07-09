from supabase import create_client, Client
import json
import os
from typing import List

# Store per-user Supabase credentials in a local JSON file
CREDENTIALS_FILE = "supabase_credentials.json"


def save_supabase_credentials(business_name, supabase_url, supabase_key):
    # Save credentials to JSON using business name as key
    data = {}
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as file:
            data = json.load(file)
    data[business_name] = {
        "url": supabase_url,
        "key": supabase_key
    }
    with open(CREDENTIALS_FILE, "w") as file:
        json.dump(data, file)


def load_supabase_client(business_name):
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    with open(CREDENTIALS_FILE, "r") as file:
        data = json.load(file)
        if business_name in data:
            creds = data[business_name]
            return create_client(creds["url"], creds["key"])
    return None


# Insert user profile into a shared table "data"
def insert_user_profile(supabase: Client, name, status, contacts, location, password):
    data = {
        "name": name,
        "status": status,
        "contacts": contacts,
        "location": location,
        "password": password
    }
    result = supabase.table("data").insert(data).execute()
    return result.data


# Fetch user profile for login validation
def get_user_profile(supabase: Client, business_name):
    result = supabase.table("data").select("*").eq("name", business_name).execute()
    if result.data:
        return result.data[0]
    return None


# Upload file metadata (store filename and URL in the "data" table)
def upload_file_metadata(supabase: Client, business_name: str, file_url: str, filename: str):
    data = {
        "name": business_name,
        "file_url": file_url,
        "filename": filename
    }
    result = supabase.table("data").insert(data).execute()
    return result.data


# List uploaded files for a specific business name
def list_uploaded_files(supabase: Client, business_name: str) -> List[dict]:
    result = supabase.table("data").select("*").eq("name", business_name).execute()
    files = []
    for item in result.data:
        if "file_url" in item and item["file_url"]:
            files.append({
                "id": item.get("id"),
                "filename": item.get("filename"),
                "url": item.get("file_url")
            })
    return files


# Delete a file record from Supabase table "data"
def delete_file_metadata(supabase: Client, file_id: int):
    result = supabase.table("data").delete().eq("id", file_id).execute()
    return result.data
