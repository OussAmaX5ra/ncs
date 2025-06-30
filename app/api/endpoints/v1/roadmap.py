from fastapi import APIRouter
from pydantic import BaseModel
from app.web.services.roadmap import generate_learning_roadmap

router = APIRouter()

class RoadmapQuery(BaseModel):
    goal: str

@router.post("/roadmap")
def roadmap(q: RoadmapQuery):
    roadmap_text = generate_learning_roadmap(q.goal)
    return {"roadmap": roadmap_text}
