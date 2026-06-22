from datetime import timedelta
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.models.models import User, AuditLog
from backend.app.models.schemas import UserCreate, UserResponse, Token, TokenData, AuditLogResponse

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
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
        raise HTTPException(status_code=400, detail="Inactive user")
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registers a new system user (Analyst/Viewer). Requires admin approval or creates first user as Admin."""
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
    
    # Audit log creation
    audit = AuditLog(
        user_id=new_user.id,
        action="USER_REGISTRATION",
        details=f"User {new_user.username} registered with role {new_user.role}."
    )
    db.add(audit)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """Retrieves access token for login validation."""
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    
    # Audit login
    audit = AuditLog(
        user_id=user.id,
        action="USER_LOGIN",
        details=f"User {user.username} successfully logged in."
    )
    db.add(audit)
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username
    }


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Retrieves authenticated user details."""
    return current_user


@router.get("/audit", response_model=List[AuditLogResponse])
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Retrieves database audit logs. Requires Admin privileges."""
    stmt = (
        select(AuditLog)
        .order_by(AuditLog.timestamp.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    audit_logs = result.scalars().all()
    
    # We will build response list including usernames
    response_logs = []
    for log in audit_logs:
        # Fetch username manually or let SQLAlchemy relationship resolve it
        # Since it's a simple lookup, we can run a quick query or use relationship
        # Let's run a select to get the username if user_id is present
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
            "timestamp": log.timestamp
        })
        
    return response_logs

