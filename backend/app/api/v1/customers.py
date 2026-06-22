from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from backend.app.core.db import get_db
from backend.app.models.models import Customer, User, AuditLog
from backend.app.models.schemas import CustomerCreate, CustomerResponse
from backend.app.api.v1.auth import get_current_user, require_viewer, require_analyst, require_admin

router = APIRouter()

@router.get("/", response_model=List[CustomerResponse])
async def list_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """Lists customer application profiles. Supports searching by name or SK_ID_CURR."""
    query = select(Customer)
    
    if search:
        search_filter = f"%{search}%"
        # Try to parse search query as number for SK_ID_CURR matching
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
    return result.scalars().all()


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """Retrieves details of a specific customer profile by ID."""
    result = await db.execute(select(Customer).filter(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )
    return customer


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Creates a new customer profile. Requires Analyst or Admin role."""
    # Check if sk_id_curr already exists
    result = await db.execute(select(Customer).filter(Customer.sk_id_curr == customer_in.sk_id_curr))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with Application ID (SK_ID_CURR) {customer_in.sk_id_curr} already exists."
        )
        
    customer = Customer(**customer_in.model_dump())
    db.add(customer)
    await db.flush()
    
    # Audit log creation
    audit = AuditLog(
        user_id=current_user.id,
        action="CUSTOMER_CREATED",
        details=f"Created customer profile for {customer.first_name} {customer.last_name} (SK_ID_CURR: {customer.sk_id_curr})."
    )
    db.add(audit)
    await db.commit()
    await db.refresh(customer)
    
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    customer_in: CustomerCreate, # Reuse creation model for complete updates
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """Updates an existing customer profile. Requires Analyst or Admin role."""
    result = await db.execute(select(Customer).filter(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )
        
    # Verify SK_ID_CURR uniqueness if it is being changed
    if customer.sk_id_curr != customer_in.sk_id_curr:
        dup_check = await db.execute(select(Customer).filter(Customer.sk_id_curr == customer_in.sk_id_curr))
        if dup_check.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with Application ID (SK_ID_CURR) {customer_in.sk_id_curr} already exists."
            )
            
    # Update fields
    for field, value in customer_in.model_dump().items():
        setattr(customer, field, value)
        
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="CUSTOMER_UPDATED",
        details=f"Updated customer profile for {customer.first_name} {customer.last_name} (SK_ID_CURR: {customer.sk_id_curr})."
    )
    db.add(audit)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Deletes a customer profile. Requires Admin role."""
    result = await db.execute(select(Customer).filter(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found"
        )
        
    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="CUSTOMER_DELETED",
        details=f"Deleted customer profile: {customer.first_name} {customer.last_name} (SK_ID_CURR: {customer.sk_id_curr})."
    )
    db.add(audit)
    await db.delete(customer)
    await db.commit()
    return None
