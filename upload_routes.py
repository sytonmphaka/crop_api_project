from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import os
import mimetypes
import httpx
import requests
from io import BytesIO
from urllib.parse import unquote
from ecocrop.processor import upload_file_to_supabase, fetch_documents, delete_file_from_supabase
import pdfplumber
from docx import Document

router = APIRouter()
templates = Jinja2Templates(directory="templates")

UPLOAD_FOLDER = "temp_uploads"
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "video/mp4",
    "video/avi",
    "video/quicktime"
}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.get("/", response_class=HTMLResponse)
async def root():
    raise HTTPException(status_code=404, detail="Page not found")


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    documents = fetch_documents() or []
    return templates.TemplateResponse("upload.html", {"request": request, "documents": documents})


@router.get("/updates", response_class=HTMLResponse)
async def updates_page(request: Request):
    updates = fetch_documents() or []
    return templates.TemplateResponse("update.html", {"request": request, "updates": updates})


@router.post("/upload", response_class=HTMLResponse)
async def handle_upload(request: Request, title: str = Form(...), file: UploadFile = File(...)):
    filename = file.filename
    mime_type, _ = mimetypes.guess_type(filename)

    if mime_type not in ALLOWED_MIME_TYPES:
        return HTMLResponse(f"❌ Upload failed: File type '{mime_type}' is not supported.", status_code=400)

    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    with open(filepath, "rb") as f:
        result = upload_file_to_supabase(f, filename, title)

    os.remove(filepath)

    documents = fetch_documents() or []
    if result.get("status") == "success":
        return templates.TemplateResponse("upload.html", {"request": request, "documents": documents})
    else:
        return HTMLResponse(f"❌ Upload failed: {result.get('message', 'unknown error')}", status_code=500)


@router.get("/view", response_class=HTMLResponse)
async def view_file(request: Request, url: str):
    file_type, _ = mimetypes.guess_type(url)
    html = "<h2>📄 File Preview</h2>"

    if file_type:
        if file_type.startswith("image"):
            html += f'<img src="{url}" alt="Image" style="max-width: 100%; height: auto;">'
        elif file_type.startswith("video"):
            html += f'<video controls style="max-width:100%"><source src="{url}" type="{file_type}"></video>'
        elif file_type == "application/pdf":
            html += f'<iframe src="{url}" width="100%" height="600px"></iframe>'
        elif file_type in [
            "application/msword", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]:
            html += f'<p>Cannot preview Word files. Please download below.</p>'
        else:
            html += f'<p>Unsupported file type: {file_type}</p>'
    else:
        html += "<p>Unknown file type.</p>"

    html += f'<br><a href="/download?url={url}">⬇️ Download</a>'
    return HTMLResponse(content=html)


@router.get("/view_file", response_class=HTMLResponse)
async def view_file_generic(url: str, type: str):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return HTMLResponse(content="Error fetching file", status_code=404)

        content = response.content
        html = "<div style='max-width:800px; margin:auto;'>"

        if "image" in type:
            html += f'<img src="{url}" alt="Image" style="max-width:100%;" />'
        elif "video" in type:
            html += f'''
                <video controls style="max-width:100%;">
                  <source src="{url}" type="{type}">
                  Your browser does not support the video tag.
                </video>
            '''
        elif "pdf" in type:
            with pdfplumber.open(BytesIO(content)) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            html += "<h3>📄 Extracted PDF Text:</h3><pre style='text-align:left;white-space:pre-wrap;'>" + text + "</pre>"
        elif "msword" in type or "officedocument.wordprocessingml.document" in type:
            doc = Document(BytesIO(content))
            text = "\n".join(p.text for p in doc.paragraphs)
            html += "<h3>📄 Extracted Word Text:</h3><pre style='text-align:left;white-space:pre-wrap;'>" + text + "</pre>"
        else:
            html += "<p>❌ Unsupported file type for preview.</p>"

        html += f'<br><a href="/download?url={url}">⬇️ Download</a></div>'
        return HTMLResponse(content=html)

    except Exception as e:
        return HTMLResponse(content=f"❌ Error: {e}", status_code=500)


@router.get("/download")
async def download_file(url: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError:
            return HTMLResponse("❌ Failed to download file", status_code=404)

        filename = url.split("/")[-1] or "downloaded_file"
        return StreamingResponse(
            response.aiter_bytes(),
            headers={"Content-Disposition": f"attachment; filename={filename}"},
            media_type=response.headers.get("content-type", "application/octet-stream"),
        )


@router.get("/delete", response_class=HTMLResponse)
async def delete_file_route(request: Request, file_url: str = Query(...), doc_id: str = Query(...)):
    try:
        filename = os.path.basename(unquote(file_url).split("?")[0])
        result = delete_file_from_supabase(filename, doc_id)

        documents = fetch_documents() or []

        if result.get("status") == "success":
            return templates.TemplateResponse("upload.html", {
                "request": request,
                "documents": documents
            })
        else:
            return HTMLResponse(content=f"❌ Delete failed: {result.get('message', 'Unknown error')}", status_code=500)

    except Exception as e:
        return HTMLResponse(content=f"❌ Error: {e}", status_code=500)
