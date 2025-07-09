from supabase import create_client
import traceback

SUPABASE_URL = "https://bqolqgyjlankyxbkxsxb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJxb2xxZ3lqbGFua3l4Ymt4c3hiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDkyNjIyNCwiZXhwIjoyMDY2NTAyMjI0fQ.2oNrmnQxdvKUJ72sRnHJ0wmC1mDtyVjTVkmCNv4D2HU"
BUCKET = "pdfs"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)







def upload_file_to_supabase(file_obj, filename, title):
    try:
        # Read the file as bytes
        file_bytes = file_obj.read()

        # Upload file to Supabase bucket
        response = supabase.storage.from_(BUCKET).upload(filename, file_bytes)

        if hasattr(response, "error") and response.error:
            return {"status": "error", "message": response.error.message}

        # Get the public URL (directly a string, not a dict)
        public_url = supabase.storage.from_(BUCKET).get_public_url(filename)

        if not isinstance(public_url, str) or not public_url.strip():
            return {"status": "error", "message": "Failed to get valid public URL"}

        # Insert metadata into 'documents' table
        data = {"title": title, "file_url": public_url}
        result = supabase.table("documents").insert(data).execute()

        if hasattr(result, "error") and result.error:
            return {"status": "error", "message": str(result.error)}

        return {"status": "success", "url": public_url, "result": result.data}

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}













def fetch_documents():
    try:
        response = supabase.table("documents").select("*").order("created_at", desc=True).execute()

        if hasattr(response, "error") and response.error:
            return []

        return getattr(response, "data", response) or []

    except Exception as e:
        print("Exception fetching documents:", e)
        return []














def delete_file_from_supabase(filename, doc_id):
    try:
        # Delete the file from storage
        storage_response = supabase.storage.from_(BUCKET).remove([filename])

        if hasattr(storage_response, "error") and storage_response.error:
            return {"status": "error", "message": storage_response.error.message}

        # Delete the record from the documents table
        db_response = supabase.table("documents").delete().eq("id", doc_id).execute()

        if hasattr(db_response, "error") and db_response.error:
            return {"status": "error", "message": db_response.error.message}

        return {"status": "success", "message": "File and metadata deleted."}

    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

















import pandas as pd
import os
import numpy as np
import re
import pdfplumber
from datetime import datetime
import calendar

# -----------------------------
# ECOCROPPROCESSOR CLASS EXACTLY AS PROVIDED
# -----------------------------

