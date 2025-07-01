# ai_services/vector_store.py
import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from logging import getLogger
import json
import glob

logger = getLogger(__name__)

class VectorStore:
    """Manages text embeddings for context retrieval."""

    def __init__(self, model_name='all-MiniLM-L6-v2', index_file='data/vector_index.pkl'):
        self.model = SentenceTransformer(model_name)
        self.index_file = index_file
        self.chunks = []
        self.embeddings = []
        self.load_index()

    def add_chunks(self, new_chunks: list[str]):
        """Add new chunks to the index and save."""
        if not new_chunks:
            logger.warning("No new chunks to add.")
            return

        logger.info(f"Adding {len(new_chunks)} new chunks to the index.")
        new_embeddings = self.model.encode(new_chunks, show_progress_bar=True)
        
        if self.embeddings is None or len(self.embeddings) == 0:
            self.embeddings = new_embeddings
        else:
            # Ensure embeddings are numpy arrays before stacking
            if not isinstance(self.embeddings, np.ndarray):
                self.embeddings = np.array(self.embeddings)
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
            
        self.chunks.extend(new_chunks)
        logger.info("Generated embeddings for new chunks.")
        self.save_index()

    def build_index_from_text(self, text: str, chunk_size=512, overlap=50):
        """Create vector index from a single large text."""
        if not text:
            logger.warning("Text for indexing is empty. Index not built.")
            return

        text_chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            text_chunks.append(text[start:end])
            start += chunk_size - overlap
        
        self.add_chunks(text_chunks)

    def load_and_index_roadmaps(self, roadmaps_dir: str):
        """Load JSON roadmaps, create text chunks, and add them to the index."""
        json_files = glob.glob(os.path.join(roadmaps_dir, '*.json'))
        if not json_files:
            logger.warning(f"No JSON files found in {roadmaps_dir}. No roadmaps indexed.")
            return

        logger.info(f"Found {len(json_files)} JSON roadmap files to index.")
        new_chunks = []
        for file_path in json_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        title = value.get('title', '')
                        description = value.get('description', '')
                        if title and description:
                            chunk = f"Topic: {title}\n{description}"
                            new_chunks.append(chunk)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to read or parse {os.path.basename(file_path)}: {e}")
        
        self.add_chunks(new_chunks)

    def save_index(self):
        """Save chunks and embeddings to a pickle file."""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        try:
            with open(self.index_file, 'wb') as f:
                pickle.dump({'chunks': self.chunks, 'embeddings': self.embeddings}, f)
            logger.info(f"Index saved successfully to {self.index_file}")
        except IOError as e:
            logger.error(f"Error saving index to {self.index_file}: {e}")

    def load_index(self):
        """Load index from a pickle file if it exists."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'rb') as f:
                    data = pickle.load(f)
                    self.chunks = data.get('chunks', [])
                    self.embeddings = data.get('embeddings', [])
                logger.info(f"Index loaded successfully from {self.index_file}")
            except (IOError, pickle.PickleError) as e:
                logger.error(f"Error loading index from {self.index_file}: {e}")
                self.chunks, self.embeddings = [], []
        else:
            logger.warning(f"Index file {self.index_file} not found. Starting with an empty index.")

    def query_chunks(self, query: str, top_k=3) -> list[str]:
        """Find the most relevant text chunks for a given query."""
        if not self.chunks or self.embeddings is None or len(self.embeddings) == 0:
            logger.warning("Index is empty. Cannot perform a query.")
            return []

        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings).flatten()
        
        num_chunks = len(self.chunks)
        k = min(top_k, num_chunks)
        if k == 0: return []
            
        top_indices = np.argsort(similarities)[-k:][::-1]
        
        return [self.chunks[i] for i in top_indices]

# Global instance
vector_store = VectorStore()

def initialize_learning_context():
    """Read context files and build the vector store index."""
    # Check if the index is already populated to avoid re-indexing on every startup
    if vector_store.chunks:
        logger.info("Vector store already populated. Skipping initialization.")
        return

    logger.info("Initializing learning context for RAG...")
    # 1. Initialize from the generic learning context text file
    learning_context_file = 'learning_context.txt'
    if os.path.exists(learning_context_file):
        try:
            with open(learning_context_file, 'r', encoding='utf-8') as f:
                content = f.read()
            vector_store.build_index_from_text(content)
        except Exception as e:
            logger.error(f"Failed to initialize from {learning_context_file}: {e}")
    else:
        logger.warning(f"Context file not found: {learning_context_file}")

    # 2. Initialize from the JSON roadmaps data
    roadmaps_dir = 'data/roadmaps'
    if os.path.isdir(roadmaps_dir):
        vector_store.load_and_index_roadmaps(roadmaps_dir)
    else:
        logger.warning(f"Roadmaps directory not found: {roadmaps_dir}")
