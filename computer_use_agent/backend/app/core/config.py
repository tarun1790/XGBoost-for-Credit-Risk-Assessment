import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Autonomous Computer Use Agent Platform (HF)"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/agent_db")
    
    # ChromaDB Settings
    CHROMADB_DIR: str = os.getenv("CHROMADB_DIR", "./data/chroma")
    
    # Hugging Face Inference Settings (Local GPU)
    HF_MODEL_ID: str = os.getenv("HF_MODEL_ID", "Qwen/Qwen2.5-Coder-7B-Instruct") # Local quantized LLM
    HF_EMBEDDING_MODEL: str = os.getenv("HF_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    USE_GPU: bool = True
    LOAD_IN_4BIT: bool = True
    
    # Safety and Security
    DOMAIN_ALLOWLIST: list[str] = ["localhost", "127.0.0.1", "google.com", "github.com", "wikipedia.org"]
    HITL_REQUIRED: bool = True # Human-in-the-loop checkpoint required for sensitive actions
    
    # Evidence & Screenshots storage (Locked to Windows standard directory)
    SCREENSHOTS_DIR: str = "C:\\AgentEvidence"
    MAX_STEPS_PER_TASK: int = 30
    
    class Config:
        case_sensitive = True

settings = Settings()