class EcoCropProcessor:
    def __init__(self, path):
        self.df = pd.read_csv(path, encoding='ISO-8859-1')
        self.df['COMNAME'] = self.df['COMNAME'].astype(str).str.lower()
        self.selected_crop_data = None
        self.selected_district_forecast = None

    def search_crops(self, keyword):
        keyword = keyword.lower().strip()
        matched_rows = self.df[self.df['COMNAME'].str.contains(keyword)]

        if matched_rows.empty:
            return {"message": f"No crops found matching '{keyword}'"}

        columns_to_keep = [
            'COMNAME', 'LISPA', 'TOPMN', 'TOPMX', 'TMIN', 'TMAX',
            'ROPMN', 'ROPMX', 'RMIN', 'RMAX',
            'PHOPMN', 'PHOPMX', 'PHMIN', 'PHMAX',
            'ALTMX', 'LIOPMN', 'LIOPMX', 'LIMN', 'LIMX',
            'DEP', 'DEPR', 'TEXT', 'TEXTR',
            'FER', 'FERR', 'SAL', 'SALR',
            'DRA', 'DRAR', 'CLIZ', 'GMIN', 'GMAX'
        ]

        results = []
        for _, row in matched_rows.iterrows():
            names = [name.strip() for name in row['COMNAME'].split(',')]
            if keyword in names:
                row_dict = row[columns_to_keep].copy()
                row_dict['COMNAME'] = keyword
                results.append(row_dict.to_dict())

        if not results:
            return {"message": f"'{keyword}' found in rows, but not as an exact name"}

        output_path = os.path.join(os.path.dirname(__file__), '..', 'results', f"{keyword}_summary.csv")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pd.DataFrame(results).to_csv(output_path, index=False)

        safe_results = []
        for row in results:
            clean_row = {k: (None if pd.isna(v) or v is np.nan else v) for k, v in row.items()}
            safe_results.append(clean_row)

        self.selected_crop_data = safe_results[0] if safe_results else None
        return safe_results

    def summarize_crop_info(self, crop_data: dict) -> str:
        name = crop_data.get("COMNAME", "This crop").capitalize()
        summary = [f"Crop Summary for {name}:  "]

        if crop_data.get("TOPMN") is not None and crop_data.get("TOPMX") is not None:
            temp_str = f"{name} grows best when the temperature is between {int(crop_data['TOPMN'])}°C and {int(crop_data['TOPMX'])}°C"
            if crop_data.get("TMIN") is not None and crop_data.get("TMAX") is not None:
                temp_str += f", but it can still grow in places from {int(crop_data['TMIN'])}°C to {int(crop_data['TMAX'])}°C."
            else:
                temp_str += "."
            summary.append(temp_str)

        if crop_data.get("ROPMN") is not None and crop_data.get("ROPMX") is not None:
            rain_str = f"It needs about {int(crop_data['ROPMN'])} to {int(crop_data['ROPMX'])} mm of rainfall to grow well"
            if crop_data.get("RMIN") is not None and crop_data.get("RMAX") is not None:
                rain_str += f", but it can survive with as little as {int(crop_data['RMIN'])} mm and up to {int(crop_data['RMAX'])} mm."
            else:
                rain_str += "."
            summary.append(rain_str)

        if crop_data.get("PHOPMN") is not None and crop_data.get("PHOPMX") is not None:
            ph_str = f"The best soil pH is between {crop_data['PHOPMN']} and {crop_data['PHOPMX']}"
            if crop_data.get("PHMIN") is not None and crop_data.get("PHMAX") is not None:
                ph_str += f", but it can still grow in soils from {crop_data['PHMIN']} to {crop_data['PHMAX']} pH."
            else:
                ph_str += "."
            summary.append(ph_str)

        if crop_data.get("ALTMX") is not None:
            summary.append(f"It can grow in areas up to {int(crop_data['ALTMX'])} meters high.")

        light_words = []
        for key in ["LIOPMN", "LIOPMX", "LIMN", "LIMX"]:
            val = crop_data.get(key)
            if val:
                light_words.append(val)
        if light_words:
            light_desc = ', '.join(sorted(set(light_words)))
            summary.append(f"{name} likes bright conditions, such as {light_desc}.")

        dep = crop_data.get("DEP")
        depr = crop_data.get("DEPR")
        if dep and depr:
            summary.append(f"It prefers soil that is {dep}. It can also grow in {depr}.")
        elif dep:
            summary.append(f"It prefers soil that is {dep}.")
        elif depr:
            summary.append(f"It can also grow in {depr} soil conditions.")

        fer = crop_data.get("FER")
        ferr = crop_data.get("FERR")
        if fer or ferr:
            fert_str = f"{name} usually grows well in {fer if fer else 'moderate'} fertility"
            if ferr:
                fert_str += f", but it can tolerate {ferr} fertility too."
            else:
                fert_str += "."
            summary.append(fert_str)

        sal = crop_data.get("SAL")
        salr = crop_data.get("SALR")
        if sal and salr:
            summary.append(f"It prefers {sal} salt levels in the soil. But it may also grow in {salr}.")
        elif sal:
            summary.append(f"It prefers {sal} salt levels in the soil.")
        elif salr:
            summary.append(f"But it may also grow in {salr} salt conditions.")

        if crop_data.get("GMIN") is not None and crop_data.get("GMAX") is not None:
            summary.append(f"The growing time for {name} is between {int(crop_data['GMIN'])} and {int(crop_data['GMAX'])} days depending on the type and conditions.")

        return " ".join(summary)

    def fetch_district_forecast_text(self, district: str) -> dict:
        base_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'districts')
        file_name = f"{district.strip().upper()}.pdf"
        file_path = os.path.join(base_dir, file_name)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"No local forecast PDF found for district '{district}' at {file_path}")

        text_chunks = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                for char in page.chars:
                    try:
                        size = float(char.get("size", 0))
                        if size >= 12:
                            text_chunks.append(char["text"])
                    except:
                        continue
        raw_text = ''.join(text_chunks)
        raw_text = re.sub(r"\s{2,}", " ", raw_text)
        raw_text = re.sub(r"[^\x00-\x7F]+", " ", raw_text).replace('\n', ' ').strip()

        month_patterns = [
            "October 2024", "November 2024", "December 2024", "January 2025",
            "February 2025", "March 2025", "April 2025"
        ]

        monthly_forecast = {}
        for i, month in enumerate(month_patterns):
            start_pattern = re.escape(month)
            end_pattern = re.escape(month_patterns[i + 1]) if i + 1 < len(month_patterns) else r"(Rainfall onset|Cessation|The 2024|Table|Produced|$)"
            pattern = rf"{start_pattern}(.*?){end_pattern}"
            match = re.search(pattern, raw_text, flags=re.DOTALL | re.IGNORECASE)
            monthly_forecast[month] = re.sub(r"\s+", " ", match.group(1)).strip() if match else ""

        summary_patterns = [
            r"Rainfall onset.*?cessation.*?\.",
            r"Cessation.*?\.",
            r"The 2024-2025 rainfall season.*?\.",
            r"La Nina.*?\."
        ]

        seasonal_summary = []
        for pattern in summary_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                seasonal_summary.append(match.group(0).strip())

        self.selected_district_forecast = {
            "district": district,
            "monthly_forecast": monthly_forecast,
            "seasonal_summary": seasonal_summary
        }

        return {
            "monthly_forecast": monthly_forecast,
            "seasonal_summary": seasonal_summary,
            "pdf_source": file_path
        }

    def generate_crop_calendar(self):
        if not self.selected_crop_data or not self.selected_district_forecast:
            raise ValueError("Both crop and district forecast data must be selected first.")

        crop = self.selected_crop_data
        forecast = self.selected_district_forecast['monthly_forecast']

        gmin = int(crop.get("GMIN", 0))
        gmax = int(crop.get("GMAX", 0))
        growth_duration = round((gmin + gmax) / 2)

        onset_month = "December 2024"
        start_date = datetime.strptime("01 " + onset_month, "%d %B %Y")
        end_date = start_date + pd.Timedelta(days=growth_duration)

        calendar_data = []
        current = start_date

        while current <= end_date:
            month_key = f"{calendar.month_name[current.month]} {current.year}"
            text = forecast.get(month_key, "")
            rain_match = re.findall(r"(\d{2,4})\s*mm", text)
            rain_avg = sum([int(r) for r in rain_match]) // len(rain_match) if rain_match else 0
            irrigation = "Yes" if rain_avg < (int(crop.get("ROPMN", 0)) // 3) else "No"

            calendar_data.append({
                "Month": month_key,
                "Expected Rainfall (mm)": rain_avg,
                "Dry Spell Detected": rain_avg < 50,
                "Irrigation Needed": irrigation,
                "Recommended Action": "Irrigate weekly" if irrigation == "Yes" else "Rainfed OK",
                "Activity": "Growth phase"
            })
            current += pd.DateOffset(months=1)

        df = pd.DataFrame(calendar_data)
        output_path = os.path.join(os.path.dirname(__file__), '..', 'results', f"{crop['COMNAME']}_calendar.csv")
        df.to_csv(output_path, index=False)
        return df














# -------------------------------
# FASTAPI HANDLER SECTION
# -------------------------------

from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi import UploadFile, HTTPException
from typing import Optional, List

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, '..', 'uploads')
DATASET_PATH = os.path.join(BASE_DIR, '..', 'data', 'Crop_dataset.csv')

