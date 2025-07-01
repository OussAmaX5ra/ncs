# indexer.py
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib


class DocumentIndexer:
    """Simple document indexer for chunk storage and retrieval"""

    def __init__(self, index_file: str = "document_index.json"):
        self.index_file = index_file
        self.index = self._load_index()

    def _load_index(self) -> Dict[str, Any]:
        """Load existing index from file"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"documents": {}, "chunks": {}, "metadata": {"created": datetime.now().isoformat()}}
        except Exception as e:
            print(f"Error loading index: {e}")
            return {"documents": {}, "chunks": {}, "metadata": {"created": datetime.now().isoformat()}}

    def _save_index(self):
        """Save index to file"""
        try:
            self.index["metadata"]["last_updated"] = datetime.now().isoformat()
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving index: {e}")

    def _generate_chunk_id(self, content: str, document_id: str, chunk_index: int) -> str:
        """Generate unique chunk ID"""
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{document_id}_{chunk_index}_{content_hash}"

    def index_chunks(self, chunks: List[str], document_id: str) -> bool:
        """Index document chunks for retrieval"""
        try:
            if not chunks or not document_id:
                return False

            # Store document info
            self.index["documents"][document_id] = {
                "chunk_count": len(chunks),
                "indexed_at": datetime.now().isoformat(),
                "chunk_ids": []
            }

            # Index each chunk
            for i, chunk in enumerate(chunks):
                if not chunk or not chunk.strip():
                    continue

                chunk_id = self._generate_chunk_id(chunk, document_id, i)

                self.index["chunks"][chunk_id] = {
                    "content": chunk.strip(),
                    "document_id": document_id,
                    "chunk_index": i,
                    "word_count": len(chunk.split()),
                    "indexed_at": datetime.now().isoformat()
                }

                self.index["documents"][document_id]["chunk_ids"].append(chunk_id)

            self._save_index()
            return True

        except Exception as e:
            print(f"Error indexing chunks: {e}")
            return False

    def search_chunks(self, query: str, document_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant chunks"""
        try:
            if not query:
                return []

            query_words = set(word.lower() for word in query.split() if len(word) > 2)
            if not query_words:
                return []

            scored_chunks = []

            for chunk_id, chunk_data in self.index["chunks"].items():
                # Filter by document if specified
                if document_id and chunk_data["document_id"] != document_id:
                    continue

                content = chunk_data["content"].lower()
                content_words = set(word.lower() for word in content.split() if len(word) > 2)

                # Calculate relevance score
                common_words = query_words.intersection(content_words)
                if common_words:
                    score = len(common_words) / len(query_words)
                    scored_chunks.append({
                        "chunk_id": chunk_id,
                        "content": chunk_data["content"],
                        "document_id": chunk_data["document_id"],
                        "score": score,
                        "chunk_index": chunk_data["chunk_index"]
                    })

            # Sort by score and return top results
            scored_chunks.sort(key=lambda x: x["score"], reverse=True)
            return scored_chunks[:limit]

        except Exception as e:
            print(f"Error searching chunks: {e}")
            return []

    def get_document_chunks(self, document_id: str) -> List[str]:
        """Get all chunks for a document"""
        try:
            if document_id not in self.index["documents"]:
                return []

            chunk_ids = self.index["documents"][document_id]["chunk_ids"]
            chunks = []

            for chunk_id in chunk_ids:
                if chunk_id in self.index["chunks"]:
                    chunks.append(self.index["chunks"][chunk_id]["content"])

            return chunks

        except Exception as e:
            print(f"Error getting document chunks: {e}")
            return []

    def remove_document(self, document_id: str) -> bool:
        """Remove document and its chunks from index"""
        try:
            if document_id not in self.index["documents"]:
                return False

            # Remove chunks
            chunk_ids = self.index["documents"][document_id]["chunk_ids"]
            for chunk_id in chunk_ids:
                if chunk_id in self.index["chunks"]:
                    del self.index["chunks"][chunk_id]

            # Remove document
            del self.index["documents"][document_id]

            self._save_index()
            return True

        except Exception as e:
            print(f"Error removing document: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get indexer statistics"""
        try:
            return {
                "total_documents": len(self.index["documents"]),
                "total_chunks": len(self.index["chunks"]),
                "index_file_size": os.path.getsize(self.index__file) if os.path.exists(self.index_file) else 0,
                "last_updated": self.index["metadata"].get("last_updated", "Never")
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}


# Global indexer instance
_indexer = DocumentIndexer()


def index_chunks(chunks: List[str], document_id: str) -> bool:
    """Global function to index chunks"""
    return _indexer.index_chunks(chunks, document_id)

def search_chunks(query: str, document_id: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Global function to search chunks"""
    return _indexer.search_chunks(query, document_id, limit)


def get_document_chunks(document_id: str) -> List[str]:
    """Global function to get document chunks"""
    return _indexer.get_document_chunks(document_id)

def remove_document(document_id: str) -> bool:
    """Global function to remove document"""
    return _indexer.remove_document(document_id)
