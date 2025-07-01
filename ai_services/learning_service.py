# ai_services/learning_service.py

class LearningService:
    """A service to handle learning-related functionalities."""

    def __init__(self):
        self.initialized = False

    def initialize(self):
        """Initializes the learning service."""
        print("INFO:     Initializing Learning Service...")
        self.initialized = True
        print("INFO:     Learning Service initialized.")

# Create a global instance of the service
learning_service = LearningService()
