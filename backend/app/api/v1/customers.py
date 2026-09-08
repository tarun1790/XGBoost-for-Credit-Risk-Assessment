from typing import List, Optional, Union
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from backend.app.core.db import get_db
from backend.app.models.models import Customer, User
from backend.app.models.schemas import CustomerCreate, CustomerResponse
from backend.app.api.v1.auth import get_current_user, require_viewer, require_analyst, require_admin
from backend.app.services.audit_service import audit_service

router = APIRouter()

def mask_email(email: Optional[str]) -> Optional[str]:
    """Masks borrower email for non-privileged roles (e.g. j***@bank.com)."""
    if not email or "@" not in email:
        return email
    user_part, domain = email.split("@", 1)
    if len(user_part) <= 2:
        masked_user = user_part[0] + "***"
    else:
        masked_user = user_part[0] + "***" + user_part[-1]
    return f"{masked_user}@{domain}"

def mask_phone(phone: Optional[str]) -> Optional[str]:
    """Masks borrower telephone number for privacy protection."""
    if not phone or len(phone) < 4:
        return phone
    return f"***-***-{phone[-4:]}"

def sanitize_customer(customer: Customer, is_privileged: bool) -> dict:
    """Applies role-based field-level PII data redaction."""
    d = {c.name: getattr(customer, c.name) for c in customer.__table__.columns}
    if not is_privileged:
        d["email"] = mask_email(customer.email)
        d["phone"] = mask_phone(customer.phone)
    return d


@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """Lists customer application profiles with role-based PII redaction."""
    query = select(Customer)
    
    if search:
        search_filter = f"%{search}%"
        try:
            sk_id_search = int(search)
            query = query.filter(
                or_(
                    Customer.first_name.ilike(search_filter),
                    Customer.last_name.ilike(search_filter),
                    Customer.email.ilike(search_filter),
                    Customer.sk_id_curr == sk_id_search
                )
            )
        except ValueError:
            query = query.filter(
                or_(
                    Customer.first_name.ilike(search_filter),
                    Customer.last_name.ilike(search_filter),
                    Customer.email.ilike(search_filter)
                )
            )
            
    query = query.order_by(Customer.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    customers = result.scalars().all()

    is_privileged = current_user.role in ["ADMIN", "ANALYST"]
    return [sanitize_customer(c, is_privileged) for c in customers]


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """Retrieves single customer profile. Logs PII access audit when viewed unredacted."""
    result = await db.execute(select(Customer).filter(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )

    is_privileged = current_user.role in ["ADMIN", "ANALYST"]
    
    # Audit log access to unmasked sensitive financial PII
    if is_privileged:
        await audit_service.create_log(
            db=db,
            action="PII_DATA_ACCESSED",
            details=f"User {current_user.username} accessed unmasked PII for borrower {customer.first_name} {customer.last_name}.",
            user_id=current_user.id,
            request=request
        )
        await db.commit()

    return sanitize_customer(customer, is_privileged)


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Creates a new customer profile with cryptographic audit trail. Requires Analyst or Admin."""
    result = await db.execute(select(Customer).filter(Customer.sk_id_curr == customer_in.sk_id_curr))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with Application ID (SK_ID_CURR) {customer_in.sk_id_curr} already exists."
        )
        
    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    await db.flush()
    
    # Cryptographically Chained Audit Log
    await audit_service.create_log(
        db=db,
        action="CUSTOMER_CREATED",
        details=f"Created customer profile: {customer.first_name} {customer.last_name} (SK_ID_CURR: {customer.sk_id_curr}).",
        user_id=current_user.id,
        request=request
    )
    await db.commit()
    await db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_in: CustomerCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Updates customer profile with cryptographic audit logging. Requires Analyst or Admin."""
    result = await db.execute(select(Customer).filter(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )
        
    if customer.sk_id_curr != customer_in.sk_id_curr:
        dup_check = await db.execute(select(Customer).filter(Customer.sk_id_curr == customer_in.sk_id_curr))
        if dup_check.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with Application ID (SK_ID_CURR) {customer_in.sk_id_curr} already exists."
            )
            
    for field, value in customer_in.model_dump().items():
        setattr(customer, field, value)
        
    await audit_service.create_log(
        db=db,
        action="CUSTOMER_UPDATED",
        details=f"Updated profile for {customer.first_name} {customer.last_name} (SK_ID_CURR: {customer.sk_id_curr}).",
        user_id=current_user.id,
        request=request
    )
    await db.commit()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Deletes a customer profile with cryptographic audit record. Requires Admin."""
    result = await db.execute(select(Customer).filter(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )
        
    await audit_service.create_log(
        db=db,
        action="CUSTOMER_DELETED",
        details=f"Deleted borrower: {customer.first_name} {customer.last_name} (SK_ID_CURR: {customer.sk_id_curr}).",
        user_id=current_user.id,
        request=request
    )
    await db.delete(customer)
    await db.commit()
    return None
