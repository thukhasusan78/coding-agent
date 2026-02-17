import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Configuration settings for the Chinese Tutor application."""
    
    APP_NAME = "Chinese Tutor AI"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Model Settings
    PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gpt-4o")
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 2000))

    # Database Settings
    # Path to the SQLite checkpoints database
    CHECKPOINTS_DB_PATH = os.getenv(
        "CHECKPOINTS_DB_PATH", 
        str(BASE_DIR / "checkpoints.sqlite")
    )
    
    # Path to the ChromaDB vector store
    MEMORY_DB_PATH = os.getenv(
        "MEMORY_DB_PATH", 
        str(BASE_DIR / "memory_db")
    )

    # Tutor Specific Settings
    DEFAULT_LANGUAGE_LEVEL = "HSK1"  # HSK1 to HSK6
    SUPPORTED_LEVELS = ["HSK1", "HSK2", "HSK3", "HSK4", "HSK5", "HSK6"]
    
    # Logging
    LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "app.log"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate_config(cls):
        """Validates that essential configuration is present."""
        if not cls.OPENAI_API_KEY:
            print("WARNING: OPENAI_API_KEY is not set. LLM features will fail.")
        
        # Ensure directories exist
        Path(cls.MEMORY_DB_PATH).mkdir(parents=True, exist_ok=True)

# Initialize configuration
config = Config()

if __name__ == "__main__":
    # Simple validation check when running the script directly
    config.validate_config()
    print(f"Configuration loaded for: {config.APP_NAME}")
    print(f"Database Path: {config.CHECKPOINTS_DB_PATH}")