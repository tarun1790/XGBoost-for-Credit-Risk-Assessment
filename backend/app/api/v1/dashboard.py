from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, Date
from backend.app.core.db import get_db
from backend.app.models.models import Customer, Prediction, User
from backend.app.models.schemas import DashboardSummary, RiskDistribution, HistoryPoint
from backend.app.api.v1.auth import get_current_user, require_viewer

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """
    Computes aggregated performance and risk stats for the main dashboard display.
    """
    # 1. Total Customers Count
    total_cust_res = await db.execute(select(func.count(Customer.id)))
    total_customers = total_cust_res.scalar() or 0
    
    # 2. Total Predictions Count
    total_pred_res = await db.execute(select(func.count(Prediction.id)))
    total_assessments = total_pred_res.scalar() or 0
    
    if total_assessments == 0:
        # Return default mock schema if empty
        return DashboardSummary(
            total_customers=total_customers,
            total_assessments=0,
            avg_credit_score=0.0,
            default_rate=0.0,
            risk_distribution=RiskDistribution(low=0, medium_low=0, medium=0, high=0),
            history=[]
        )
        
    # 3. Average Credit Score
    avg_score_res = await db.execute(select(func.avg(Prediction.credit_score)))
    avg_credit_score = float(avg_score_res.scalar() or 0)
    
    # 4. Default Rate (defined as average probability of default)
    avg_pd_res = await db.execute(select(func.avg(Prediction.probability_of_default)))
    default_rate = float(avg_pd_res.scalar() or 0) * 100.0 # Convert to percentage
    
    # 5. Risk Category Distribution
    # Query count grouped by risk_category
    dist_res = await db.execute(
        select(Prediction.risk_category, func.count(Prediction.id))
        .group_by(Prediction.risk_category)
    )
    dist_data = dict(dist_res.all())
    
    risk_dist = RiskDistribution(
        low=dist_data.get("Low Risk (Excellent)", 0),
        medium_low=dist_data.get("Medium-Low Risk (Good)", 0),
        medium=dist_data.get("Medium Risk (Fair)", 0),
        high=dist_data.get("High Risk (Poor)", 0)
    )
    
    # 6. Timeline History (last 7 assessments group-by-date or recent trend)
    # Group by date of assessment
    history_stmt = (
        select(
            func.cast(Prediction.assessed_at, Date).label("assessment_date"),
            func.count(Prediction.id).label("count"),
            func.avg(Prediction.credit_score).label("avg_score")
        )
        .group_by(func.cast(Prediction.assessed_at, Date))
        .order_by("assessment_date")
        .limit(30) # Last 30 active days
    )
    
    history_res = await db.execute(history_stmt)
    history_points = []
    
    for row in history_res.all():
        history_points.append(
            HistoryPoint(
                date=str(row[0]),
                count=int(row[1]),
                avg_score=float(row[2])
            )
        )
        
    return DashboardSummary(
        total_customers=total_customers,
        total_assessments=total_assessments,
        avg_credit_score=round(avg_credit_score, 1),
        default_rate=round(default_rate, 2),
        risk_distribution=risk_dist,
        history=history_points
    )
