# app/utils/prompts.py

def build_roadmap_prompt(goal: str, context_chunks: list[str]) -> str:
    return f"""
User Goal:
{goal}

Relevant Knowledge:
{'\n\n---\n\n'.join(context_chunks)}

Instruction:
Using the user goal and the resources above, generate a personalized learning roadmap.
- Include structured steps
- Add links where applicable
- Make it beginner-friendly unless otherwise stated
"""
