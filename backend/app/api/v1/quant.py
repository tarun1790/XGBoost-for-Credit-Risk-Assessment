from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from backend.app.core.db import get_db
from backend.app.models.models import Customer, Prediction, User, AuditLog
from backend.app.models.schemas import (
    PortfolioSimulationRequest,
    StressTestRequest,
    LoanPricingRequest,
    LoanPricingResponse,
    QuantPortfolioSummaryResponse,
)
from backend.app.services.quant_service import quant_service
from backend.app.api.v1.auth import get_current_user, require_viewer, require_analyst

router = APIRouter()

async def _get_portfolio_data(db: AsyncSession) -> Tuple[List[float], List[float], List[float]]:
    """Helper to extract active portfolio PDs, LGDs, and EADs from the database."""
    # Query latest prediction per customer or all predictions
    stmt = (
        select(Prediction)
        .options(selectinload(Prediction.customer))
        .order_by(Prediction.assessed_at.desc())
    )
    result = await db.execute(stmt)
    predictions = result.scalars().all()

    pds, lgds, eads = [], [], []
    seen_customers = set()

    for p in predictions:
        if p.customer_id in seen_customers:
            continue
        seen_customers.add(p.customer_id)
        
        pd_val = float(p.probability_of_default)
        lgd_val = float(p.lgd if p.lgd is not None else 0.45)
        ead_val = float(p.ead if (p.ead is not None and p.ead > 0) else (p.customer.amt_credit if p.customer else 100000.0))
        
        pds.append(pd_val)
        lgds.append(lgd_val)
        eads.append(ead_val)

    # Fallback to customer table if no predictions yet
    if not pds:
        c_stmt = select(Customer)
        c_res = await db.execute(c_stmt)
        customers = c_res.scalars().all()
        for c in customers:
            amt = float(c.amt_credit or 150000.0)
            # Impute baseline PD from credit ratio and external sources
            ext_avg = ((c.ext_source_1 or 0.5) + (c.ext_source_2 or 0.5) + (c.ext_source_3 or 0.5)) / 3.0
            pd_approx = max(0.005, min(0.40, 0.15 - (ext_avg - 0.5) * 0.2))
            lgd_approx = quant_service.estimate_lgd(c.flag_own_realty == 'Y', c.flag_own_car == 'Y', c.own_car_age)
            ead_approx = quant_service.estimate_ead(amt, c.name_contract_type == "Revolving loans")
            
            pds.append(pd_approx)
            lgds.append(lgd_approx)
            eads.append(ead_approx)

    # If database is completely unpopulated, provide institutional benchmark portfolio
    if not pds:
        pds = [0.002, 0.005, 0.012, 0.025, 0.045, 0.085, 0.140, 0.220]
        lgds = [0.35, 0.40, 0.45, 0.42, 0.48, 0.50, 0.55, 0.60]
        eads = [450000.0, 300000.0, 200000.0, 180000.0, 120000.0, 95000.0, 60000.0, 45000.0]

    return pds, lgds, eads


@router.get("/portfolio-summary", response_model=QuantPortfolioSummaryResponse)
async def get_portfolio_quant_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """
    Computes comprehensive institutional quantitative credit portfolio metrics:
    Total EAD Exposure, Expected Loss, RWA, Basel III Capital, Weighted PD/LGD,
    and IFRS 9 Staging Distribution across all active borrowers.
    """
    pds, lgds, eads = await _get_portfolio_data(db)
    total_loans = len(pds)
    total_ead = float(sum(eads))
    
    # Expected Loss & Basel Capital
    total_el = float(sum(p * l * e for p, l, e in zip(pds, lgds, eads)))
    basel_metrics = [quant_service.compute_basel_capital(p, l, e) for p, l, e in zip(pds, lgds, eads)]
    total_rwa = float(sum(m["rwa"] for m in basel_metrics))
    total_reg_capital = total_rwa * 0.08 # 8% minimum capital requirement

    weighted_pd = float(sum(p * e for p, e in zip(pds, eads)) / max(1.0, total_ead))
    weighted_lgd = float(sum(l * e for l, e in zip(lgds, eads)) / max(1.0, total_ead))

    # IFRS 9 Staging breakdown
    staging_dist = {"Stage 1 (Performing)": 0, "Stage 2 (SICR)": 0, "Stage 3 (Credit Impaired)": 0}
    rating_dist = {"AAA": 0, "AA": 0, "A": 0, "BBB": 0, "BB": 0, "B": 0, "CCC": 0, "D": 0}

    for p, l, e in zip(pds, lgds, eads):
        staging = quant_service.calculate_ifrs9_staging(p, l, e)
        if staging["stage_num"] == 1:
            staging_dist["Stage 1 (Performing)"] += 1
        elif staging["stage_num"] == 2:
            staging_dist["Stage 2 (SICR)"] += 1
        else:
            staging_dist["Stage 3 (Credit Impaired)"] += 1

        grade = quant_service.assign_rating_grade(p, 700)
        rating_dist[grade] = rating_dist.get(grade, 0) + 1

    return QuantPortfolioSummaryResponse(
        total_loans=total_loans,
        total_exposure_ead=round(total_ead, 2),
        total_expected_loss=round(total_el, 2),
        total_rwa=round(total_rwa, 2),
        total_regulatory_capital=round(total_reg_capital, 2),
        weighted_avg_pd=round(weighted_pd, 4),
        weighted_avg_lgd=round(weighted_lgd, 4),
        ifrs9_staging_distribution=staging_dist,
        rating_distribution=rating_dist
    )


