from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.app.core.db import get_db
from backend.app.models.models import Customer, Prediction, User, AuditLog
from backend.app.models.schemas import PredictionResponse
from backend.app.services.ml_service import ml_service
from backend.app.api.v1.auth import get_current_user, require_viewer, require_analyst

router = APIRouter()

@router.post("/{customer_id}", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED)
async def assess_credit_risk(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst)
):
    """
    Triggers credit risk assessment for an existing customer in the database.
    Calculates Probability of Default (PD), Credit Score, Risk Category, and SHAP values.
    Saves the assessment prediction and logs the transaction.
    """
    # 1. Fetch customer from database
    result = await db.execute(select(Customer).filter(Customer.id == customer_id))
    customer = result.scalars().first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found in database. Please register the customer first."
        )
        
    # 2. Extract features to dictionary
    raw_data = {
        "NAME_CONTRACT_TYPE": customer.name_contract_type,
        "CODE_GENDER": customer.code_gender,
        "FLAG_OWN_CAR": customer.flag_own_car,
        "FLAG_OWN_REALTY": customer.flag_own_realty,
        "CNT_CHILDREN": customer.cnt_children,
        "AMT_INCOME_TOTAL": customer.amt_income_total,
        "AMT_CREDIT": customer.amt_credit,
        "AMT_ANNUITY": customer.amt_annuity,
        "AMT_GOODS_PRICE": customer.amt_credit * 0.95, # Estimate goods price if not tracked
        "NAME_INCOME_TYPE": customer.name_income_type,
        "NAME_EDUCATION_TYPE": customer.name_education_type,
        "NAME_FAMILY_STATUS": customer.name_family_status,
        "NAME_HOUSING_TYPE": customer.name_housing_type,
        "DAYS_BIRTH": customer.days_birth,
        "DAYS_EMPLOYED": customer.days_employed,
        "OWN_CAR_AGE": customer.own_car_age if customer.own_car_age is not None else 0.0,
        "REGION_RATING_CLIENT": customer.region_rating_client,
        "EXT_SOURCE_1": customer.ext_source_1,
        "EXT_SOURCE_2": customer.ext_source_2,
        "EXT_SOURCE_3": customer.ext_source_3
    }
    
    # 3. Call ML Inference Service
    try:
        prediction_results = ml_service.predict(raw_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Machine learning model prediction failure: {str(e)}"
        )
        
    # 4. Save assessment prediction record
    prediction = Prediction(
        customer_id=customer.id,
        probability_of_default=prediction_results["probability_of_default"],
        credit_score=prediction_results["credit_score"],
        risk_category=prediction_results["risk_category"],
        shap_explanations=prediction_results["shap_explanations"],
        assessed_by=current_user.id
    )
    
    db.add(prediction)
    await db.flush()
    
    # 5. Log audit transaction
    audit = AuditLog(
        user_id=current_user.id,
        action="CREDIT_ASSESSMENT",
        details=f"Assessed credit risk for {customer.first_name} {customer.last_name}. "
                f"Score: {prediction.credit_score} ({prediction.risk_category})."
    )
    db.add(audit)
    await db.commit()
    
    # Load relationships for response schema serialization
    stmt = (
        select(Prediction)
        .options(selectinload(Prediction.customer))
        .filter(Prediction.id == prediction.id)
    )
    res = await db.execute(stmt)
    full_prediction = res.scalars().first()
    
    return full_prediction


@router.get("/history", response_model=List[PredictionResponse])
async def list_assessment_history(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """Lists past credit risk assessments sorted by assessment timestamp."""
    stmt = (
        select(Prediction)
        .options(selectinload(Prediction.customer))
        .order_by(Prediction.assessed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/history/{prediction_id}", response_model=PredictionResponse)
async def get_assessment_details(
    prediction_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """Retrieves standard details and SHAP analysis for a single historical prediction."""
    stmt = (
        select(Prediction)
        .options(selectinload(Prediction.customer))
        .filter(Prediction.id == prediction_id)
    )
    result = await db.execute(stmt)
    prediction = result.scalars().first()
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction record not found"
        )
    return prediction
