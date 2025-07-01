# ai_services/utils/input_validator.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import re


class LearningQueryValidator:
    """Validator for learning-related queries."""

    def __init__(self):
        # This regex is a simple example. You can make it more sophisticated.
        self.learning_keywords = re.compile(
            r"\b(learn|master|understand|study|how to|guide|roadmap|course|tutorial|become a|develop skills in)\b",
            re.IGNORECASE
        )

    def is_valid_learning_query(self, query: str) -> (bool, str, List[str]):
        """Check if a query is a valid learning goal."""
        if not query or not isinstance(query, str) or len(query.strip()) < 10:
            return False, "Query is too short or empty.", []

        if not self.learning_keywords.search(query):
            suggestions = [
                f"Try rephrasing with 'learn to {query}' or 'roadmap for {query}'."
            ]
            return False, "Query does not seem to be a learning goal.", suggestions

        return True, "Valid learning goal.", []

    def enhance_query(self, query: str) -> str:
        """Enhance the query for better LLM performance."""
        # Example enhancement: could be more complex
        if not query.lower().startswith(("roadmap for", "plan for")):
            return f"Create a detailed learning roadmap for: {query}"
        return query

class InputValidator:
    """Validator for user inputs like files and text queries."""

    def __init__(self, max_file_size_mb=10, allowed_content_types=None):
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        if allowed_content_types is None:
            self.allowed_content_types = [
                "text/plain",
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
                "text/markdown",
            ]
        else:
            self.allowed_content_types = allowed_content_types

    def validate_file(self, content_type: str, file_size: int) -> (bool, str):
        """Validate file type and size."""
        if content_type not in self.allowed_content_types:
            return False, f"Invalid file type: {content_type}. Allowed types: {', '.join(self.allowed_content_types)}"
        if file_size > self.max_file_size_bytes:
            return False, f"File is too large: {file_size / (1024 * 1024):.2f} MB. Maximum size is {self.max_file_size_bytes / (1024 * 1024):.2f} MB."
        if file_size == 0:
            return False, "File is empty."
        return True, "File is valid."

    def sanitize_text(self, text: str) -> str:
        """Sanitize text input by stripping whitespace."""
        if not isinstance(text, str):
            return ""
        # Basic sanitization, can be expanded (e.g., remove HTML tags)
        return text.strip()


roadmap_input_validator = LearningQueryValidator()


# --- Request Models (Input) ---

class RoadmapRequest(BaseModel):
    """Request model for generating a learning roadmap."""
    goal: str = Field(..., min_length=10, description="The primary learning goal.")
    exp_lvl: str = Field("beginner", description="User's experience level.")
    timeline: str = Field("3 months", description="Desired timeline for completion.")
    specific_goals: Optional[str] = Field(None, description="Any specific sub-goals or topics to focus on.")

class ChatRequest(BaseModel):
    """Request model for chatting with a document."""
    document_id: str = Field(..., description="ID of the document to chat with.")
    question: str = Field(..., min_length=1, description="User's question.")


# --- Response Models (Output) ---

class DocumentInfo(BaseModel):
    """Detailed information about a single analyzed file."""
    id: uuid.UUID
    filename: str
    content_type: str
    word_count: int
    status: str
    created_at: datetime
    summary: Optional[str] = None
    key_points: Optional[str] = None  # Stored as JSON string in DB
    qa_cards: Optional[str] = None   # Stored as JSON string in DB

    model_config = ConfigDict(from_attributes=True)

class AnalyzeFileResponse(DocumentInfo):
    """Response after a file is successfully analyzed."""
    pass # Inherits all fields from DocumentInfo

class DocumentList(BaseModel):
    """A list of analyzed documents."""
    documents: List[DocumentInfo]

class DeletionResponse(BaseModel):
    """Confirmation of document deletion."""
    message: str

class ChatResponse(BaseModel):
    """Response from the chat endpoint."""
    response: str
    debug_info: Optional[Dict[str, Any]] = None

# --- Roadmap Response Models ---

class ResourceInfo(BaseModel):
    """Information about a learning resource."""
    id: int
    name: str
    url: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class StepInfo(BaseModel):
    """A single step in a learning roadmap."""
    id: int
    name: str
    description: Optional[str] = None
    estimated_time: Optional[str] = None
    order: int
    resources: List[ResourceInfo] = []

    model_config = ConfigDict(from_attributes=True)

class RoadmapResponse(BaseModel):
    """The complete, structured learning roadmap."""
    id: int
    topic: str
    exp_lvl: str
    specific_goals: Optional[str] = None
    timeline: str
    created_at: datetime
    steps: List[StepInfo] = []

    model_config = ConfigDict(from_attributes=True)
