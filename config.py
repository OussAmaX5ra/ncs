from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Manages application settings using pydantic-settings for robust validation."""
    # Configure pydantic-settings to load from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database settings
    DATABASE_URL: str

    # API keys
    GEMINI_API_KEY: str

    # Security settings
    SECRET_KEY: str

# Create a single instance of the settings
settings = Settings()

class Settings(BaseSettings):
    """Manages application settings using pydantic-settings for robust validation."""
    # Configure pydantic-settings to load from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Define your application's settings
    # These will be loaded from the .env file and validated
    DATABASE_URL: str
    GEMINI_API_KEY: str
    SECRET_KEY: str

# Create a single, global instance of the settings object
# This will be imported by other parts of the application
settings = Settings()
