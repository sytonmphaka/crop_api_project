from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from ecocrop.processor import EcoCropProcessor
import os
import pandas as pd

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Mount the "results" folder to serve generated CSV files as static content
app.mount("/results", StaticFiles(directory="results"), name="results")

# Path to EcoCrop CSV (adjust as needed)
data_path = os.path.join(os.path.dirname(__file__), 'data', 'EcoCrop_DB.csv')
processor = EcoCropProcessor(data_path)

@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/search/")
def search_crops(keywords: str = Query(..., description="Comma-separated crop names, e.g. maize,cassava,sorghum")):
    crop_list = [kw.strip().lower() for kw in keywords.split(',')]
    summaries = []
    all_matches = []

    for crop in crop_list:
        result = processor.search_crops(crop)
        if isinstance(result, list):
            summaries.extend([processor.summarize_crop_info(r) for r in result])
            all_matches.extend(result)
        else:
            summaries.append(f"No exact match found for '{crop}'")

    if all_matches:
        output_dir = os.path.join(os.path.dirname(__file__), 'results')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'searched_crops_summary.csv')
        pd.DataFrame(all_matches).to_csv(output_path, index=False)

    return {
        "searched_crops": crop_list,
        "summary": summaries,
        "note": "Summaries generated from EcoCrop database."
    }

@app.get("/forecast/")
def get_district_forecast(district: str = Query(..., description="Enter a Malawi district name, e.g. karonga, mzimba")):
    try:
        # Fetch raw forecast (loads PDF text)
        _ = processor.fetch_district_forecast_text(district)

        # Generate human-readable calendar summary and advice
        readable_data = processor.generate_readable_calendar_advice()

        # Return plain strings (no nested dict) for easy frontend handling
        return {
            "district": district.title(),
            "forecast_summary": readable_data["summary"],
            "advice_header": readable_data["advice_header"],
            "advice_text": readable_data["advice_text"],
            "farmer_action": readable_data["farmer_action"]
        }
    except Exception as e:
        return {
            "district": district.title(),
            "error": str(e)
        }

@app.get("/calendar/")
def generate_calendar():
    try:
        df = processor.generate_crop_calendar()
        calendar_preview = df.head(6).to_dict(orient='records')
        saved_to = os.path.join('results', f"{processor.selected_crop_data['COMNAME']}_calendar.csv")
        return {
            "message": f"Calendar generated for {processor.selected_crop_data['COMNAME']}.",
            "calendar_preview": calendar_preview,
            "saved_to": "/" + saved_to.replace("\\", "/")
        }
    except Exception as e:
        return {
            "error": str(e)
        }
