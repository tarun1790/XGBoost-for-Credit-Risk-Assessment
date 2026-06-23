import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Autonomous Computer Use Agent Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_db")
    
    # ChromaDB Settings
    CHROMADB_DIR: str = os.getenv("CHROMADB_DIR", "./data/chroma")
    
    # LLM Settings (Ollama / Local Inference)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b") # default fast local model
    OLLAMA_VISION_MODEL: str = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5-vl:7b") # default vision model
    
    # Safety and Security
    DOMAIN_ALLOWLIST: list[str] = ["localhost", "127.0.0.1", "google.com", "github.com", "wikipedia.org"]
    HITL_REQUIRED: bool = True # Human-in-the-loop checkpoint required for sensitive actions
    
    # Execution parameters
    SCREENSHOTS_DIR: str = os.getenv("SCREENSHOTS_DIR", "./data/screenshots")
    MAX_STEPS_PER_TASK: int = 30
    
    class Config:
        case_sensitive = True

settings = Settings()
