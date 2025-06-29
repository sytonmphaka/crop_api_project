from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from ecocrop.processor import fetch_documents  # Adjust path as needed

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/updates", response_class=HTMLResponse)
async def updates_page(request: Request):
    updates = fetch_documents() or []
    return templates.TemplateResponse("update.html", {
        "request": request,
        "updates": updates
    })
