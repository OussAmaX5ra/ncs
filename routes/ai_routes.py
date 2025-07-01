# routes/ai_routes.py
import os
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import PyPDF2
import docx

# Database and authentication dependencies (assuming they exist)
from database import get_db
from auth import get_current_active_user # Placeholder for your auth logic
from models import User

# AI Services and Pydantic Models
from ai_services.document_analyser import DocumentAnalyzer
from ai_services.roadmap_service import roadmap_service
from ai_services.utils.input_validator import (
    ChatRequest,
    AnalyzeFileResponse,
    ChatResponse,
    DocumentInfo,
    DocumentList,
    DeletionResponse,
    RoadmapRequest,
    RoadmapResponse
)

# Create API router
router = APIRouter()

# --- Helper Functions for Text Extraction ---

def _extract_text_from_pdf(file_stream) -> str:
    try:
        reader = PyPDF2.PdfReader(file_stream)
        text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
        if not text: raise ValueError("No text found in PDF.")
        return text
    except Exception as e:
        raise IOError(f"PDF processing failed: {e}")

def _extract_text_from_docx(file_stream) -> str:
    try:
        doc = docx.Document(file_stream)
        text = "\n".join(para.text for para in doc.paragraphs if para.text)
        if not text: raise ValueError("No text found in DOCX file.")
        return text
    except Exception as e:
        raise IOError(f"DOCX processing failed: {e}")

# --- API Endpoints ---

@router.post("/ai/analyze-file/", response_model=AnalyzeFileResponse, tags=["AI Services"])
async def analyze_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload, save, and analyze a file (PDF, DOCX, TXT) in the background."""
    content_type = file.content_type
    filename = file.filename
    text_content = ""

    try:
        if content_type == "application/pdf":
            text_content = _extract_text_from_pdf(file.file)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            text_content = _extract_text_from_docx(file.file)
        elif content_type == "text/plain":
            text_content = (await file.read()).decode("utf-8")
        else:
            raise HTTPException(status_code=415, detail="Unsupported file type.")

        if not text_content.strip():
            raise HTTPException(status_code=400, detail="File is empty or contains no text.")

        analyzer = DocumentAnalyzer()
        # Create the file record in the DB immediately
        new_file = analyzer.add_document(
            db, current_user.id, filename, content_type, text_content
        )

        # Run the CPU/network-bound analysis in the background
        background_tasks.add_task(analyzer.start_analysis, db, new_file.id)

        return new_file # Pydantic will serialize this ORM object

    except (ValueError, IOError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/ai/chat/", response_model=ChatResponse, tags=["AI Services"])
async def chat_with_document(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Engage in a conversation with an analyzed document."""
    try:
        analyzer = DocumentAnalyzer()
        chat_result = analyzer.chat_with_document(
            db, current_user.id, request.document_id, request.question
        )
        return ChatResponse(**chat_result)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")

@router.get("/ai/documents/", response_model=DocumentList, tags=["AI Services"])
async def list_all_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve a list of all of the current user's analyzed documents."""
    analyzer = DocumentAnalyzer()
    documents = analyzer.list_documents(db, current_user.id)
    return DocumentList(documents=documents)

@router.get("/ai/documents/{document_id}", response_model=DocumentInfo, tags=["AI Services"])
async def get_document_details(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information for a specific document."""
    try:
        analyzer = DocumentAnalyzer()
        doc = analyzer.get_document(db, current_user.id, document_id)
        return doc
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.delete("/ai/documents/{document_id}", response_model=DeletionResponse, tags=["AI Services"])
async def delete_analyzed_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete an analyzed document and its associated data."""
    try:
        analyzer = DocumentAnalyzer()
        result = analyzer.delete_document(db, current_user.id, document_id)
        return DeletionResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

@router.post("/ai/roadmap/", response_model=RoadmapResponse, tags=["AI Services"])
async def get_learning_roadmap(
    request: RoadmapRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate and save a personalized learning roadmap."""
    try:
        roadmap = roadmap_service.generate_learning_roadmap(
            db, current_user.id, request
        )
        return roadmap
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except ConnectionError as ce:
        raise HTTPException(status_code=503, detail=str(ce))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate roadmap: {e}")

@router.get("/ai/health/", status_code=200, tags=["AI Services"])
async def health_check():
    """Check if the AI service and its dependencies are running."""
    # In a real app, you might check DB connection, LLM client, etc.
    return {"status": "AI services are operational"}
