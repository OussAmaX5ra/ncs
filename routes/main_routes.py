import logging
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse

log = logging.getLogger(__name__)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from middleware import login_required, redirect_if_logged_in
from models import Roadmap, Step, StepState, File as FileModel
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@redirect_if_logged_in
async def landing_page(request: Request):
    log.debug("Accessed landing page route")
    """Render landing page for anonymous users."""
    return templates.TemplateResponse("landing.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
@login_required
async def dashboard(request: Request, db: Session = Depends(get_db)):
    log.debug("Accessed dashboard route")
    log.debug("Request method: %s", request.method)
    log.debug("Request headers: %s", request.headers)
    log.debug("Request query params: %s", request.query_params)
    """Render dashboard page"""
    user = request.state.user
    
    roadmaps_count = db.query(Roadmap).filter(Roadmap.user_id == user.id).count()
    
    completed_steps = db.query(Step).join(Roadmap).filter(
        Roadmap.user_id == user.id,
        Step.state == StepState.completed
    ).count()
    
    context = {
        "request": request,
        "username": user.username,
        "roadmaps_count": roadmaps_count,
        "completed_steps": completed_steps
    }
    return templates.TemplateResponse("dashboard.html", context)

@router.get("/roadmap/create", response_class=HTMLResponse)
@login_required
async def create_roadmap_page(request: Request):
    log.debug("Accessed create roadmap route")
    log.debug("Request method: %s", request.method)
    log.debug("Request headers: %s", request.headers)
    log.debug("Request query params: %s", request.query_params)
    """Render create roadmap page"""
    return templates.TemplateResponse("create_roadmap.html", {"request": request})

@router.post("/roadmap/create")
@login_required
async def create_roadmap_submit(
    request: Request,
    topic: str = Form(...),
    experience_level: str = Form(...),
    specific_goals: str = Form(""),
    timeline: str = Form(...),
    db: Session = Depends(get_db)
):
    log.debug(f"Accessed create roadmap submit with topic: {topic}")
    log.debug("Request method: %s", request.method)
    log.debug("Request headers: %s", request.headers)
    log.debug("Request query params: %s", request.query_params)
    """Handle create roadmap form submission"""
    user = request.state.user
    
    # Create roadmap
    roadmap_content = (
        f"Experience Level: {experience_level}\n"
        f"Specific Goals: {specific_goals or 'Not specified'}\n"
        f"Timeline: {timeline}"
    )
    roadmap = Roadmap(
        title=topic,
        content=roadmap_content,
        user_id=user.id
    )
    
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    
    # Create sample steps (in a real app, you'd use AI to generate these)
    sample_steps = [
        {"name": "Introduction and Basics", "description": f"Learn the fundamentals of {topic}", "estimated_time": "1 week"},
        {"name": "Intermediate Concepts", "description": f"Dive deeper into {topic} concepts", "estimated_time": "2 weeks"},
        {"name": "Advanced Topics", "description": f"Master advanced {topic} techniques", "estimated_time": "2 weeks"},
        {"name": "Practice Projects", "description": f"Build real-world {topic} projects", "estimated_time": "3 weeks"},
        {"name": "Review and Assessment", "description": f"Review and test your {topic} knowledge", "estimated_time": "1 week"}
    ]
    
    for i, step_data in enumerate(sample_steps):
        step = Step(
            name=step_data["name"],
            description=step_data["description"],
            estimated_time=step_data["estimated_time"],
            order=i + 1,
            roadmap_id=roadmap.id
        )
        db.add(step)
    
    db.commit()
    
    return RedirectResponse(url="/dashboard", status_code=302)

@router.get("/code-assistant", response_class=HTMLResponse)
@login_required
async def code_assistant_page(request: Request):
    log.debug("Accessed code assistant route")
    log.debug("Request method: %s", request.method)
    log.debug("Request headers: %s", request.headers)
    log.debug("Request query params: %s", request.query_params)
    """Render code assistant page"""
    return templates.TemplateResponse("code_with_me.html", {"request": request})

@router.post("/code-assistant")
@login_required
async def code_assistant_submit(
    request: Request,
    code: str = Form(...),
    db: Session = Depends(get_db)
):
    log.debug(f"Accessed code assistant submit with code: {code}")
    log.debug("Request method: %s", request.method)
    log.debug("Request headers: %s", request.headers)
    log.debug("Request query params: %s", request.query_params)
    """Handle code analysis form submission"""
    # In a real app, you'd process the code with AI here
    # For now, just redirect back to the page
    return RedirectResponse(url="/code-assistant", status_code=302)

@router.get("/document-summarizer", response_class=HTMLResponse)
@login_required
async def document_summarizer_page(request: Request):
    log.debug("Accessed document summarizer route")
    log.debug("Request method: %s", request.method)
    log.debug("Request headers: %s", request.headers)
    log.debug("Request query params: %s", request.query_params)
    """Render document summarizer page"""
    return templates.TemplateResponse("summarize.html", {"request": request})

@router.post("/document-summarizer")
@login_required
async def document_summarizer_submit(
    request: Request,
    document: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    log.debug(f"Accessed document summarizer submit with file: {document.filename}")
    log.debug("Request method: %s", request.method)
    log.debug("Request headers: %s", request.headers)
    log.debug("Request query params: %s", request.query_params)
    """Handle document upload and summarization"""
    user = request.state.user
    
    # Save uploaded file (in a real app, you'd use proper file storage)
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, f"{user.id}_{document.filename}")
    
    with open(file_path, "wb") as buffer:
        content = await document.read()
        buffer.write(content)
    
    # Save file record to database
    file_record = FileModel(
        filename=document.filename,
        file_path=file_path,
        user_id=user.id
    )
    
    db.add(file_record)
    db.commit()
    
    # In a real app, you'd process the document with AI here
    return RedirectResponse(url="/document-summarizer", status_code=302)
