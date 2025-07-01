# ai_services/utils/roadmap_input_validator.py
import re

class RoadmapInputValidator:
    """Validates and processes user queries for learning roadmap generation."""

    def __init__(self):
        # Patterns to identify non-learning queries
        self.non_learning_patterns = [
            r"^\s*(hi|hello|hey|thanks|test|ping|pong)\s*$",
            r"^\s*\W+\s*$",  # Only punctuation
            r"^\d+\s*$"      # Only numbers
        ]

        # Keywords indicating a learning-related query
        self.learning_keywords = [
            'learn', 'master', 'understand', 'become', 'guide',
            'roadmap', 'tutorial', 'course', 'study', 'develop'
        ]

    def is_valid_learning_query(self, query: str) -> tuple[bool, str, list[str]]:
        """Check if a query is a valid, learning-focused request."""
        query = query.strip().lower()

        if not query:
            return False, "Query cannot be empty.", []

        # Check for non-learning patterns
        for pattern in self.non_learning_patterns:
            if re.match(pattern, query, re.IGNORECASE):
                return False, "Query appears to be a greeting or test, not a learning goal.", []

        # Check for presence of learning keywords
        if not any(keyword in query for keyword in self.learning_keywords):
            # If no keywords, check if it's a simple topic (e.g., "python", "data science")
            if len(query.split()) > 4:
                return False, "Query is too long and doesn't seem to be a learning goal. Try a shorter topic.", [
                    "'I want to learn about [your topic]'",
                    "'Roadmap for [your topic]'"
                ]

        return True, "Valid learning query.", []

    def enhance_query(self, query: str) -> str:
        """Enhance a simple query to be more descriptive for the LLM."""
        query = query.strip()
        # If the query is just a topic, frame it as a learning goal
        if len(query.split()) <= 3 and not any(keyword in query.lower() for keyword in self.learning_keywords):
            return f"Create a comprehensive learning roadmap for '{query}'."
        return query

# Instantiate the validator for easy import and use
roadmap_input_validator = RoadmapInputValidator()