os.makedirs(UPLOAD_DIR, exist_ok=True)

try:
    crop_df = pd.read_csv(DATASET_PATH)
except Exception as e:
    crop_df = pd.DataFrame()
    print(f"[Warning] Could not load dataset: {e}")


async def handle_advice_form(
    files: Optional[List[UploadFile]] = None,
    soil_ph: Optional[float] = None,
    moisture: Optional[float] = None,
    district: Optional[str] = None,
    indigenous_knowledge: Optional[str] = None
) -> JSONResponse:
    saved_files = []
    if files:
        for file in files:
            if not file.filename:
                continue
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            saved_files.append(file.filename)

    summary_parts = [
        f"Soil pH: {soil_ph}" if soil_ph is not None else None,
        f"Soil Moisture: {moisture}%" if moisture is not None else None,
        f"District: {district}" if district else None,
        f"Local Knowledge: {indigenous_knowledge}" if indigenous_knowledge else None,
        f"Uploaded {len(saved_files)} file(s)" if saved_files else "No files uploaded"
    ]
    summary = " | ".join(filter(None, summary_parts))

    recommended_crops = []
    if not crop_df.empty:
        filtered = crop_df.copy()

        if soil_ph is not None:
            soil_ph_whole = int(soil_ph)
            filtered['ph_whole'] = crop_df['ph'].fillna(0).astype(float).astype(int)
            filtered = filtered[filtered['ph_whole'] == soil_ph_whole]

        if moisture is not None:
            moisture_whole = int(moisture)
            filtered['humidity_whole'] = crop_df['humidity'].fillna(0).astype(float).astype(int)
            filtered = filtered[filtered['humidity_whole'] == moisture_whole]

        recommended_crops = filtered['label'].dropna().unique().tolist()

    return JSONResponse(content={
        "summary": summary,
        "uploaded_files": saved_files,
        "recommended_crops": recommended_crops or ["No crop matched the input"]
    })


