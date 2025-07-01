# document_analyzer.py
import json
import re
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from ai_services.llm_client import LLMClient
from ai_services.indexer import index_chunks, search_chunks, remove_document
from ai_services.utils.prompts import PromptTemplates
from ai_services.utils.input_validator import InputValidator
from models import File as FileModel, User as UserModel


class DocumentAnalyzer:
    """Service to analyze documents, persist them, and handle related queries."""

    def __init__(self):
        """Initializes the analyzer with necessary clients and utilities."""
        try:
            self.llm_client = LLMClient()
            self.prompt_templates = PromptTemplates()
            self.validator = InputValidator()
            print("✅ DocumentAnalyzer initialized successfully.")
        except Exception as e:
            print(f"❌ Error initializing DocumentAnalyzer: {e}")
            self.llm_client = None
            self.prompt_templates = None
            self.validator = None

    def add_document(
        self, db: Session, user_id: str, filename: str, content_type: str, text_content: str
    ) -> FileModel:
        """Analyzes, persists, and indexes a document for a given user."""
        # 1. Validate input
        if not all([self.validator, self.llm_client, self.prompt_templates]):
            raise ConnectionError("DocumentAnalyzer is not properly initialized.")

        if not self.validator.validate_text_content(text_content) or not self.validator.validate_filename(filename):
            raise ValueError("Invalid input: Text content or filename is not valid.")

        cleaned_content = self.validator.sanitize_text(text_content)
        if not cleaned_content:
            raise ValueError("Content is empty after cleaning.")

        # 2. Generate AI analysis
        word_count = len(cleaned_content.split())
        chunks = self._create_chunks(cleaned_content)
        print(f"📄 Processing document: {filename} ({word_count} words, {len(chunks)} chunks)")

        summary = self._generate_summary(cleaned_content)
        key_points = self._extract_key_points(cleaned_content)
        qa_cards = self._generate_qa_cards(cleaned_content, summary)

        # 3. Create and save the File record to the database
        new_file = FileModel(
            user_id=user_id,
            filename=filename,
            content_type=content_type,
            word_count=word_count,
            summary=summary,
            key_points=json.dumps(key_points),  # Serialize list to JSON string
            qa_cards=json.dumps(qa_cards),    # Serialize list of dicts to JSON string
            status="processed",
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        # 4. Index the document chunks for semantic search
        if chunks:
            # Use the newly created file's ID for indexing
            index_chunks(str(new_file.id), chunks)

        print(f"✅ Document '{filename}' analyzed and stored with ID: {new_file.id}")
        return new_file

    def get_document(self, db: Session, user_id: str, document_id: str) -> Optional[FileModel]:
        """Retrieves a single document for a user from the database."""
        return db.query(FileModel).filter(
            FileModel.id == document_id, 
            FileModel.user_id == user_id
        ).first()

    def list_documents(self, db: Session, user_id: str) -> List[FileModel]:
        """Retrieves all documents for a specific user from the database."""
        return db.query(FileModel).filter(FileModel.user_id == user_id).order_by(FileModel.created_at.desc()).all()

    def delete_document(self, db: Session, user_id: str, document_id: str) -> bool:
        """Deletes a document from the database and the search index."""
        doc_to_delete = self.get_document(db, user_id, document_id)
        if doc_to_delete:
            db.delete(doc_to_delete)
            db.commit()
            remove_document(str(document_id))  # Remove from search index
            print(f"🗑️ Document with ID {document_id} deleted.")
            return True
        return False

    def chat_with_document(self, db: Session, user_id: str, document_id: str, query: str) -> Dict:
        """Generates a chat response by querying the document's indexed content."""
        if not self.llm_client or not self.prompt_templates or not self.validator:
            raise ConnectionError("DocumentAnalyzer is not properly initialized.")

        # 1. Validate that the document exists and belongs to the user
        document = self.get_document(db, user_id, document_id)
        if not document:
            raise ValueError("Document not found or access denied.")

        # 2. Find relevant context from the indexed chunks
        sanitized_query = self.validator.sanitize_text(query)
        search_results = search_chunks(sanitized_query, document_id=str(document.id))
        context = "\n".join([res['content'] for res in search_results])
        if not context:
            context = document.summary  # Fallback to summary if no relevant chunks are found

        # 3. Build prompt and get LLM response
        prompt = self.prompt_templates.get_chat_prompt(
            doc_content=context,
            user_query=sanitized_query,
            chat_history=[] # Placeholder for future chat history implementation
        )
        response = self.llm_client.generate_content(prompt)

        if not response or not response.text:
            raise ConnectionError("Failed to get a valid response from the LLM.")

        return {
            "response": response.text,
            "document_id": document_id,
            "debug_info": {"prompt_length": len(prompt), "context_used": context},
        }

    # Internal helper methods for AI content generation
    def _create_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Create overlapping chunks from text."""
        if not text:
            return []
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunks.append(' '.join(words[i:i + chunk_size]))
        return chunks

    def _generate_summary(self, content: str) -> str:
        """Generate a summary for the given content."""
        prompt = self.prompt_templates.get_summary_prompt(content)
        response = self.llm_client.generate_content(prompt)
        return response.text if response and response.text else "Could not generate summary."

    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from the content."""
        prompt = self.prompt_templates.get_key_points_prompt(content)
        response = self.llm_client.generate_content(prompt)
        if not response or not response.text:
            return []
        return [p.strip() for p in response.text.split('\n') if p.strip() and p.strip().startswith("*")]

    def _generate_qa_cards(self, content: str, summary: str) -> List[Dict]:
        """Generate Q&A cards from the content."""
        prompt = self.prompt_templates.get_qa_cards_prompt(content, summary)
        response = self.llm_client.generate_content(prompt)
        if not response or not response.text:
            return []
        try:
            # The response is expected to be a JSON string of a list of objects
            qa_list = json.loads(response.text)
            return qa_list if isinstance(qa_list, list) else []
        except json.JSONDecodeError:
            print(f"⚠️ Failed to decode JSON for Q&A cards. Raw: {response.text}")
            return self._parse_qa_text_fallback(response.text)

    def _parse_qa_text_fallback(self, text: str) -> List[Dict]:
        """Fallback to parse plain text Q&A into a list of dicts."""
        cards = []
        pairs = re.findall(r'Q: (.*?)\nA: (.*?)(?=\nQ:|$)', text, re.DOTALL)
        for q, a in pairs:
            cards.append({"question": q.strip(), "answer": a.strip()})
        return cards

    def _find_relevant_context(self, question: str, chunks: List[str]) -> List[str]:
        """Find most relevant chunks for the question"""

        try:
            if not question or not chunks:
                return []

            # Simple keyword-based relevance (can be improved with embeddings)
            question_words = set(word.lower() for word in question.split() if len(word) > 2)

            if not question_words:
                return chunks[:5]  # Return first 5 chunks if no meaningful words

            chunk_scores = []
            for chunk in chunks:
                if not chunk:
                    continue

                chunk_words = set(word.lower() for word in chunk.split() if len(word) > 2)
                common_words = question_words.intersection(chunk_words)
                score = len(common_words) / len(question_words) if question_words else 0
                chunk_scores.append((chunk, score))

            # Sort by relevance score
            chunk_scores.sort(key=lambda x: x[1], reverse=True)

            return [chunk for chunk, _ in chunk_scores[:5]]  # Top 5 relevant chunks

        except Exception as e:
            print(f"❌ Error finding relevant context: {e}")
            return chunks[:5] if chunks else []

    def _create_chunks(self, content: str, chunk_size: int = 500) -> List[str]:
        """Create text chunks for processing"""

        try:
            if not content:
                return []

            # Split by sentences first
            sentences = re.split(r'[.!?]+', content)

            if not sentences:
                return [content] if len(content) > 50 else []

            chunks = []
            current_chunk = ""

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                if len(current_chunk) + len(sentence) < chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "

            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            return [chunk for chunk in chunks if len(chunk) > 50]  # Filter out very short chunks

        except Exception as e:
            print(f"❌ Error creating chunks: {e}")
            return [content] if content and len(content) > 50 else []

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""

        try:
            if not text or not isinstance(text, str):
                return ""

            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)

            # Remove special characters but keep punctuation
            text = re.sub(r'[^\w\s.,!?;:()\-"]', '', text)

            return text.strip()

        except Exception as e:
            print(f"❌ Error cleaning text: {e}")
            return str(text) if text else ""

    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        try:
            # This is a placeholder - you might want to use a proper language detection library
            if not text:
                return "unknown"
            return "en"  # Default to English
        except:
            return "unknown"

    def _calculate_readability(self, text: str) -> float:
        """Calculate simple readability score"""

        try:
            if not text:
                return 0.0

            words = text.split()
            sentences = re.split(r'[.!?]+', text)
            sentences = [s for s in sentences if s.strip()]  # Remove empty sentences

            if len(sentences) == 0 or len(words) == 0:
                return 0.0

            avg_words_per_sentence = len(words) / len(sentences)

            # Simple readability metric (lower is more readable)
            return avg_words_per_sentence
        except Exception as e:
            print(f"Error calculating readability: {e}")
            return 0.0

    def _extract_json_content(self, response: str, key: str) -> Any:
        """Extract JSON content from LLM response""" 
        try:
            # Find the JSON block
            match = re.search(r'```json\n({.*?})\n```', response, re.DOTALL)
            if not match:
                # Fallback for non-fenced JSON
                match = re.search(r'({.*?})', response, re.DOTALL)

            if match:
                json_str = match.group(1)
                data = json.loads(json_str)
                return data.get(key)
            else:
                # If no JSON, try to parse the whole response
                try:
                    data = json.loads(response)
                    return data.get(key)
                except json.JSONDecodeError:
                    # If parsing fails, return the raw response for the key if it exists as a string
                    return response if key in response else None
        except Exception as e:
            print(f"Error extracting JSON for key '{key}': {e}")
            return None


