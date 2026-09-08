from datetime import timedelta
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
    is_token_revoked
)
from backend.app.core.rate_limiter import (
    rate_limit_login,
    rate_limit_register,
    lockout_manager,
    get_client_ip
)
from backend.app.services.audit_service import audit_service
from backend.app.models.models import User, AuditLog
from backend.app.models.schemas import (
    UserCreate,
    UserResponse,
    Token,
    TokenData,
    RefreshTokenRequest,
    AuditLogResponse,
    AuditVerifyResponse,
    SecurityTelemetryResponse
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been terminated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_token(token, is_refresh=False)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
        
    result = await db.execute(select(User).filter(User.username == token_data.username))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
    return user

# Helper function for RBAC permissions
class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied: Insufficient privileges"
            )
        return current_user

# Common Roles Permissions
require_viewer = RoleChecker(["ADMIN", "ANALYST", "VIEWER"])
require_analyst = RoleChecker(["ADMIN", "ANALYST"])
require_admin = RoleChecker(["ADMIN"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_register)])
async def register(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Registers a new system user with IP rate limiting and cryptographic audit logging."""
    # Check if username or email already exists
    result = await db.execute(
        select(User).filter((User.username == user_in.username) | (User.email == user_in.email))
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
        
    # Check if this is the first user; if so, make them Admin, otherwise default role
    result_any = await db.execute(select(User))
    any_user = result_any.scalars().first()
    
    assigned_role = user_in.role
    if not any_user:
        assigned_role = "ADMIN"
        
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pwd,
        role=assigned_role,
        is_active=True
    )
    
    db.add(new_user)
    await db.flush()
    
    # Cryptographically Chained Audit Log
    await audit_service.create_log(
        db=db,
        action="USER_REGISTRATION",
        details=f"User {new_user.username} registered with role {new_user.role}.",
        user_id=new_user.id,
        request=request
    )
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token, dependencies=[Depends(rate_limit_login)])
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates user, enforces brute-force lockout, issues 15-minute Access Token
    and 7-day rotating Refresh Token with cryptographic audit trail.
    """
    client_ip = get_client_ip(request)
    
    # 1. Check progressive account lockout
    is_locked, remaining_seconds = lockout_manager.is_locked_out(form_data.username)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked due to consecutive failed attempts. Retry in {remaining_seconds} seconds.",
            headers={"Retry-After": str(remaining_seconds)}
        )

    # 2. Query user
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalars().first()
    
    # 3. Verify credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        is_now_locked, lock_duration = lockout_manager.record_failed_attempt(form_data.username, client_ip)
        
        await audit_service.create_log(
            db=db,
            action="AUTH_FAILURE",
            details=f"Failed login attempt for '{form_data.username}'. Lockout triggered: {is_now_locked}.",
            user_id=user.id if user else None,
            request=request
        )
        await db.commit()

        if is_now_locked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Account locked for {lock_duration} seconds.",
                headers={"Retry-After": str(lock_duration)}
            )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")

    # 4. Authentication success: clear lockout counters
    lockout_manager.record_successful_login(form_data.username)

    # 5. Issue short-lived access token (15 mins) and rotating refresh token (7 days)
    access_token = create_access_token(subject=user.username)
    refresh_token = create_refresh_token(subject=user.username)
    
    # 6. Append cryptographic audit record
    await audit_service.create_log(
        db=db,
        action="USER_LOGIN",
        details=f"User {user.username} authenticated successfully.",
        user_id=user.id,
        request=request
    )
    await db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    req: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh Token Rotation (RTR): Validates incoming refresh token, immediately revokes it
    to prevent replay attacks, and issues a brand-new Access Token and Refresh Token pair.
    """
    try:
        payload = decode_token(req.refresh_token, is_refresh=True)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    # Rotate: Revoke the used refresh token immediately
    revoke_token(req.refresh_token)

    # Verify user is still active
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account disabled or deleted")

    # Issue new pair
    new_access_token = create_access_token(subject=user.username)
    new_refresh_token = create_refresh_token(subject=user.username)

    await audit_service.create_log(
        db=db,
        action="TOKEN_ROTATION",
        details=f"Rotated refresh token for user {user.username}.",
        user_id=user.id,
        request=request
    )
    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username,
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Explicitly terminates user session and blacklists the token."""
    revoke_token(token)
    await audit_service.create_log(
        db=db,
        action="USER_LOGOUT",
        details=f"User {current_user.username} logged out and revoked active session.",
        user_id=current_user.id,
        request=request
    )
    await db.commit()
    return {"message": "Session terminated and token revoked successfully"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Retrieves authenticated user details."""
    return current_user


@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Retrieves database audit logs with IP, user-agent, and SHA-256 hash proofs. Requires Admin."""
    stmt = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100)
    result = await db.execute(stmt)
    audit_logs = result.scalars().all()
    
    response_logs = []
    for log in audit_logs:
        username = None
        if log.user_id:
            user_res = await db.execute(select(User).filter(User.id == log.user_id))
            user = user_res.scalars().first()
            if user:
                username = user.username
                
        response_logs.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": username or "System",
            "action": log.action,
            "details": log.details,
            "ip_address": log.ip_address or "127.0.0.1",
            "user_agent": log.user_agent or "INTERNAL",
            "previous_hash": log.previous_hash,
            "record_hash": log.record_hash,
            "timestamp": log.timestamp
        })
        
    return response_logs


@router.get("/audit/verify", response_model=AuditVerifyResponse)
async def verify_audit_trail(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Cryptographic verification endpoint.
    Scans the sequential SHA-256 hash chain across all audit logs from Genesis to Head.
    Proves mathematical immutability and flags any database tampering.
    """
    verification = await audit_service.verify_chain_integrity(db)
    return verification


@router.get("/security-telemetry", response_model=SecurityTelemetryResponse)
async def get_security_telemetry(
    current_user: User = Depends(require_admin)
):
    """Returns real-time security telemetry and protection status for admin monitoring."""
    telemetry = lockout_manager.get_security_telemetry()
    return {
        "active_locked_accounts": telemetry["active_locked_accounts"],
        "accounts_with_failed_attempts": telemetry["accounts_with_failed_attempts"],
        "jwt_access_expiry_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_rotation_enabled": True,
        "audit_blockchain_active": True,
        "rate_limiting_active": True
    }
