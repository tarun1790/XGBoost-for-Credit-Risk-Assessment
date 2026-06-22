import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Float, Integer, DateTime, ForeignKey, text, UUID, JSON
from sqlalchemy.orm import relationship
from backend.app.core.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="VIEWER", nullable=False) # ADMIN, ANALYST, VIEWER
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="assessor")
    audit_logs = relationship("AuditLog", back_populates="user")

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sk_id_curr = Column(Integer, unique=True, index=True, nullable=False) # Home Credit application ID
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)
    
    # Numerical features matching Home Credit dataset
    amt_income_total = Column(Float, nullable=False)
    amt_credit = Column(Float, nullable=False)
    amt_annuity = Column(Float, nullable=False)
    days_birth = Column(Integer, nullable=False)
    days_employed = Column(Integer, nullable=False)
    own_car_age = Column(Float, nullable=True)
    region_rating_client = Column(Integer, nullable=False, default=2)
    ext_source_1 = Column(Float, nullable=True)
    ext_source_2 = Column(Float, nullable=True)
    ext_source_3 = Column(Float, nullable=True)
    
    # Categorical features matching Home Credit dataset
    name_contract_type = Column(String, nullable=False, default="Cash loans")
    code_gender = Column(String, nullable=False, default="F")
    flag_own_car = Column(String, nullable=False, default="N")
    flag_own_realty = Column(String, nullable=False, default="Y")
    cnt_children = Column(Integer, nullable=False, default=0)
    name_income_type = Column(String, nullable=False, default="Working")
    name_education_type = Column(String, nullable=False, default="Secondary / secondary special")
    name_family_status = Column(String, nullable=False, default="Married")
    name_housing_type = Column(String, nullable=False, default="House / apartment")
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    predictions = relationship("Prediction", back_populates="customer", cascade="all, delete-orphan")

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    probability_of_default = Column(Float, nullable=False)
    credit_score = Column(Integer, nullable=False)
    risk_category = Column(String, nullable=False)
    shap_explanations = Column(JSON, nullable=False) # Stores feature contribution scores
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assessed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    customer = relationship("Customer", back_populates="predictions")
    assessor = relationship("User", back_populates="predictions")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    action = Column(String, nullable=False)
    details = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
