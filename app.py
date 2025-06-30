from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from eco_crop_routes import router as eco_router
from upload_routes import router as upload_router
from upload_routes import upload_page, updates_page  # for reuse

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

@app.get("/advise", response_class=HTMLResponse)
async def advise(request: Request):
    return templates.TemplateResponse("advise.html", {"request": request})


@app.get("/uploads", response_class=HTMLResponse)
async def identify_plant(request: Request):
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
    return HTMLResponse("Welcome to Maphunziro page")

from upload_routes import fetch_documents  # Make sure this is imported

@app.get("/updates", response_class=HTMLResponse, name="updates")
async def updates(request: Request):
    return await updates_page(request)


# Include other routers
app.include_router(eco_router)
app.include_router(upload_router)