def read_uploaded_file(filename: str) -> PlainTextResponse:
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return PlainTextResponse("Cannot display this file (possibly binary or non-text format)", status_code=400)

    return PlainTextResponse(content)







def search_plants(search_term: str, limit=10):
    import pandas as pd
    import os

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    CSV_PATH = os.path.join(BASE_DIR, 'data', 'pfaf_plants_merged.csv')


    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"[Error] Could not load pfaf_plants_merged.csv: {e}")
        return [f"Error loading plant database: {e}"]

    search_columns = [
        'use_keywords', 'latin_name_search', 'common_name_search',
        'Scientific Name', 'Common Name'
    ]

    mask = False
    for col in search_columns:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.contains(search_term, case=False, na=False)

    matched = df[mask]

    matched = matched.drop_duplicates(subset=["Common Name", "Scientific Name"])
    matched = matched.head(limit)

    results = []
    for _, row in matched.iterrows():
        para = f"{row.get('Common Name', 'Unknown Plant')} ({row.get('latin_name_search', row.get('Scientific Name', ''))}) "
        para += f"is traditionally used for {row.get('use_keywords', 'various uses')}. "
        edibility = row.get('edibility_rating_search', row.get('Edibility Rating', 'N/A'))
        medicinal = row.get('medicinal_rating_search', row.get('Medicinal Rating', 'N/A'))
        para += f"It has an edibility rating of {edibility} and a medicinal rating of {medicinal}.\n\n"
        para += f"The plant prefers: {row.get('Care Requirements', 'Care details not available.')}\n\n"
        para += f"Cultivation details: {row.get('Cultivation Details', 'No cultivation details provided.')}\n\n"
        para += f"Edible uses: {row.get('Edible Uses', 'No edible uses recorded.')}\n\n"
        para += f"Known hazards: {row.get('Known Hazards', 'No known hazards.')}\n\n"
        para += f"Medicinal properties include: {row.get('Medicinal Properties', 'Medicinal properties not specified.')}\n\n"
        para += f"Native range: {row.get('Native Range', 'Native range not recorded.')}\n\n"
        para += f"Other uses: {row.get('Other Uses', 'No other uses specified.')}\n\n"
        summary_text = row.get('Summary', '')
        if summary_text:
            para += f"Summary: {summary_text}\n\n"
        para += f"👉 🔗 [View Full Details and Images]({row.get('plant_url', '#')})"
        results.append(para)

    return results











