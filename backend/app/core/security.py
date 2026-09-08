import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, Set
from jose import jwt, JWTError
from passlib.context import CryptContext
from backend.app.core.config import settings

# Setup password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory Token Revocation Blacklist
_token_blacklist: Set[str] = set()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a bcrypt hash for a given password."""
    return pwd_context.hash(password)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a short-lived JWT access token (15 minutes)."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    jti = str(uuid.uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "jti": jti
    }
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a long-lived rotating refresh token (7 days)."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    jti = str(uuid.uuid4())
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": jti
    }
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str, is_refresh: bool = False) -> dict:
    """Decodes and validates token signature, expiration, and revocation status."""
    if is_token_revoked(token):
        raise JWTError("Token has been revoked")

    secret = settings.JWT_REFRESH_SECRET if is_refresh else settings.JWT_SECRET
    payload = jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
    
    expected_type = "refresh" if is_refresh else "access"
    if payload.get("type") != expected_type:
        raise JWTError(f"Invalid token type: expected {expected_type}")
        
    return payload

def revoke_token(token: str):
    """Adds a token's JTI or signature hash to the revocation blacklist."""
    try:
        # Try decoding without verification just to extract JTI
        unverified = jwt.get_unverified_claims(token)
        jti = unverified.get("jti", token)
        _token_blacklist.add(jti)
    except Exception:
        _token_blacklist.add(token)

def is_token_revoked(token: str) -> bool:
    """Checks if a token has been revoked."""
    try:
        unverified = jwt.get_unverified_claims(token)
        jti = unverified.get("jti")
        if jti and jti in _token_blacklist:
            return True
    except Exception:
        pass
    return token in _token_blacklist

# ---------------------------------------------------------------------------
# Cryptographic SHA-256 Audit Trail Hashing (Blockchain-style immutability)
# ---------------------------------------------------------------------------
def compute_audit_hash(
    log_id: str,
    user_id: Optional[str],
    action: str,
    details: str,
    timestamp_iso: str,
    ip_address: Optional[str],
    previous_hash: Optional[str]
) -> str:
    """
    Computes a tamper-evident SHA-256 hash linking this audit record to the preceding block:
    Hash = SHA256(log_id || user_id || action || details || timestamp || ip || previous_hash)
    """
    prev = previous_hash if previous_hash else ("0" * 64)
    u_id = str(user_id) if user_id else "SYSTEM"
    ip = str(ip_address) if ip_address else "127.0.0.1"

    payload = f"{log_id}:{u_id}:{action}:{details}:{timestamp_iso}:{ip}:{prev}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()
