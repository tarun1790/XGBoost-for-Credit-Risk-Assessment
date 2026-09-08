import pytest
import numpy as np
from backend.app.services.quant_service import quant_service

def test_basel_capital_calculation():
    """Validates Basel III IRB formula for regulatory capital (K), RWA, and Expected Loss."""
    pd = 0.02
    lgd = 0.45
    ead = 200000.0

    res = quant_service.compute_basel_capital(pd, lgd, ead, maturity_years=2.5)

    assert "asset_correlation" in res
    assert "capital_charge_k" in res
    assert "rwa" in res
    assert "expected_loss" in res
    assert "unexpected_loss" in res
    assert "min_regulatory_capital" in res

    # Mathematical consistency checks
    assert 0.03 <= res["asset_correlation"] <= 0.24
    assert res["expected_loss"] == pytest.approx(pd * lgd * ead, rel=1e-2)
    assert res["rwa"] == pytest.approx(res["capital_charge_k"] * 12.5 * ead, rel=1e-2)
    assert res["min_regulatory_capital"] == pytest.approx(res["rwa"] * 0.08, rel=1e-2)
    assert res["capital_charge_k"] > 0.0


def test_ifrs9_staging_and_scenario_ecl():
    """Validates IFRS 9 3-stage classification and multi-scenario weighted ECL."""
    # Low risk -> Stage 1
    s1 = quant_service.calculate_ifrs9_staging(pd=0.01, lgd=0.40, ead=100000.0)
    assert s1["stage_num"] == 1
    assert "Stage 1" in s1["stage"]

    # Medium risk -> Stage 2 (SICR)
    s2 = quant_service.calculate_ifrs9_staging(pd=0.08, lgd=0.45, ead=100000.0)
    assert s2["stage_num"] == 2
    assert "Stage 2" in s2["stage"]
    assert s2["lifetime_pd"] > s2["annual_pd"]

    # Impaired risk -> Stage 3
    s3 = quant_service.calculate_ifrs9_staging(pd=0.25, lgd=0.50, ead=100000.0)
    assert s3["stage_num"] == 3
    assert "Stage 3" in s3["stage"]

    # Multi-scenario monotonicity: ECL_bull < ECL_base < ECL_bear
    assert s2["scenarios"]["bull"]["ecl"] < s2["scenarios"]["base"]["ecl"] < s2["scenarios"]["bear"]["ecl"]


def test_copula_monte_carlo_portfolio_simulation():
    """Validates GPU/CUDA Vasicek Copula simulation properties and tail risk metrics."""
    pds = [0.01, 0.02, 0.04, 0.08, 0.12]
    lgds = [0.40, 0.45, 0.42, 0.48, 0.50]
    eads = [150000.0, 200000.0, 80000.0, 50000.0, 30000.0]

    sim = quant_service.simulate_portfolio_losses(pds, lgds, eads, num_simulations=20000)

    assert sim["num_simulations"] == 20000
    assert sim["portfolio_size"] == 5
    assert sim["total_exposure"] == pytest.approx(sum(eads), rel=1e-3)
    assert "device_used" in sim

    # Tail risk ordering: Mean Loss <= VaR 95 <= VaR 99 <= VaR 99.9 <= Expected Shortfall 99.9
    assert sim["expected_loss"] <= sim["var_95"]
    assert sim["var_95"] <= sim["var_99"]
    assert sim["var_99"] <= sim["var_999"]
    assert sim["var_999"] <= sim["expected_shortfall_999"]

    # Histogram generated
    assert len(sim["histogram"]) > 0


def test_macro_stress_testing_transmission():
    """Validates macroeconomic stress-testing factor transmission."""
    pds = [0.015, 0.035, 0.070]
    lgds = [0.40, 0.45, 0.50]
    eads = [100000.0, 200000.0, 150000.0]

    # Adverse shock: GDP -3%, Unemp +4%, Rates +200bps, HPI -15%
    stress = quant_service.run_macro_stress_test(
        portfolio_pds=pds, portfolio_lgds=lgds, portfolio_eads=eads,
        delta_gdp_pct=-3.0, delta_unemployment_pct=4.0, delta_rate_bps=200.0, delta_hpi_pct=-15.0
    )

    # Adverse shocks must increase expected loss and RWA
    assert stress["stressed"]["expected_loss"] > stress["baseline"]["expected_loss"]
    assert stress["stressed"]["rwa"] > stress["baseline"]["rwa"]
    assert stress["impact"]["el_increase"] > 0
    assert stress["impact"]["capital_deficit"] > 0


def test_raroc_and_hurdle_loan_pricing():
    """Validates RAROC and breakeven credit spread solver."""
    pricing = quant_service.calculate_raroc_and_pricing(
        pd=0.03, lgd=0.45, ead=100000.0, capital_charge_k=0.08,
        cost_of_funds=0.045, opex_rate=0.012, target_hurdle_rate=0.15
    )

    assert pricing["recommended_interest_rate_pct"] > 4.5 # Must exceed funding cost
    assert pricing["recommended_spread_bps"] > 0
    assert pricing["economic_capital"] > 0


def test_markov_rating_transitions():
    """Validates Markov chain credit rating transition matrices."""
    m3 = quant_service.compute_multi_year_transition(years=3)
    matrix = m3["transition_matrix"]
    
    # Rows should sum to approximately 1.0
    for grade, row in matrix.items():
        row_sum = sum(row.values())
        assert row_sum == pytest.approx(1.0, abs=0.01)

    # Cumulative default probability is highest for lowest rating grade
    assert m3["cumulative_default_probabilities"]["AAA"] < m3["cumulative_default_probabilities"]["BBB"]
    assert m3["cumulative_default_probabilities"]["BBB"] < m3["cumulative_default_probabilities"]["CCC"]
