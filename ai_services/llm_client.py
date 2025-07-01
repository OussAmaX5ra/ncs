import os
import time
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMClient:
    """Enhanced Gemini 1.5 client with advanced configuration"""

    def __init__(self):
        # Load environment variables
        load_dotenv()

        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            # Try alternative environment variable names
            self.api_key = os.getenv('GOOGLE_API_KEY')

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY or GOOGLE_API_KEY environment variable is required. Please check your .env file.")

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Initialize model with optimal settings for document analysis
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",  # Using Gemini 1.5 Pro for better analysis
            generation_config=self._get_generation_config(),
            safety_settings=self._get_safety_settings()
        )

        # Performance tracking
        self.request_count = 0
        self.total_tokens = 0
        self.total_response_time = 0.0

        logging.info("Gemini 1.5 Pro client initialized successfully")
        print(f"✅ Gemini 1.5 Pro client initialized with API key: {self.api_key[:10]}...")

    def call_llm(self, prompt: str) -> str:
        """A simple wrapper to call the LLM with a given prompt."""
        try:
            # For simplicity, this wrapper uses the main generate_content method
            response = self.generate_content(prompt)
            return response
        except Exception as e:
            logging.error(f"Error in call_llm: {e}")
            # Depending on desired behavior, re-raise or return an error message
            raise e

    def _get_generation_config(self) -> genai.GenerationConfig:
        """Optimized generation configuration for document analysis"""
        return genai.GenerationConfig(
            temperature=0.2,  # Lower temperature for more consistent analysis
            top_p=0.8,
            top_k=40,
            max_output_tokens=4096,  # Increased for comprehensive responses
            candidate_count=1,
            stop_sequences=[]
        )

    def _get_safety_settings(self) -> list:
        """Safety settings for document analysis"""
        return [
            {
                "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            },
            {
                "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            },
            {
                "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            },
            {
                "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
            }
        ]

    def generate_content(self, prompt: str, **kwargs) -> str:
        """Generate content with enhanced error handling and retries"""

        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # Generate content
                response = self.model.generate_content(
                    prompt,
                    generation_config=kwargs.get('generation_config', self._get_generation_config()),
                    safety_settings=kwargs.get('safety_settings', self._get_safety_settings())
                )

                # Calculate response time
                response_time = time.time() - start_time

                # Update statistics
                self.request_count += 1
                self.total_response_time += response_time

                # Extract text from response
                if response.candidates and len(response.candidates) > 0:
                    text_response = response.candidates[0].content.parts[0].text

                    # Estimate tokens (rough approximation)
                    estimated_tokens = len(text_response.split()) * 1.3
                    self.total_tokens += estimated_tokens

                    logging.info(f"Generated response in {response_time:.2f}s, ~{estimated_tokens} tokens")
                    return text_response
                else:
                    raise Exception("No valid response generated")

            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise Exception(f"Failed to generate content after {max_retries} attempts: {str(e)}")

    def generate_content_stream(self, prompt: str, **kwargs):
        """Generate streaming content for real-time responses"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=kwargs.get('generation_config', self._get_generation_config()),
                safety_settings=kwargs.get('safety_settings', self._get_safety_settings()),
                stream=True
            )

            for chunk in response:
                if chunk.candidates and len(chunk.candidates) > 0:
                    yield chunk.candidates[0].content.parts[0].text

        except Exception as e:
            logging.error(f"Streaming generation failed: {str(e)}")
            yield f"Error: {str(e)}"

    def analyze_with_context(self, content: str, analysis_type: str = "comprehensive") -> str:
        """Specialized analysis with context-aware prompting"""

        context_prompts = {
            "comprehensive": """
            Analyze this document comprehensively, focusing on:
            1. Main themes and key concepts
            2. Structure and organization
            3. Important details and insights
            4. Potential applications or implications

            Provide a detailed analysis that would be valuable for someone studying or working with this content.
            """,

            "summary": """
            Create a concise but comprehensive summary that captures:
            1. The core message or purpose
            2. Key points and supporting details
            3. Important conclusions or recommendations

            Make it accessible and actionable for the reader.
            """,

            "educational": """
            Analyze this content from an educational perspective:
            1. Learning objectives and key concepts
            2. Difficulty level and prerequisite knowledge
            3. Practical applications and examples
            4. Potential questions for assessment

            Structure the analysis to support effective learning and teaching.
            """
        }

        base_prompt = context_prompts.get(analysis_type, context_prompts["comprehensive"])
        full_prompt = f"{base_prompt}\n\nCONTENT TO ANALYZE:\n{content}"

        return self.generate_content(full_prompt)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get client performance statistics"""

        avg_response_time = (
            self.total_response_time / self.request_count
            if self.request_count > 0 else 0
        )

        return {
            "total_requests": self.request_count,
            "total_tokens": int(self.total_tokens),
            "average_response_time": round(avg_response_time, 2),
            "total_response_time": round(self.total_response_time, 2),
            "model_name": "gemini-1.5-pro",
            "api_configured": bool(self.api_key)
        }

    def reset_stats(self):
        """Reset performance statistics"""
        self.request_count = 0
        self.total_tokens = 0
        self.total_response_time = 0.0
        logging.info("Performance statistics reset")

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Gemini API"""

        try:
            test_prompt = "Respond with 'Connection successful' if you can read this."
            response = self.generate_content(test_prompt)

            return {
                "success": True,
                "message": "Connection to Gemini 1.5 Pro is working",
                "response": response[:100],
                "model": "gemini-1.5-pro"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error": str(e),
                "model": "gemini-1.5-pro"
            }
