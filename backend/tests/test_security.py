import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.core.db import get_db, Base
from backend.app.core.security import get_password_hash, compute_audit_hash
from backend.app.core.rate_limiter import rate_limiter, lockout_manager
from backend.app.models.models import User, Customer, AuditLog
from backend.app.services.audit_service import audit_service

# SQLite in-memory test database for isolated security test execution
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """Resets rate limiters and lockout state between test executions."""
    rate_limiter._requests.clear()
    lockout_manager._failed_attempts.clear()
    lockout_manager._locked_until.clear()

@pytest.mark.asyncio
async def test_security_http_headers():
    """Validates that OWASP security headers (CSP, HSTS, X-Frame-Options, nosniff) are enforced."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "Strict-Transport-Security" in response.headers
    assert "Content-Security-Policy" in response.headers
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_sliding_window_rate_limiter():
    """Validates sliding-window rate limiting on authentication endpoints."""
    # Reset limiters for clean test
    rate_limiter._requests.clear()

    # Simulate 5 rapid requests from same test client IP
    for _ in range(5):
        client.post(
            "/api/v1/auth/token",
            data={"username": "test_rl", "password": "WrongPassword"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

    # 6th request must be throttled with HTTP 429 Too Many Requests
    throttled = client.post(
        "/api/v1/auth/token",
        data={"username": "test_rl", "password": "WrongPassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert throttled.status_code == 429
    assert "Retry-After" in throttled.headers


def test_account_lockout_after_consecutive_failures():
    """Validates that 5 consecutive failed passwords trigger an automatic account lockout."""
    username = "target_analyst"
    ip = "192.168.1.100"

    for i in range(4):
        is_locked, rem = lockout_manager.record_failed_attempt(username, ip)
        assert not is_locked

    # 5th failure must trigger lockout
    is_locked, rem = lockout_manager.record_failed_attempt(username, ip)
    assert is_locked
    assert rem > 800 # 15 minutes lockout

    # Account remains locked out on subsequent query
    is_locked, rem = lockout_manager.is_locked_out(username)
    assert is_locked


def test_cryptographic_audit_hash_chain():
    """Validates SHA-256 blockchain-style cryptographic linkage across audit blocks."""
    # Block 0 (Genesis)
    genesis_prev = "0" * 64
    hash_0 = compute_audit_hash(
        log_id="id-0", user_id="u1", action="INIT",
        details="Genesis", timestamp_iso="2026-09-08T00:00:00Z",
        ip_address="127.0.0.1", previous_hash=genesis_prev
    )

    # Block 1 (Links to Block 0)
    hash_1 = compute_audit_hash(
        log_id="id-1", user_id="u1", action="LOGIN",
        details="User login", timestamp_iso="2026-09-08T00:01:00Z",
        ip_address="127.0.0.1", previous_hash=hash_0
    )

    # Block 2 (Links to Block 1)
    hash_2 = compute_audit_hash(
        log_id="id-2", user_id="u2", action="ASSESS",
        details="Credit score computed", timestamp_iso="2026-09-08T00:02:00Z",
        ip_address="127.0.0.1", previous_hash=hash_1
    )

    assert len(hash_0) == 64
    assert len(hash_1) == 64
    assert len(hash_2) == 64
    assert hash_0 != hash_1 != hash_2

    # Tampering test: if Block 1 details are modified, hash changes and breaks linkage
    tampered_hash_1 = compute_audit_hash(
        log_id="id-1", user_id="u1", action="LOGIN",
        details="TAMPERED DETAILS", timestamp_iso="2026-09-08T00:01:00Z",
        ip_address="127.0.0.1", previous_hash=hash_0
    )
    assert tampered_hash_1 != hash_1
