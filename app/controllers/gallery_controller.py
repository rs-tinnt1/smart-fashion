from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.web import build_gallery_data

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/gallery", response_class=HTMLResponse)
def gallery(request: Request):
    images = build_gallery_data()
    return templates.TemplateResponse("gallery.html", {"request": request, "images": images})
