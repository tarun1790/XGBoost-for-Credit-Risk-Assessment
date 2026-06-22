import os
import sys
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

# Ensure python path includes repository root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.main import app
from backend.app.core.db import Base, get_db
from backend.app.services.ml_service import ml_service

# Test database URL: In-memory SQLite for self-contained testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def async_db_init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def async_db_cleanup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="session", autouse=True)
def db_setup():
    """Initializes the database tables synchronously before the session starts."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(async_db_init())
        yield
        loop.run_until_complete(async_db_cleanup())
    finally:
        loop.close()

@pytest.fixture(autouse=True)
def override_db_dependency():
    """Overrides the FastAPI database session dependency with the test session local."""
    async def _get_test_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
            
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.pop(get_db, None)


# --- UNIT TESTS FOR ML CALCULATIONS ---
def test_ml_service_predict_mock():
    """Validates that MLService loads model artifacts and evaluates risk metrics correctly."""
    # Ensure artifacts are loaded
    ml_service.load_artifacts()
    assert ml_service.is_loaded is True
    
    # Create test input resembling Home Credit features
    mock_input = {
        "NAME_CONTRACT_TYPE": "Cash loans",
        "CODE_GENDER": "F",
        "FLAG_OWN_CAR": "N",
        "FLAG_OWN_REALTY": "Y",
        "CNT_CHILDREN": 0,
        "AMT_INCOME_TOTAL": 150000.0,
        "AMT_CREDIT": 400000.0,
        "AMT_ANNUITY": 20000.0,
        "DAYS_BIRTH": -15000, # ~41 years old
        "DAYS_EMPLOYED": -1500, # ~4 years employed
        "OWN_CAR_AGE": None,
        "CNT_FAM_MEMBERS": 1,
        "REGION_RATING_CLIENT": 2,
        "EXT_SOURCE_1": 0.6,
        "EXT_SOURCE_2": 0.7,
        "EXT_SOURCE_3": 0.55
    }
    
    results = ml_service.predict(mock_input)
    
    # Assert result structure and ranges
    assert "probability_of_default" in results
    assert "credit_score" in results
    assert "risk_category" in results
    assert "shap_explanations" in results
    
    pd = results["probability_of_default"]
    score = results["credit_score"]
    
    assert 0.0 <= pd <= 1.0
    assert 300 <= score <= 850
    assert isinstance(results["risk_category"], str)
    assert len(results["shap_explanations"]) > 0


# --- INTEGRATION TESTS FOR API ENDPOINTS ---
def test_auth_and_user_creation():
    """Verifies user registration, login, JWT validation, and RBAC controls."""
    client = TestClient(app)
    
    # 1. Register a test ADMIN account
    reg_payload = {
        "username": "testadmin",
        "email": "testadmin@creditrisk.com",
        "password": "AdminSecurePassword123",
        "role": "ADMIN"
      }
    response = client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201
    assert response.json()["username"] == "testadmin"
    assert response.json()["role"] == "ADMIN"
    
    # 2. Authenticate and retrieve token
    login_data = {
        "username": "testadmin",
        "password": "AdminSecurePassword123"
    }
    login_resp = client.post("/api/v1/auth/token", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert token is not None
    
    # 3. Test current user /me endpoint using token
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "testadmin"
    
    # 4. Test fetch audit logs (requires admin)
    audit_resp = client.get("/api/v1/auth/audit", headers=headers)
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) > 0
