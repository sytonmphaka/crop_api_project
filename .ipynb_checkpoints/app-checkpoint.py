from fastapi import FastAPI, Query
from ecocrop.processor import EcoCropProcessor
import os
import pandas as pd

# FastAPI app code

app = FastAPI()

# Path to EcoCrop CSV (adjust as needed)
data_path = os.path.join(os.path.dirname(__file__), 'data', 'EcoCrop_DB.csv')
processor = EcoCropProcessor(data_path)

@app.get("/")
def welcome():
    return {"message": "EcoCrop API is live"}

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
        output_path = os.path.join(os.path.dirname(__file__), 'results', 'searched_crops_summary.csv')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        pd.DataFrame(all_matches).to_csv(output_path, index=False)

    return {
        "searched_crops": crop_list,
        "summary": summaries,
        "note": "Results saved in 'results/searched_crops_summary.csv'" if all_matches else "No crop results saved."
    }

@app.get("/forecast/")
def get_district_forecast(district: str = Query(..., description="Enter a Malawi district name, e.g. karonga, mzimba")):
    try:
        forecast = processor.fetch_district_forecast_text(district)
        return {
            "district": district.title(),
            "forecast_summary": forecast
        }
    except Exception as e:
        return {
            "district": district.title(),
            "error": str(e)
        }

@app.get("/calendar/")
def generate_calendar():
    try:
        calendar_df = processor.generate_crop_calendar()
        output_path = os.path.join(os.path.dirname(__file__), 'results', f"{processor.selected_crop_data['COMNAME'].lower()}_calendar.csv")
        calendar_df.to_csv(output_path, index=False)
        return {
            "message": f"Calendar for {processor.selected_crop_data['COMNAME'].title()} in {processor.selected_district_forecast['district'].title()} has been generated.",
            "calendar_preview": calendar_df.head(12).to_dict(orient="records"),
            "saved_to": output_path
        }
    except Exception as e:
        return {"error": str(e)}