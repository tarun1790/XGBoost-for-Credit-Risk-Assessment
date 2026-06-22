from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

# --- AUTH SCHEMAS ---
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "VIEWER"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[UUID] = None

# --- CUSTOMER SCHEMAS ---
class CustomerBase(BaseModel):
    sk_id_curr: int = Field(..., description="Unique application ID")
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    
    # Financial fields
    amt_income_total: float = Field(..., ge=0)
    amt_credit: float = Field(..., ge=0)
    amt_annuity: float = Field(..., ge=0)
    
    # Demographics
    days_birth: int = Field(..., description="Age in days (negative value)")
    days_employed: int = Field(..., description="Employment days (negative or 365243)")
    own_car_age: Optional[float] = Field(None, ge=0)
    region_rating_client: int = Field(2, ge=1, le=3)
    
    ext_source_1: Optional[float] = Field(None, ge=0, le=1)
    ext_source_2: Optional[float] = Field(None, ge=0, le=1)
    ext_source_3: Optional[float] = Field(None, ge=0, le=1)
    
    # Categoricals
    name_contract_type: str = "Cash loans"
    code_gender: str = "F"
    flag_own_car: str = "N"
    flag_own_realty: str = "Y"
    cnt_children: int = 0
    name_income_type: str = "Working"
    name_education_type: str = "Secondary / secondary special"
    name_family_status: str = "Married"
    name_housing_type: str = "House / apartment"

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- PREDICTION SCHEMAS ---
class PredictionResponse(BaseModel):
    id: UUID
    customer_id: UUID
    probability_of_default: float
    credit_score: int
    risk_category: str
    shap_explanations: Dict[str, float] # Feature impact mapping
    assessed_by: Optional[UUID] = None
    assessed_at: datetime
    customer: Optional[CustomerResponse] = None
    
    class Config:
        from_attributes = True

# --- DASHBOARD SUMMARY SCHEMAS ---
class RiskDistribution(BaseModel):
    low: int
    medium_low: int
    medium: int
    high: int

class HistoryPoint(BaseModel):
    date: str
    count: int
    avg_score: float

class DashboardSummary(BaseModel):
    total_customers: int
    total_assessments: int
    avg_credit_score: float
    default_rate: float # Percentage
    risk_distribution: RiskDistribution
    history: List[HistoryPoint]

# --- AUDIT LOG SCHEMA ---
class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    username: Optional[str]
    action: str
    details: str
    timestamp: datetime
    
    class Config:
        from_attributes = True