@router.post("/portfolio-simulation")
async def run_portfolio_monte_carlo(
    request: PortfolioSimulationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """
    Executes a high-performance, GPU-accelerated Vasicek Copula Monte Carlo simulation
    (up to 200,000 paths) on the active loan portfolio.
    Calculates Credit VaR (95%, 99%, 99.9%), Expected Shortfall (CVaR),
    Unexpected Loss, and simulated loss distribution histogram.
    """
    pds, lgds, eads = await _get_portfolio_data(db)
    
    simulation_result = quant_service.simulate_portfolio_losses(
        portfolio_pds=pds,
        portfolio_lgds=lgds,
        portfolio_eads=eads,
        num_simulations=request.num_simulations
    )
    return simulation_result


@router.post("/stress-test")
async def run_macro_stress_test(
    request: StressTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_viewer)
):
    """
    Macroeconomic Stress-Testing Engine (CCAR/DFAST/EBA alignment).
    Simulates portfolio degradation under user-defined macroeconomic shocks:
    GDP drop, unemployment spike, central bank interest rate shift, and real estate (HPI) declines.
    Returns baseline vs. stressed Expected Losses, RWAs, capital shortfalls, and rating migrations.
    """
    pds, lgds, eads = await _get_portfolio_data(db)

    stress_result = quant_service.run_macro_stress_test(
        portfolio_pds=pds,
        portfolio_lgds=lgds,
        portfolio_eads=eads,
        delta_gdp_pct=request.delta_gdp_pct,
        delta_unemployment_pct=request.delta_unemployment_pct,
        delta_rate_bps=request.delta_rate_bps,
        delta_hpi_pct=request.delta_hpi_pct
    )
    return stress_result


@router.post("/price-loan", response_model=LoanPricingResponse)
async def price_individual_loan(
    request: LoanPricingRequest,
    current_user: User = Depends(require_viewer)
):
    """
    Risk-Adjusted Return on Capital (RAROC) & Loan Pricing Engine.
    Determines hurdle-rate loan interest rate and recommended risk spread (bps)
    given applicant default probability, collateral profile, and bank funding costs.
    """
    lgd = quant_service.estimate_lgd(request.has_realty, request.has_car, request.car_age)
    ead = quant_service.estimate_ead(request.amt_credit)
    basel = quant_service.compute_basel_capital(request.pd, lgd, ead)
    
    pricing = quant_service.calculate_raroc_and_pricing(
        pd=request.pd,
        lgd=lgd,
        ead=ead,
        capital_charge_k=basel["capital_charge_k"],
        cost_of_funds=request.cost_of_funds,
        opex_rate=request.opex_rate,
        target_hurdle_rate=request.target_hurdle_rate
    )
    
    return LoanPricingResponse(
        economic_capital=pricing["economic_capital"],
        expected_loss=pricing["expected_loss"],
        recommended_interest_rate_pct=pricing["recommended_interest_rate_pct"],
        recommended_spread_bps=pricing["recommended_spread_bps"],
        target_hurdle_rate_pct=pricing["target_hurdle_rate_pct"],
        current_market_raroc_pct=pricing["current_market_raroc_pct"]
    )


@router.get("/transition-matrix")
async def get_rating_transition_matrix(
    tenure_years: int = Query(1, ge=1, le=10),
    current_user: User = Depends(require_viewer)
):
    """
    Returns multi-year Markov chain credit rating transition probability matrix
    and cumulative default term structure curves.
    """
    return quant_service.compute_multi_year_transition(years=tenure_years)
