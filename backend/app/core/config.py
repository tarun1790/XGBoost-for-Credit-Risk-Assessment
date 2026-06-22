import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Luffy Risk Management"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings
    # Use postgresql+asyncpg for async SQLAlchemy database operations
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/credit_risk"
    
    # Security Settings
    JWT_SECRET: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7" # Development default
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 1 week
    
    # ML Model Settings
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    MODEL_PATH: str = os.path.join(BASE_DIR, "ml_pipeline", "models", "model.json")
    PREPROCESSOR_PATH: str = os.path.join(BASE_DIR, "ml_pipeline", "models", "preprocessor.pkl")
    EXPLAINER_PATH: str = os.path.join(BASE_DIR, "ml_pipeline", "models", "explainer.pkl")
    METADATA_PATH: str = os.path.join(BASE_DIR, "ml_pipeline", "models", "metadata.pkl")
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
