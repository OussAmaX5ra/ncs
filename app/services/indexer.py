# app/services/indexer.py

import os
import json
from sentence_transformers import SentenceTransformer
import chromadb

# Load model and Chroma client once (global)
model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection(name="roadmap_chunks")


def load_json_folder(folder_path: str):
    """Load individual JSON files as roadmap chunks."""
    chunks = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            filepath = os.path.join(folder_path, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                doc_id = filename.replace(".json", "")
                links_text = "\n".join([f"- {l['title']} ({l['url']})" for l in data.get("links", [])])
                full_text = f"Title: {data['title']}\n\nDescription: {data['description']}\n\nResources:\n{links_text}"
                chunks.append((doc_id, full_text, {"title": data["title"]}))
    return chunks


def index_chunks(chunks):
    """Embed and store roadmap chunks in vector DB."""
    for doc_id, text, metadata in chunks:
        embedding = model.encode(text).tolist()
        collection.add(
            documents=[text],
            embeddings=[embedding],
            ids=[doc_id],
            metadatas=[metadata]
        )


def query_chunks(user_goal: str, top_k=5):
    """Query top K relevant chunks based on the user goal."""
    embedding = model.encode(user_goal).tolist()
    results = collection.query(
        query_embeddings=[embedding],
        n_results=top_k
    )
    return results["documents"][0]
