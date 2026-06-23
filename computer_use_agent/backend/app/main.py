import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.db import engine, Base
from app.api.routes import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configuration for cross-origin local React requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup hook to initialize SQL schemas
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Ensure static directory exists
    os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)

# Register routes
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount screenshots directory to serve visual audits to the React client
app.mount("/static/screenshots", StaticFiles(directory=settings.SCREENSHOTS_DIR), name="screenshots")

@app.get("/")
def read_root():
    return {"message": "Autonomous Computer Use Agent API is online."}
