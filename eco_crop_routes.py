from fastapi import FastAPI, Query, Request, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from ecocrop.processor import EcoCropProcessor, handle_advice_form, read_uploaded_file, search_plants
from typing import Optional, List
import os
import pandas as pd
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates




#app = FastAPI()



from fastapi import APIRouter
router = APIRouter()

templates = Jinja2Templates(directory="templates")


# Path to EcoCrop CSV (adjust as needed)
data_path = os.path.join(os.path.dirname(__file__), 'data', 'EcoCrop_DB.csv')
processor = EcoCropProcessor(data_path)


@router.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/search/")
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
        "note": "Results saved in 'results/searched_crops_summary.csv'" if all_matches else "No crop results saved."
    }


@router.get("/forecast/")
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


@router.get("/calendar/")
def generate_calendar():
    try:
        calendar_df = processor.generate_crop_calendar()
        output_dir = os.path.join(os.path.dirname(__file__), 'results')
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{processor.selected_crop_data['COMNAME'].lower()}_calendar.csv"
        output_path = os.path.join(output_dir, filename)
        calendar_df.to_csv(output_path, index=False)
        return {
            "message": f"Calendar for {processor.selected_crop_data['COMNAME'].title()} in {processor.selected_district_forecast['district'].title()} has been generated.",
            "calendar_preview": calendar_df.head(12).to_dict(orient="records"),
            "saved_to": f"/results/{filename}"
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/advise/")
async def advise_endpoint(
    files: Optional[List[UploadFile]] = File(None),
    soil_ph: Optional[float] = Form(None),
    moisture: Optional[float] = Form(None),
    district: Optional[str] = Form(None),
    indigenous_knowledge: Optional[str] = Form(None)
):
    return await handle_advice_form(
        files=files,
        soil_ph=soil_ph,
        moisture=moisture,
        district=district,
        indigenous_knowledge=indigenous_knowledge
    )








@router.get("/read-file/{filename}")
def read_file(filename: str):
    return read_uploaded_file(filename)

from fastapi import Query, Response

CSV_COLUMNS = [
    'use_keywords', 'latin_name_search', 'edibility_rating_search',
    'medicinal_rating_search', 'plant_url', 'Care Requirements', 'Common Name',
    'Cultivation Details', 'Edibility Rating', 'Edible Uses', 'Family', 'Known Hazards',
    'Medicinal Properties', 'Medicinal Rating', 'Native Range', 'Other Uses',
    'Other Uses Rating', 'Propagation', 'Range', 'Scientific Name', 'Special Uses',
    'Summary', 'USDA hardiness', 'Weed Potential'
]

@router.get("/search/plants/")
def search_plants_endpoint(q: str = Query(..., description="Search term using plant name, latin name, or use keyword"),
                           download: bool = Query(False, description="Set to true to download CSV")):
    import pandas as pd
    import io

    file_path = '/Users/patrickkawayechimseu/crop_api_project/data/pfaf_plants_merged.csv'
    df = pd.read_csv(file_path)

    search_columns = ['use_keywords', 'latin_name_search', 'common_name_search', 'Scientific Name', 'Common Name']
    mask = False
    for col in search_columns:
        if col in df.columns:
            mask = mask | df[col].astype(str).str.contains(q, case=False, na=False)
    filtered_df = df.loc[mask]

    if filtered_df.empty:
        return {"query": q, "results": [], "message": "No plants found"}

    if download:
        filtered_df_csv = filtered_df.loc[:, [col for col in CSV_COLUMNS if col in filtered_df.columns]]
        filtered_df_csv = filtered_df_csv.drop_duplicates(subset=['Common Name', 'latin_name_search'])

        stream = io.StringIO()
        filtered_df_csv.to_csv(stream, index=False)
        csv_data = stream.getvalue()
        stream.close()

        headers = {
            "Content-Disposition": "attachment; filename=plant_search_results.csv",
            "Content-Type": "text/csv",
        }
        return Response(content=csv_data, headers=headers, media_type="text/csv")

    results = search_plants(q)
    return {"query": q, "results": results}




