from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from eco_crop_routes import router as eco_router
from upload_routes import router as upload_router
from upload_routes import upload_page, updates_page  # for reuse

from fastapi import UploadFile, File
from supa import list_uploaded_files

from fastapi.responses import JSONResponse
from supabase_utils import (
    insert_user_data, fetch_user_data, 
    insert_business_data, fetch_business_data
)

from starlette.middleware.sessions import SessionMiddleware

from supa import save_supabase_credentials, load_supabase_client, insert_user_profile, get_user_profile

from supa import save_supabase_credentials, load_supabase_client, insert_user_profile, get_user_profile

from fastapi import FastAPI, Form, Request, status
from fastapi.responses import RedirectResponse
import json
import os







app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/results", StaticFiles(directory="results"), name="results")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/advice", response_class=HTMLResponse)
async def advise(request: Request):
    return templates.TemplateResponse("advise.html", {"request": request})


@app.get("/uploads", response_class=HTMLResponse)
async def uploads(request: Request):
    return await upload_page(request)



@app.get("/identify-plant", response_class=HTMLResponse)
async def identify_plant(request: Request):
    return templates.TemplateResponse("identity.html", {"request": request})




@app.get("/community", response_class=HTMLResponse)
async def community(request: Request):
    return templates.TemplateResponse("market.html", {"request": request})

@app.get("/flooddrought", response_class=HTMLResponse)
async def flooddrought(request: Request):
    return templates.TemplateResponse("floods.html", {"request": request})


@app.get("/medicrop", response_class=HTMLResponse)
async def medicrop(request: Request):
    return templates.TemplateResponse("mediplant.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/farm", response_class=HTMLResponse)
async def farm(request: Request):
    return templates.TemplateResponse("notes.html", {"request": request})









@app.get("/maphunziro", response_class=HTMLResponse)
async def maphunziro(request: Request):
    return templates.TemplateResponse("maphunziro.html", {"request": request})

from upload_routes import fetch_documents  # Make sure this is imported

@app.get("/updates", response_class=HTMLResponse, name="updates")
async def updates(request: Request):
    return await updates_page(request)


# Include other routers
app.include_router(eco_router)
app.include_router(upload_router)









# For tools/materials businesses
@app.post("/register_business")
async def register_business(request: Request):
    data = await request.json()
    name = data.get("business_name")
    status = data.get("status")
    website = data.get("website")

    try:
        result = insert_user_data(name, status, website)
        return JSONResponse(content={"message": "Business saved successfully", "data": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error saving business", "error": str(e)})

@app.get("/businesses")
async def get_businesses():
    try:
        businesses = fetch_user_data()
        return JSONResponse(content={"businesses": businesses})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error fetching businesses", "error": str(e)})

# For product businesses
@app.post("/register_product")
async def register_product(request: Request):
    data = await request.json()
    name = data.get("business_name")
    status = data.get("status")
    website = data.get("website")

    try:
        result = insert_business_data(name, status, website)
        return JSONResponse(content={"message": "Product business saved successfully", "data": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error saving product business", "error": str(e)})

@app.get("/products")
async def get_products():
    try:
        products = fetch_business_data()
        return JSONResponse(content={"products": products})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": "Error fetching products", "error": str(e)})




























CREDENTIALS_FILE = "supabase_credentials.json"

def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_credentials(data):
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(
    request: Request,
    supabase_url: str = Form(...),
    supabase_key: str = Form(...),
    name: str = Form(...),
    status: str = Form(...),
    contacts: str = Form(...),
    location: str = Form(...),
    password: str = Form(...)
):
    credentials = load_credentials()

    if name in credentials:
        return HTMLResponse(f"<h3>Business '{name}' already registered. Please login.</h3>")

    # Save Supabase credentials locally
    save_supabase_credentials(name, supabase_url, supabase_key)

    # Save registration data locally for login check (including password)
    credentials[name] = {
        "url": supabase_url,
        "key": supabase_key,
        "status": status,
        "contacts": contacts,
        "location": location,
        "password": password
    }
    save_credentials(credentials)

    # Insert user profile into Supabase shared table "data"
    supabase_client = load_supabase_client(name)
    insert_user_profile(supabase_client, name, status, contacts, location, password)

    return RedirectResponse(url=f"/profile/{name}", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/login")
async def login(
    request: Request,
    name: str = Form(...),
    password: str = Form(...)
):
    credentials = load_credentials()
    if name in credentials:
        if credentials[name]["password"] == password:
            return RedirectResponse(url=f"/profile/{name}", status_code=status.HTTP_303_SEE_OTHER)

    return HTMLResponse("<h3>Login failed: wrong business name or password.</h3>")



@app.get("/profile/{name}", response_class=HTMLResponse)
async def profile(request: Request, name: str):
    credentials = load_credentials()
    user = credentials.get(name)
    if not user:
        return HTMLResponse(f"<h3>Business '{name}' not found. Please register or login.</h3>")

    supabase = load_supabase_client(name)
    files = list_uploaded_files(supabase, name) if supabase else []

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": {**user, "name": name},
        "files": files
    })




















import uuid

@app.post("/upload/{name}")
async def upload_file(name: str, file: UploadFile = File(...)):
    supabase = load_supabase_client(name)
    if not supabase:
        return {"error": "Supabase client not found for this user."}

    contents = await file.read()
    file_ext = file.filename.split('.')[-1]
    unique_name = f"{uuid.uuid4()}.{file_ext}"

    try:
        # Upload to Supabase Storage (bucket name must be 'uploads')
        supabase.storage.from_("uploads").upload(
            unique_name,
            contents,
            {"content-type": file.content_type}
        )

        # Get public URL
        public_url = supabase.storage.from_("uploads").get_public_url(unique_name)

        # Save file metadata in the 'data' table
        supabase.table("data").insert({
            "name": name,
            "filename": file.filename,
            "file_url": public_url
        }).execute()

        return RedirectResponse(url=f"/profile/{name}", status_code=303)

    except Exception as e:
        print("Upload error:", e)
        return {"error": f"Failed to upload file: {str(e)}"}












@app.post("/delete/{name}/{file_id}")
async def delete_file(name: str, file_id: int):
    supabase = load_supabase_client(name)
    if not supabase:
        return {"error": "Supabase client not found for this user."}

    # Delete from the table
    supabase.table("data").delete().eq("id", file_id).execute()

    return RedirectResponse(url=f"/profile/{name}", status_code=303)
