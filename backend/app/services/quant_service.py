import math
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import scipy.stats as stats
import torch

class QuantRiskEngine:
    """
    Institutional Quantitative Credit Risk & Capital Analytics Engine.
    Implements Basel III ASRF IRB framework, IFRS 9/CECL multi-horizon ECL,
    GPU-accelerated Vasicek Copula Monte Carlo portfolio simulation,
    CCAR/DFAST macroeconomic stress-testing, and RAROC loan pricing.
    """

    def __init__(self):
        # Configure GPU/CUDA acceleration for Monte Carlo simulations
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Rating scale thresholds (Standard & Poor's / Moody's alignment)
        self.rating_scale = [
            {"grade": "AAA", "max_pd": 0.0005, "min_score": 810},
            {"grade": "AA",  "max_pd": 0.0020, "min_score": 770},
            {"grade": "A",   "max_pd": 0.0060, "min_score": 730},
            {"grade": "BBB", "max_pd": 0.0200, "min_score": 680},
            {"grade": "BB",  "max_pd": 0.0550, "min_score": 630},
            {"grade": "B",   "max_pd": 0.1400, "min_score": 570},
            {"grade": "CCC", "max_pd": 0.3500, "min_score": 450},
            {"grade": "D",   "max_pd": 1.0000, "min_score": 300},
        ]

        # 1-Year Baseline Transition Matrix (Standard corporate/retail credit migration)
        # Rows: Current Rating [AAA, AA, A, BBB, BB, B, CCC, D]
        # Columns: Next Year Rating [AAA, AA, A, BBB, BB, B, CCC, D]
        self.base_transition_matrix = np.array([
            [0.9081, 0.0833, 0.0068, 0.0009, 0.0006, 0.0002, 0.0001, 0.0000], # AAA
            [0.0070, 0.9065, 0.0779, 0.0064, 0.0006, 0.0011, 0.0003, 0.0002], # AA
            [0.0009, 0.0227, 0.9105, 0.0552, 0.0074, 0.0026, 0.0003, 0.0004], # A
            [0.0002, 0.0033, 0.0595, 0.8693, 0.0530, 0.0117, 0.0012, 0.0018], # BBB
            [0.0003, 0.0014, 0.0067, 0.0773, 0.8053, 0.0884, 0.0101, 0.0105], # BB
            [0.0000, 0.0011, 0.0024, 0.0043, 0.0648, 0.8346, 0.0388, 0.0540], # B
            [0.0000, 0.0000, 0.0022, 0.0130, 0.0238, 0.1124, 0.6486, 0.2000], # CCC
            [0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 0.0000, 1.0000], # D (Absorbing)
        ])

    # -----------------------------------------------------------------------
    # 1. Rating Grade Classification
    # -----------------------------------------------------------------------
    def assign_rating_grade(self, pd: float, credit_score: int) -> str:
        """Assigns institutional credit rating grade based on calibrated PD and score."""
        for tier in self.rating_scale:
            if pd <= tier["max_pd"] or credit_score >= tier["min_score"]:
                return tier["grade"]
        return "D"

    # -----------------------------------------------------------------------
    # 2. Basel III IRB Asset Correlation & Capital Requirement (K)
    # -----------------------------------------------------------------------
    def compute_basel_correlation(self, pd: float, is_revolving: bool = False) -> float:
        """
        Computes asset correlation rho per Basel III IRB formula:
        For Retail: rho = 0.03 * (1 - e^-35*PD)/(1 - e^-35) + 0.16 * [1 - (1 - e^-35*PD)/(1 - e^-35)]
        For Corporate/SME: rho = 0.12 * (1 - e^-50*PD)/(1 - e^-50) + 0.24 * [1 - (1 - e^-50*PD)/(1 - e^-50)]
        """
        pd_capped = np.clip(pd, 0.0001, 0.9999)
        if is_revolving:
            # Qualifying Revolving Retail Exposure (QRRE): fixed 0.04
            return 0.04
        # Standard Retail / Unsecured credit formula
        factor = (1.0 - math.exp(-35.0 * pd_capped)) / (1.0 - math.exp(-35.0))
        rho = 0.03 * factor + 0.16 * (1.0 - factor)
        return float(rho)

    def compute_basel_capital(self, pd: float, lgd: float, ead: float, maturity_years: float = 2.5, is_revolving: bool = False) -> Dict[str, float]:
        """
        Calculates Basel III Pillar 1 Regulatory Capital Requirement (K),
        Risk-Weighted Assets (RWA), Expected Loss (EL), and Unexpected Loss (UL).
        """
        pd_c = np.clip(pd, 0.0003, 0.9999) # Basel floor of 3 bps
        lgd_c = np.clip(lgd, 0.05, 1.0)
        rho = self.compute_basel_correlation(pd_c, is_revolving)

        # 99.9% Vasicek single risk factor conditional default rate:
        # PD_cond = N( (N^-1(PD) + sqrt(rho)*N^-1(0.999)) / sqrt(1 - rho) )
        norm_inv_pd = stats.norm.ppf(pd_c)
        norm_inv_999 = stats.norm.ppf(0.999) # 3.0902
        conditional_pd = stats.norm.cdf((norm_inv_pd + math.sqrt(rho) * norm_inv_999) / math.sqrt(1.0 - rho))

        # Maturity adjustment factor b(PD)
        b = (0.11852 - 0.05478 * math.log(pd_c)) ** 2
        maturity_adj = (1.0 + (maturity_years - 2.5) * b) / (1.0 - 1.5 * b)

        # Capital charge per dollar of exposure K
        k = max(0.0, (lgd_c * conditional_pd - pd_c * lgd_c) * maturity_adj)
        
        # Risk-Weighted Assets (RWA = K * 12.5 * EAD)
        rwa = k * 12.5 * ead
        
        # Expected Loss (EL)
        el = pd_c * lgd_c * ead
        
        # Unexpected Loss (UL = K * EAD at 99.9% confidence)
        ul = k * ead
        
        # Minimum Tier 1 Capital requirement (8.0% of RWA)
        min_tier1_capital = rwa * 0.08

        return {
            "asset_correlation": round(float(rho), 4),
            "conditional_pd_999": round(float(conditional_pd), 4),
            "capital_charge_k": round(float(k), 4),
            "rwa": round(float(rwa), 2),
            "expected_loss": round(float(el), 2),
            "unexpected_loss": round(float(ul), 2),
            "min_regulatory_capital": round(float(min_tier1_capital), 2),
        }

    # -----------------------------------------------------------------------
    # 3. LGD & EAD Engineering
    # -----------------------------------------------------------------------
    def estimate_lgd(self, has_realty: bool, has_car: bool, car_age: Optional[float] = None) -> float:
        """
        Estimates Loss Given Default (LGD) with asset haircuts.
        Unsecured Baseline = 45.0%
        Realty Collateral = -10.0% reduction
        Vehicle Collateral = -5.0% reduction (adjusted for vehicle age)
        """
        lgd = 0.45 # 45% standard unsecured baseline
        if has_realty:
            lgd -= 0.10
        if has_car:
            car_discount = 0.05
            if car_age is not None and car_age > 10.0:
                car_discount = 0.02 # depreciated collateral value
            lgd -= car_discount
        return max(0.15, min(0.85, lgd))

    def estimate_ead(self, amt_credit: float, is_revolving: bool = False, credit_limit: Optional[float] = None) -> float:
        """
        Estimates Exposure at Default (EAD).
        Term loan: 100% of drawn balance.
        Revolving line: Drawn + CCF * Undrawn (CCF = 50% Basel standard).
        """
        if not is_revolving or credit_limit is None or credit_limit <= amt_credit:
            return float(amt_credit)
        undrawn = max(0.0, credit_limit - amt_credit)
        ccf = 0.50 # Credit Conversion Factor
        return float(amt_credit + ccf * undrawn)

    # -----------------------------------------------------------------------
    # 4. IFRS 9 / CECL Multi-Horizon Staging & Loss Provisioning
    # -----------------------------------------------------------------------
    def calculate_ifrs9_staging(self, pd: float, lgd: float, ead: float, tenure_years: float = 3.0) -> Dict[str, Any]:
        """
        IFRS 9 Expected Credit Loss (ECL) calculation across 3 stages:
        - Stage 1: Performing -> 12-Month ECL
        - Stage 2: Underperforming / SICR -> Lifetime ECL
        - Stage 3: Credit Impaired -> Lifetime ECL (Defaulted state)
        Computes multi-scenario probability-weighted ECL:
          Base (50%), Bull (20%), Bear (30%)
        """
        # Staging criteria
        if pd >= 0.20:
            stage = "Stage 3 (Credit-Impaired)"
            stage_num = 3
            lifetime_pd = min(1.0, pd * 1.5)
        elif pd >= 0.035: # SICR threshold
            stage = "Stage 2 (Underperforming - SICR)"
            stage_num = 2
            # Cumulative lifetime PD derived from Poisson / hazard rate
            hazard_rate = -math.log(max(1e-5, 1.0 - pd))
            lifetime_pd = 1.0 - math.exp(-hazard_rate * tenure_years)
        else:
            stage = "Stage 1 (Performing)"
            stage_num = 1
            lifetime_pd = pd # 12-month PD used for Stage 1

        effective_pd = pd if stage_num == 1 else lifetime_pd
        
        # Scenario macroeconomic shifts
        pd_base = effective_pd
        pd_bull = effective_pd * 0.75 # Expansionary scenario
        pd_bear = min(0.99, effective_pd * 1.45) # Recessionary scenario

        lgd_base = lgd
        lgd_bull = max(0.10, lgd * 0.90)
        lgd_bear = min(0.95, lgd * 1.25) # Downturn LGD

        ecl_base = pd_base * lgd_base * ead
        ecl_bull = pd_bull * lgd_bull * ead
        ecl_bear = pd_bear * lgd_bear * ead

        # Probability-weighted ECL (Base 50%, Bull 20%, Bear 30%)
        weighted_ecl = 0.50 * ecl_base + 0.20 * ecl_bull + 0.30 * ecl_bear

        return {
            "stage": stage,
            "stage_num": stage_num,
            "annual_pd": round(float(pd), 4),
            "lifetime_pd": round(float(lifetime_pd), 4),
            "weighted_ecl": round(float(weighted_ecl), 2),
            "scenarios": {
                "base": {"pd": round(float(pd_base), 4), "lgd": round(float(lgd_base), 4), "ecl": round(float(ecl_base), 2), "weight": 0.50},
                "bull": {"pd": round(float(pd_bull), 4), "lgd": round(float(lgd_bull), 4), "ecl": round(float(ecl_bull), 2), "weight": 0.20},
                "bear": {"pd": round(float(pd_bear), 4), "lgd": round(float(lgd_bear), 4), "ecl": round(float(ecl_bear), 2), "weight": 0.30}
            }
        }

    # -----------------------------------------------------------------------
    # 5. Risk-Adjusted Return on Capital (RAROC) & Loan Pricing
    # -----------------------------------------------------------------------
    def calculate_raroc_and_pricing(self, pd: float, lgd: float, ead: float, capital_charge_k: float,
                                    cost_of_funds: float = 0.045, opex_rate: float = 0.012,
                                    target_hurdle_rate: float = 0.15) -> Dict[str, Any]:
        """
        Solves for risk-adjusted pricing and computes RAROC:
        RAROC = (Interest Income + Fees - Cost of Funds - Operating Costs - EL) / Economic Capital
        Optimal Spread = Cost of Funds + Opex + (EL / EAD) + (Target Hurdle * Economic Capital / EAD)
        """
        economic_capital = max(100.0, capital_charge_k * ead)
        expected_loss = pd * lgd * ead

        # Hurdle Rate Breakeven Interest Rate
        required_capital_return = target_hurdle_rate * economic_capital
        total_required_income = (cost_of_funds * ead) + (opex_rate * ead) + expected_loss + required_capital_return
        recommended_interest_rate = total_required_income / max(1.0, ead)
        recommended_spread_bps = max(0.0, (recommended_interest_rate - cost_of_funds) * 10000.0)

        # If evaluating a standard retail rate of e.g. 9.5%:
        standard_market_rate = 0.095
        actual_net_revenue = (standard_market_rate - cost_of_funds - opex_rate) * ead - expected_loss
        raroc = actual_net_revenue / economic_capital

        return {
            "economic_capital": round(float(economic_capital), 2),
            "expected_loss": round(float(expected_loss), 2),
            "recommended_interest_rate_pct": round(float(recommended_interest_rate * 100.0), 2),
            "recommended_spread_bps": round(float(recommended_spread_bps), 0),
            "target_hurdle_rate_pct": round(float(target_hurdle_rate * 100.0), 1),
            "current_market_raroc_pct": round(float(raroc * 100.0), 2),
        }

    # -----------------------------------------------------------------------
    # 6. GPU-Accelerated Vasicek / Copula Monte Carlo Portfolio Simulation
    # -----------------------------------------------------------------------
    def simulate_portfolio_losses(self, portfolio_pds: List[float], portfolio_lgds: List[float], portfolio_eads: List[float],
                                  num_simulations: int = 50000) -> Dict[str, Any]:
        """
        Vectorized Monte Carlo Vasicek Copula Simulation modeling correlated defaults across
        the entire portfolio. Runs with PyTorch on CUDA GPU if available for extreme speed.
        """
        M = len(portfolio_pds)
        if M == 0:
            return {"status": "empty_portfolio"}

        # Prepare tensors / arrays
        pds_t = np.clip(np.array(portfolio_pds, dtype=np.float32), 0.0001, 0.9999)
        lgds_t = np.clip(np.array(portfolio_lgds, dtype=np.float32), 0.05, 1.0)
        eads_t = np.array(portfolio_eads, dtype=np.float32)

        # Asset correlations rho for each borrower
        rhos = np.array([self.compute_basel_correlation(float(p)) for p in pds_t], dtype=np.float32)
        sqrt_rho = np.sqrt(rhos)
        sqrt_1_minus_rho = np.sqrt(1.0 - rhos)
        thresholds = stats.norm.ppf(pds_t) # Individual default thresholds

        total_exposure = float(np.sum(eads_t))

        # Check GPU availability and execute
        use_cuda = self.device.type == 'cuda'
        
        if use_cuda:
            try:
                # Transfer to GPU device
                t_sqrt_rho = torch.tensor(sqrt_rho, device=self.device).view(1, M)
                t_sqrt_1_rho = torch.tensor(sqrt_1_minus_rho, device=self.device).view(1, M)
                t_thresholds = torch.tensor(thresholds, device=self.device).view(1, M)
                t_lgd_ead = torch.tensor(lgds_t * eads_t, device=self.device).view(1, M)

                # Batch simulation on GPU
                # Systemic factor Z shape: (num_simulations, 1)
                Z = torch.randn(num_simulations, 1, device=self.device)
                # Idiosyncratic shocks epsilon shape: (num_simulations, M)
                eps = torch.randn(num_simulations, M, device=self.device)

                # Latent asset return: R = sqrt(rho)*Z + sqrt(1-rho)*eps
                R = t_sqrt_rho * Z + t_sqrt_1_rho * eps

                # Default indicator: 1 if R < threshold else 0
                defaults = (R < t_thresholds).float()

                # Portfolio loss per simulation path: sum(defaults * LGD * EAD)
                sim_losses = (defaults * t_lgd_ead).sum(dim=1)

                losses_cpu = sim_losses.cpu().numpy()
            except Exception as e:
                # Graceful CPU fallback if memory issue
                use_cuda = False
        
        if not use_cuda:
            # High-performance vectorized NumPy execution
            Z = np.random.randn(num_simulations, 1).astype(np.float32)
            eps = np.random.randn(num_simulations, M).astype(np.float32)
            R = sqrt_rho * Z + sqrt_1_minus_rho * eps
            defaults = (R < thresholds).astype(np.float32)
            losses_cpu = np.sum(defaults * (lgds_t * eads_t), axis=1)

        # Sort simulated losses to extract tail risk metrics
        losses_sorted = np.sort(losses_cpu)
        mean_loss = float(np.mean(losses_sorted))
        std_loss = float(np.std(losses_sorted))

        # Value at Risk (VaR)
        var_95 = float(np.percentile(losses_sorted, 95.0))
        var_99 = float(np.percentile(losses_sorted, 99.0))
        var_999 = float(np.percentile(losses_sorted, 99.9))

        # Expected Shortfall (CVaR) at 99.0% and 99.9%
        idx_99 = int(0.99 * num_simulations)
        idx_999 = int(0.999 * num_simulations)
        es_99 = float(np.mean(losses_sorted[idx_99:]))
        es_999 = float(np.mean(losses_sorted[idx_999:]))

        # Unexpected Loss (UL = VaR_99.9 - Expected Loss)
        ul = max(0.0, var_999 - mean_loss)

        # Generate Histogram bins for frontend rendering (30 buckets)
        counts, bin_edges = np.histogram(losses_sorted, bins=30)
        histogram_data = []
        for i in range(len(counts)):
            histogram_data.append({
                "bin_start": round(float(bin_edges[i]), 2),
                "bin_end": round(float(bin_edges[i+1]), 2),
                "count": int(counts[i]),
                "frequency_pct": round(float(counts[i] / num_simulations * 100.0), 2)
            })

        return {
            "device_used": "GPU (NVIDIA CUDA)" if use_cuda else "CPU (Vectorized NumPy)",
            "num_simulations": num_simulations,
            "portfolio_size": M,
            "total_exposure": round(total_exposure, 2),
            "expected_loss": round(mean_loss, 2),
            "loss_volatility": round(std_loss, 2),
            "var_95": round(var_95, 2),
            "var_99": round(var_99, 2),
            "var_999": round(var_999, 2),
            "expected_shortfall_99": round(es_99, 2),
            "expected_shortfall_999": round(es_999, 2),
            "unexpected_loss": round(ul, 2),
            "var_999_pct_of_exposure": round((var_999 / max(1.0, total_exposure)) * 100.0, 2),
            "histogram": histogram_data
        }

    # -----------------------------------------------------------------------
    # 7. CCAR / DFAST Macroeconomic Stress-Testing Engine
    # -----------------------------------------------------------------------
    def run_macro_stress_test(self, portfolio_pds: List[float], portfolio_lgds: List[float], portfolio_eads: List[float],
                              delta_gdp_pct: float, delta_unemployment_pct: float,
                              delta_rate_bps: float, delta_hpi_pct: float) -> Dict[str, Any]:
        """
        Macroeconomic Factor Transmission Model:
        Simulates how exogenous macroeconomic shocks (GDP, Unemployment, Rates, HPI)
        shift conditional default probabilities, increase downturn LGDs, elevate Expected Losses,
        and cause regulatory capital deficit/surplus.
        """
        M = len(portfolio_pds)
        if M == 0:
            return {"status": "empty_portfolio"}

        # Macroeconomic satellite index:
        # Contractionary factors increase systematic shock Z_macro
        z_gdp = -0.45 * (delta_gdp_pct / 2.0)
        z_unemp = 0.55 * (delta_unemployment_pct / 3.0)
        z_rate = 0.30 * (delta_rate_bps / 200.0)
        z_hpi = -0.35 * (delta_hpi_pct / 10.0)
        z_macro = float(z_gdp + z_unemp + z_rate + z_hpi)

        # Baseline metrics
        base_el = sum(p * l * e for p, l, e in zip(portfolio_pds, portfolio_lgds, portfolio_eads))
        base_k_metrics = [self.compute_basel_capital(p, l, e) for p, l, e in zip(portfolio_pds, portfolio_lgds, portfolio_eads)]
        base_rwa = sum(m["rwa"] for m in base_k_metrics)
        base_capital_req = base_rwa * 0.08

        # Stressed metrics calculation
        stressed_pds = []
        stressed_lgds = []
        for p, l in zip(portfolio_pds, portfolio_lgds):
            rho = self.compute_basel_correlation(p)
            norm_inv_p = stats.norm.ppf(np.clip(p, 0.0001, 0.9999))
            # Conditional shifted PD under macro shock
            shifted_norm = (norm_inv_p + z_macro * math.sqrt(rho)) / math.sqrt(1.0 - rho * 0.25)
            s_p = float(np.clip(stats.norm.cdf(shifted_norm), 0.0001, 0.9999))
            stressed_pds.append(s_p)

            # Stressed LGD increases if real estate / HPI falls
            lgd_multiplier = 1.0 + max(0.0, -delta_hpi_pct * 0.015) + max(0.0, delta_unemployment_pct * 0.03)
            s_l = float(np.clip(l * lgd_multiplier, 0.10, 0.95))
            stressed_lgds.append(s_l)

        stressed_el = sum(sp * sl * e for sp, sl, e in zip(stressed_pds, stressed_lgds, portfolio_eads))
        stressed_k_metrics = [self.compute_basel_capital(sp, sl, e) for sp, sl, e in zip(stressed_pds, stressed_lgds, portfolio_eads)]
        stressed_rwa = sum(m["rwa"] for m in stressed_k_metrics)
        stressed_capital_req = stressed_rwa * 0.08

        el_increase = stressed_el - base_el
        rwa_increase = stressed_rwa - base_rwa
        capital_deficit = stressed_capital_req - base_capital_req

        # Rating migrations under stress
        baseline_ratings = [self.assign_rating_grade(p, 700) for p in portfolio_pds]
        stressed_ratings = [self.assign_rating_grade(sp, 700) for sp in stressed_pds]
        
        rating_order = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
        downgrades = sum(1 for b, s in zip(baseline_ratings, stressed_ratings) if rating_order.index(s) > rating_order.index(b))

        return {
            "macro_shocks": {
                "delta_gdp_pct": delta_gdp_pct,
                "delta_unemployment_pct": delta_unemployment_pct,
                "delta_rate_bps": delta_rate_bps,
                "delta_hpi_pct": delta_hpi_pct,
                "systemic_z_index": round(z_macro, 3)
            },
            "baseline": {
                "expected_loss": round(base_el, 2),
                "rwa": round(base_rwa, 2),
                "capital_requirement": round(base_capital_req, 2),
                "avg_pd": round(float(np.mean(portfolio_pds)), 4),
                "avg_lgd": round(float(np.mean(portfolio_lgds)), 4)
            },
            "stressed": {
                "expected_loss": round(stressed_el, 2),
                "rwa": round(stressed_rwa, 2),
                "capital_requirement": round(stressed_capital_req, 2),
                "avg_pd": round(float(np.mean(stressed_pds)), 4),
                "avg_lgd": round(float(np.mean(stressed_lgds)), 4)
            },
            "impact": {
                "el_increase": round(el_increase, 2),
                "el_surge_pct": round((el_increase / max(1.0, base_el)) * 100.0, 2),
                "rwa_increase": round(rwa_increase, 2),
                "capital_deficit": round(capital_deficit, 2),
                "borrowers_downgraded": downgrades,
                "downgrade_percentage": round((downgrades / max(1, M)) * 100.0, 2)
            }
        }

    # -----------------------------------------------------------------------
    # 8. Markov Chain Rating Migration Term Structure
    # -----------------------------------------------------------------------
    def compute_multi_year_transition(self, years: int = 3) -> Dict[str, Any]:
        """
        Computes multi-period Markov rating migration matrix by matrix exponentiation:
        P(t) = P^t
        """
        years_c = max(1, min(10, years))
        P_t = np.linalg.matrix_power(self.base_transition_matrix, years_c)
        
        grades = ["AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D"]
        matrix_dict = {}
        cumulative_default_curve = {}
        
        for i, grade in enumerate(grades):
            matrix_dict[grade] = {grades[j]: round(float(P_t[i, j]), 4) for j in range(len(grades))}
            cumulative_default_curve[grade] = round(float(P_t[i, -1]), 4) # Probability of reaching D

        return {
            "tenure_years": years_c,
            "transition_matrix": matrix_dict,
            "cumulative_default_probabilities": cumulative_default_curve
        }

# Module-level singleton
quant_service = QuantRiskEngine()
