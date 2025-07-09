from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from eco_crop_routes import router as eco_router
from upload_routes import router as upload_router
from upload_routes import upload_page, updates_page  # for reuse
from fastapi.responses import JSONResponse
from supabase_utils import (
    insert_user_data, fetch_user_data, 
    insert_business_data, fetch_business_data
)





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





