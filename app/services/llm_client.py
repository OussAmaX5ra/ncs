import requests
import os

API_KEY = os.getenv("OPENROUTER_API_KEY")

def call_llm(prompt: str):
    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "openchat/openchat-3.5-0106",
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return res.json()['choices'][0]['message']['content']
