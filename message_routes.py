# messages.py
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_303_SEE_OTHER
from fastapi.staticfiles import StaticFiles

from ecocrop.processor import registered_numbers_by_district, register_number_by_district

messages_router = APIRouter()
templates = Jinja2Templates(directory="templates")

@messages_router.get("/ziwan")
def ziwan_page(request: Request):
    return templates.TemplateResponse("ziwan.html", {
        "request": request,
        "districts": list(registered_numbers_by_district.keys()),
        "registered_numbers": registered_numbers_by_district
    })

@messages_router.post("/add_number")
def add_number(
    request: Request,
    district: str = Form(...),
    phone: str = Form(...)
):
    if phone.startswith("0"):
        phone = "+265" + phone[1:]
    register_number_by_district(district, phone)
    return RedirectResponse(url="/ziwan", status_code=HTTP_303_SEE_OTHER)














@messages_router.get("/messages/{district}")
def view_messages(request: Request, district: str):
    from ecocrop.processor import get_messages_for_district
    messages = get_messages_for_district(district)
    return templates.TemplateResponse("messages_list.html", {
        "request": request,
        "district": district,
        "messages": messages
    })



@messages_router.post("/add_message")
def add_message(
    request: Request,
    district: str = Form(...),
    message: str = Form(...)
):
    # ✅ Import needed functions inside the route
    from ecocrop.processor import add_message_to_district, get_registered_numbers_by_district
    from ecocrop.sms import send_sms

    add_message_to_district(district, message)

    # ✅ Print to debug
    print("Sending to:", get_registered_numbers_by_district(district))

    for phone in get_registered_numbers_by_district(district):
        send_sms(phone, message)

    return RedirectResponse(f"/messages/{district}", status_code=HTTP_303_SEE_OTHER)
