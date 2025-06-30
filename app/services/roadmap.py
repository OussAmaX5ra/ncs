# app/services/roadmap_generator.py

from app.web.services.indexer import query_chunks
from app.web.utils.prompts import build_roadmap_prompt
from app.web.services.llm_client import call_llm


def generate_learning_roadmap(user_goal: str, top_k: int = 5) -> str:
    """
    Generates a personalized learning roadmap using RAG.

    Args:
        user_goal (str): The user's learning goal (e.g., "Become a app developer")
        top_k (int): Number of relevant chunks to retrieve

    Returns:
        str: LLM-generated roadmap text
    """
    # Retrieve similar roadmap chunks
    context_chunks = query_chunks(user_goal, top_k=top_k)

    # Build a prompt using goal + retrieved content
    prompt = build_roadmap_prompt(goal=user_goal, context_chunks=context_chunks)

    # Call the LLM to generate the final roadmap
    roadmap = call_llm(prompt=prompt, model="openchat/openchat-3.5")  # or another provider/model
    return roadmap
