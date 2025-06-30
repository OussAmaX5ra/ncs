# llm_debugger.py
from app.web.services.indexer import query_chunks
from app.web.utils.prompts import build_roadmap_prompt
from app.web.services.llm_client import call_llm  # You might need to create this

def generate_learning_roadmap(goal: str) -> str:
    context_chunks = query_chunks(goal)
    prompt = build_roadmap_prompt(goal, context_chunks)
    result = call_llm(prompt)
    return result
