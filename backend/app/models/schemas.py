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

    # Quantitative Risk & Basel III / IFRS 9 attributes
    lgd: Optional[float] = 0.45
    ead: Optional[float] = 0.0
    expected_loss: Optional[float] = 0.0
    regulatory_capital: Optional[float] = 0.0
    rwa: Optional[float] = 0.0
    economic_capital: Optional[float] = 0.0
    ifrs9_stage: Optional[str] = "Stage 1 (Performing)"
    rating_grade: Optional[str] = "BBB"
    recommended_spread_bps: Optional[float] = 0.0
    raroc_pct: Optional[float] = 0.0
    quant_metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

# --- QUANTITATIVE RISK & CAPITAL SCHEMAS ---
class PortfolioSimulationRequest(BaseModel):
    num_simulations: int = Field(50000, ge=1000, le=200000, description="Monte Carlo simulation paths")

class StressTestRequest(BaseModel):
    delta_gdp_pct: float = Field(-2.5, description="GDP shock in percentage points (e.g. -2.5%)")
    delta_unemployment_pct: float = Field(3.0, description="Unemployment rate increase in percentage points (e.g. +3.0%)")
    delta_rate_bps: float = Field(150.0, description="Central bank interest rate shock in basis points (e.g. +150 bps)")
    delta_hpi_pct: float = Field(-12.0, description="House price index shock in percentage points (e.g. -12.0%)")

class LoanPricingRequest(BaseModel):
    amt_credit: float = Field(..., ge=1000)
    pd: float = Field(..., ge=0.0001, le=0.999)
    has_realty: bool = False
    has_car: bool = False
    car_age: Optional[float] = None
    cost_of_funds: float = Field(0.045, ge=0.0, le=0.30)
    opex_rate: float = Field(0.012, ge=0.0, le=0.10)
    target_hurdle_rate: float = Field(0.15, ge=0.05, le=0.50)

class LoanPricingResponse(BaseModel):
    economic_capital: float
    expected_loss: float
    recommended_interest_rate_pct: float
    recommended_spread_bps: float
    target_hurdle_rate_pct: float
    current_market_raroc_pct: float

class QuantPortfolioSummaryResponse(BaseModel):
    total_loans: int
    total_exposure_ead: float
    total_expected_loss: float
    total_rwa: float
    total_regulatory_capital: float
    weighted_avg_pd: float
    weighted_avg_lgd: float
    ifrs9_staging_distribution: Dict[str, int]
    rating_distribution: Dict[str, int]


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
