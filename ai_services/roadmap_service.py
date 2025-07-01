# ai_services/roadmap_service.py
import json
import re
import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from .llm_client import LLMClient
from .utils.prompts import PromptTemplates
from .utils.roadmap_input_validator import roadmap_input_validator
from .vector_store import vector_store
from models import Roadmap, Step, Resource, User
from ai_services.utils.input_validator import RoadmapRequest

logger = logging.getLogger(__name__)

class RoadmapService:
    """Service to generate and persist personalized learning roadmaps."""

    def __init__(self):
        self.llm_client = LLMClient()
        self.prompts = PromptTemplates()
        self.validator = roadmap_input_validator
        self.vector_store = vector_store

    def generate_learning_roadmap(
        self, db: Session, user_id: str, request: RoadmapRequest
    ) -> Roadmap:
        """Generates and saves a learning roadmap based on user input."""
        # 1. Validate and enhance the query
        goal = request.goal
        is_valid, reason, _ = self.validator.is_valid_learning_query(goal)
        if not is_valid:
            raise ValueError(f"Invalid learning goal: {reason}")

        enhanced_goal = self.validator.enhance_query(goal)

        # 2. Get context and build prompt
        context_chunks = self.vector_store.query_chunks(enhanced_goal, top_k=3)
        prompt = self.prompts.get_roadmap_prompt(enhanced_goal, context_chunks)

        # 3. Call LLM and get structured response
        llm_response = self.llm_client.call_llm(prompt)
        if not llm_response:
            raise ConnectionError("Failed to get a response from the LLM.")

        # 4. Parse the response and save to the database
        new_roadmap = self._parse_and_save_roadmap(db, user_id, request, llm_response)
        
        return new_roadmap

    def _parse_and_save_roadmap(
        self, db: Session, user_id: str, request: RoadmapRequest, llm_response: str
    ) -> Roadmap:
        """Parses the LLM's JSON output and saves the roadmap to the database."""
        try:
            # The LLM is prompted to return a JSON string.
            roadmap_data = json.loads(llm_response)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from LLM response: {llm_response}")
            # Here you might want to add a fallback parser for non-JSON text
            raise ValueError("The AI returned an invalid format. Could not parse the roadmap.")

        # Create the main Roadmap object
        new_roadmap = Roadmap(
            user_id=user_id,
            topic=roadmap_data.get("topic", request.goal),
            exp_lvl=request.exp_lvl,
            specific_goals=request.specific_goals,
            timeline=request.timeline
        )
        db.add(new_roadmap)
        db.flush() # Flush to get the roadmap ID for steps

        # Create and add steps and resources
        for i, step_data in enumerate(roadmap_data.get("steps", [])):
            new_step = Step(
                roadmap_id=new_roadmap.id,
                name=step_data.get("name", "Unnamed Step"),
                description=step_data.get("description", ""),
                estimated_time=step_data.get("estimated_time", "N/A"),
                order=i
            )
            db.add(new_step)
            db.flush() # Flush to get the step ID for resources

            for resource_data in step_data.get("resources", []):
                new_resource = Resource(
                    step_id=new_step.id,
                    name=resource_data.get("name", "Unnamed Resource"),
                    url=resource_data.get("url", ""),
                    description=resource_data.get("description", "")
                )
                db.add(new_resource)

        db.commit()
        db.refresh(new_roadmap)
        return new_roadmap

# Global instance for easy access in routes
roadmap_service = RoadmapService()
