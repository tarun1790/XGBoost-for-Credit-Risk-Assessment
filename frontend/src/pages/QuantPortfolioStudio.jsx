import React, { useState, useEffect } from 'react';
import { quantAPI } from '../services/api';
import {
  Activity,
  Cpu,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Sliders,
  DollarSign,
  Layers,
  ShieldCheck,
  Zap,
  BarChart2,
  ChevronRight,
  PieChart as PieIcon,
  Percent
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell
} from 'recharts';

const QuantPortfolioStudio = () => {
  // State for portfolio summary
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(true);

  // State for Monte Carlo simulation
  const [simulation, setSimulation] = useState(null);
  const [simPaths, setSimPaths] = useState(50000);
  const [loadingSim, setLoadingSim] = useState(false);

  // State for Macro Stress-Testing
  const [macroShocks, setMacroShocks] = useState({
    delta_gdp_pct: -2.5,
    delta_unemployment_pct: 3.0,
    delta_rate_bps: 150.0,
    delta_hpi_pct: -12.0
  });
  const [stressResult, setStressResult] = useState(null);
  const [loadingStress, setLoadingStress] = useState(false);

  // State for RAROC Loan Pricing Calculator
  const [pricingInput, setPricingInput] = useState({
    amt_credit: 150000,
    pd_pct: 2.5,
    has_realty: true,
    has_car: false,
    cost_of_funds_pct: 4.5,
    target_hurdle_pct: 15.0
  });
  const [pricingResult, setPricingResult] = useState(null);
  const [loadingPricing, setLoadingPricing] = useState(false);

  // State for Transition Matrix
  const [transitionTenure, setTransitionTenure] = useState(3);
  const [transitionData, setTransitionData] = useState(null);

  // Initial Data Fetch
  const fetchSummary = async () => {
    setLoadingSummary(true);
    try {
      const data = await quantAPI.getPortfolioSummary();
      setSummary(data);
    } catch (err) {
      console.error("Failed to load quant portfolio summary:", err);
    } finally {
      setLoadingSummary(false);
    }
  };

  const runSimulation = async (paths = simPaths) => {
    setLoadingSim(true);
    try {
      const data = await quantAPI.runSimulation(paths);
      setSimulation(data);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setLoadingSim(false);
    }
  };

  const runStressTest = async (shocks = macroShocks) => {
    setLoadingStress(true);
    try {
      const data = await quantAPI.runStressTest(shocks);
      setStressResult(data);
    } catch (err) {
      console.error("Stress test failed:", err);
    } finally {
      setLoadingStress(false);
    }
  };

  const calculatePricing = async () => {
    setLoadingPricing(true);
    try {
      const payload = {
        amt_credit: Number(pricingInput.amt_credit),
        pd: Number(pricingInput.pd_pct) / 100.0,
        has_realty: Boolean(pricingInput.has_realty),
        has_car: Boolean(pricingInput.has_car),
        cost_of_funds: Number(pricingInput.cost_of_funds_pct) / 100.0,
        opex_rate: 0.012,
        target_hurdle_rate: Number(pricingInput.target_hurdle_pct) / 100.0
      };
      const data = await quantAPI.priceLoan(payload);
      setPricingResult(data);
    } catch (err) {
      console.error("Loan pricing calculation failed:", err);
    } finally {
      setLoadingPricing(false);
    }
  };

  const fetchTransitionMatrix = async (tenure) => {
    try {
      const data = await quantAPI.getTransitionMatrix(tenure);
      setTransitionData(data);
    } catch (err) {
      console.error("Transition matrix fetch failed:", err);
    }
  };

  useEffect(() => {
    fetchSummary();
    runSimulation(50000);
    runStressTest(macroShocks);
    calculatePricing();
    fetchTransitionMatrix(transitionTenure);
  }, []);

  return (
    <div className="space-y-10 animate-fadeIn font-mono bg-black text-white pb-12">
      {/* Upper Executive Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 border-b border-neutral-900 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black tracking-wider uppercase">Quant Risk Studio</h1>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 border border-white text-white text-[10px] font-bold uppercase tracking-widest bg-neutral-950">
              <Cpu className="w-3 h-3" />
              {simulation?.device_used || "GPU (CUDA)"}
            </span>
          </div>
          <p className="text-neutral-500 text-xs mt-1 uppercase tracking-widest">
            Basel III ASRF IRB, IFRS 9 Multi-Horizon ECL, Copula Monte Carlo & CCAR Stress-Testing
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => runSimulation(simPaths)}
            disabled={loadingSim}
            className="px-4 py-2.5 bg-white text-black hover:bg-neutral-200 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-2"
          >
            <Zap className={`w-3.5 h-3.5 ${loadingSim ? 'animate-spin' : ''}`} />
            Run Monte Carlo
          </button>
          <button
            onClick={() => { fetchSummary(); runStressTest(); }}
            disabled={loadingSummary}
            className="p-2.5 border border-neutral-800 hover:border-white text-neutral-400 hover:text-white transition-colors"
            title="Refresh Portfolio"
          >
            <RefreshCw className={`w-4 h-4 ${loadingSummary ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* SECTION 1: BASEL III & IFRS 9 PORTFOLIO CAPITAL KPIS */}
      <div>
        <div className="flex items-center gap-2 mb-4 text-xs font-bold uppercase tracking-widest text-neutral-400">
          <ShieldCheck className="w-4 h-4 text-white" />
          <span>Basel III Pillar 1 & IFRS 9 Portfolio Capitalization</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="border border-neutral-900 p-4 bg-neutral-950/60">
            <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Total EAD Exposure</span>
            <span className="text-xl font-black text-white">
              ${summary ? summary.total_exposure_ead.toLocaleString() : "..."}
            </span>
            <span className="text-[9px] text-neutral-500 block mt-1 uppercase">{summary?.total_loans || 0} active loans</span>
          </div>

          <div className="border border-neutral-900 p-4 bg-neutral-950/60">
            <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Expected Loss (EL)</span>
            <span className="text-xl font-black text-red-400">
              ${summary ? summary.total_expected_loss.toLocaleString() : "..."}
            </span>
            <span className="text-[9px] text-neutral-500 block mt-1 uppercase">
              {summary ? ((summary.total_expected_loss / Math.max(1, summary.total_exposure_ead)) * 100).toFixed(2) : "0"}% of EAD
            </span>
          </div>

          <div className="border border-neutral-900 p-4 bg-neutral-950/60">
            <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Risk-Weighted Assets (RWA)</span>
            <span className="text-xl font-black text-white">
              ${summary ? summary.total_rwa.toLocaleString() : "..."}
            </span>
            <span className="text-[9px] text-neutral-500 block mt-1 uppercase">Basel III Density</span>
          </div>

          <div className="border border-neutral-900 p-4 bg-neutral-950/60">
            <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Min Tier 1 Capital (8%)</span>
            <span className="text-xl font-black text-white">
              ${summary ? summary.total_regulatory_capital.toLocaleString() : "..."}
            </span>
            <span className="text-[9px] text-neutral-500 block mt-1 uppercase">Regulatory Charge</span>
          </div>

          <div className="border border-neutral-900 p-4 bg-neutral-950/60">
            <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Weighted Average PD</span>
            <span className="text-xl font-black text-white">
              {summary ? (summary.weighted_avg_pd * 100).toFixed(2) : "0.00"}%
            </span>
            <span className="text-[9px] text-neutral-500 block mt-1 uppercase">Point-in-Time</span>
          </div>

          <div className="border border-neutral-900 p-4 bg-neutral-950/60">
            <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Weighted Average LGD</span>
            <span className="text-xl font-black text-white">
              {summary ? (summary.weighted_avg_lgd * 100).toFixed(1) : "45.0"}%
            </span>
            <span className="text-[9px] text-neutral-500 block mt-1 uppercase">Haircut-Adjusted</span>
          </div>
        </div>
      </div>

      {/* SECTION 2: GPU COPULA MONTE CARLO LOSS DISTRIBUTION */}
      <div className="border border-neutral-900 p-6 bg-neutral-950">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-neutral-900 pb-4 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-white" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                Vasicek Copula Correlated Loss Distribution ({simPaths.toLocaleString()} Paths)
              </h2>
            </div>
            <p className="text-[11px] text-neutral-500 mt-1">
              Simulates portfolio joint defaults incorporating correlated systematic macroeconomic shocks (Z) and idiosyncratic borrower resilience.
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs">
            <span className="text-neutral-400">Paths:</span>
            {[20000, 50000, 100000].map((count) => (
              <button
                key={count}
                onClick={() => { setSimPaths(count); runSimulation(count); }}
                className={`px-2.5 py-1 border text-[10px] font-bold uppercase transition-colors ${
                  simPaths === count ? 'border-white bg-white text-black' : 'border-neutral-800 text-neutral-400 hover:text-white'
                }`}
              >
                {count / 1000}k
              </button>
            ))}
          </div>
        </div>

        {/* Tail Risk Metrics Banner */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
          <div className="p-3 border border-neutral-900 bg-black">
            <span className="text-[9px] uppercase text-neutral-500 block font-bold">95.0% Credit VaR</span>
            <span className="text-base font-extrabold text-white">
              ${simulation ? simulation.var_95.toLocaleString() : "..."}
            </span>
          </div>
          <div className="p-3 border border-neutral-900 bg-black">
            <span className="text-[9px] uppercase text-neutral-500 block font-bold">99.0% Credit VaR</span>
            <span className="text-base font-extrabold text-white">
              ${simulation ? simulation.var_99.toLocaleString() : "..."}
            </span>
          </div>
          <div className="p-3 border border-white bg-neutral-900">
            <span className="text-[9px] uppercase text-white block font-bold">99.9% Credit VaR (IRB)</span>
            <span className="text-base font-black text-white">
              ${simulation ? simulation.var_999.toLocaleString() : "..."}
            </span>
            <span className="text-[8px] text-neutral-400 block mt-0.5">{simulation?.var_999_pct_of_exposure}% of Portfolio</span>
          </div>
          <div className="p-3 border border-neutral-900 bg-black">
            <span className="text-[9px] uppercase text-neutral-500 block font-bold">Expected Shortfall (ES 99.9%)</span>
            <span className="text-base font-extrabold text-red-400">
              ${simulation ? simulation.expected_shortfall_999.toLocaleString() : "..."}
            </span>
            <span className="text-[8px] text-neutral-500 block mt-0.5">Tail CVaR</span>
          </div>
          <div className="p-3 border border-neutral-900 bg-black">
            <span className="text-[9px] uppercase text-neutral-500 block font-bold">Unexpected Loss (UL)</span>
            <span className="text-base font-extrabold text-white">
              ${simulation ? simulation.unexpected_loss.toLocaleString() : "..."}
            </span>
            <span className="text-[8px] text-neutral-500 block mt-0.5">Economic Capital</span>
          </div>
        </div>

        {/* Loss Distribution Histogram Chart */}
        <div className="h-64 w-full">
          {simulation?.histogram ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={simulation.histogram} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" vertical={false} />
                <XAxis 
                  dataKey="bin_start" 
                  stroke="#737373" 
                  fontSize={10} 
                  tickFormatter={(v) => `$${(v/1000).toFixed(0)}k`} 
                />
                <YAxis stroke="#737373" fontSize={10} tickFormatter={(v) => `${v}`} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-black border border-white p-2.5 text-[11px] shadow-2xl font-mono">
                          <div className="font-bold text-white mb-1">Loss Interval: ${data.bin_start.toLocaleString()} - ${data.bin_end.toLocaleString()}</div>
                          <div className="text-neutral-400">Simulation Frequency: {data.count} paths ({data.frequency_pct}%)</div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="count" fill="#ffffff" radius={[1, 1, 0, 0]}>
                  {simulation.histogram.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.bin_start >= simulation.var_999 ? "#ef4444" : entry.bin_start >= simulation.var_95 ? "#f59e0b" : "#ffffff"} 
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-neutral-500">
              Generating GPU simulation paths...
            </div>
          )}
        </div>
        <div className="flex items-center justify-between text-[9px] uppercase text-neutral-500 font-mono mt-3 border-t border-neutral-900 pt-2">
          <span>White: Standard Loss Regime</span>
          <span className="text-amber-400">Yellow: &gt;95% VaR Tail</span>
          <span className="text-red-400">Red: &gt;99.9% Severe Tail Risk</span>
        </div>
      </div>

      {/* SECTION 3: CCAR / DFAST MACROECONOMIC STRESS-TESTING SIMULATOR */}
      <div className="border border-neutral-900 p-6 bg-neutral-950">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-neutral-900 pb-4 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-white" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                CCAR / DFAST Macroeconomic Stress-Testing Simulator
              </h2>
            </div>
            <p className="text-[11px] text-neutral-500 mt-1">
              Dynamic macro-factor transmission model evaluating portfolio resilience against severe economic contractions.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                const severe = { delta_gdp_pct: -4.5, delta_unemployment_pct: 5.5, delta_rate_bps: 300.0, delta_hpi_pct: -20.0 };
                setMacroShocks(severe);
                runStressTest(severe);
              }}
              className="px-3 py-1.5 border border-red-500/60 hover:border-red-500 text-red-400 hover:bg-red-500/10 text-[10px] font-bold uppercase transition-colors"
            >
              Preset: Severely Adverse
            </button>
            <button
              onClick={() => {
                const base = { delta_gdp_pct: 1.5, delta_unemployment_pct: 0.0, delta_rate_bps: 0.0, delta_hpi_pct: 2.0 };
                setMacroShocks(base);
                runStressTest(base);
              }}
              className="px-3 py-1.5 border border-neutral-800 hover:border-white text-neutral-400 hover:text-white text-[10px] font-bold uppercase transition-colors"
            >
              Reset Baseline
            </button>
          </div>
        </div>

        {/* Sliders Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* GDP Shock Slider */}
          <div className="border border-neutral-900 p-4 bg-black">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-neutral-400 font-bold uppercase">Delta GDP Growth</span>
              <span className={`font-black ${macroShocks.delta_gdp_pct < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {macroShocks.delta_gdp_pct > 0 ? `+${macroShocks.delta_gdp_pct}` : macroShocks.delta_gdp_pct}%
              </span>
            </div>
            <input
              type="range"
              min="-6.0"
              max="4.0"
              step="0.5"
              value={macroShocks.delta_gdp_pct}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                const updated = { ...macroShocks, delta_gdp_pct: val };
                setMacroShocks(updated);
                runStressTest(updated);
              }}
              className="w-full accent-white cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-neutral-600 mt-1">
              <span>-6.0% (Recession)</span>
              <span>+4.0% (Boom)</span>
            </div>
          </div>

          {/* Unemployment Spike Slider */}
          <div className="border border-neutral-900 p-4 bg-black">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-neutral-400 font-bold uppercase">Delta Unemployment</span>
              <span className="font-black text-amber-400">
                +{macroShocks.delta_unemployment_pct}%
              </span>
            </div>
            <input
              type="range"
              min="0.0"
              max="8.0"
              step="0.5"
              value={macroShocks.delta_unemployment_pct}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                const updated = { ...macroShocks, delta_unemployment_pct: val };
                setMacroShocks(updated);
                runStressTest(updated);
              }}
              className="w-full accent-white cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-neutral-600 mt-1">
              <span>0.0% (Normal)</span>
              <span>+8.0% (Severe Spike)</span>
            </div>
          </div>

          {/* Interest Rate Shock */}
          <div className="border border-neutral-900 p-4 bg-black">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-neutral-400 font-bold uppercase">Rate Shock (bps)</span>
              <span className={`font-black ${macroShocks.delta_rate_bps > 0 ? 'text-amber-400' : 'text-neutral-400'}`}>
                {macroShocks.delta_rate_bps > 0 ? `+${macroShocks.delta_rate_bps}` : macroShocks.delta_rate_bps} bps
              </span>
            </div>
            <input
              type="range"
              min="-200"
              max="500"
              step="25"
              value={macroShocks.delta_rate_bps}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                const updated = { ...macroShocks, delta_rate_bps: val };
                setMacroShocks(updated);
                runStressTest(updated);
              }}
              className="w-full accent-white cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-neutral-600 mt-1">
              <span>-200 bps</span>
              <span>+500 bps (Hike)</span>
            </div>
          </div>

          {/* Real Estate / HPI Drop */}
          <div className="border border-neutral-900 p-4 bg-black">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-neutral-400 font-bold uppercase">Delta HPI / Real Estate</span>
              <span className={`font-black ${macroShocks.delta_hpi_pct < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                {macroShocks.delta_hpi_pct > 0 ? `+${macroShocks.delta_hpi_pct}` : macroShocks.delta_hpi_pct}%
              </span>
            </div>
            <input
              type="range"
              min="-30.0"
              max="15.0"
              step="1.0"
              value={macroShocks.delta_hpi_pct}
              onChange={(e) => {
                const val = parseFloat(e.target.value);
                const updated = { ...macroShocks, delta_hpi_pct: val };
                setMacroShocks(updated);
                runStressTest(updated);
              }}
              className="w-full accent-white cursor-pointer"
            />
            <div className="flex justify-between text-[9px] text-neutral-600 mt-1">
              <span>-30% (Crash)</span>
              <span>+15% (Appreciation)</span>
            </div>
          </div>
        </div>

        {/* Stress Test Comparison Results */}
        {stressResult && stressResult.impact && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 border-t border-neutral-900 pt-6">
            <div className="border border-neutral-900 p-4 bg-black">
              <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Stressed Expected Loss</span>
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-black text-red-400">${stressResult.stressed.expected_loss.toLocaleString()}</span>
                <span className="text-[10px] text-neutral-500 line-through">${stressResult.baseline.expected_loss.toLocaleString()}</span>
              </div>
              <span className="text-[10px] text-red-400 block mt-1 font-bold">
                +{stressResult.impact.el_increase.toLocaleString()} (+{stressResult.impact.el_surge_pct}%)
              </span>
            </div>

            <div className="border border-neutral-900 p-4 bg-black">
              <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Stressed RWA</span>
              <div className="flex items-baseline gap-2">
                <span className="text-xl font-black text-white">${stressResult.stressed.rwa.toLocaleString()}</span>
                <span className="text-[10px] text-neutral-500 line-through">${stressResult.baseline.rwa.toLocaleString()}</span>
              </div>
              <span className="text-[10px] text-amber-400 block mt-1 font-bold">
                +${stressResult.impact.rwa_increase.toLocaleString()} RWA inflation
              </span>
            </div>

            <div className="border border-neutral-900 p-4 bg-black">
              <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Capital Deficit / Shortfall</span>
              <span className="text-xl font-black text-red-500">
                ${stressResult.impact.capital_deficit.toLocaleString()}
              </span>
              <span className="text-[10px] text-neutral-500 block mt-1">Required Capital Buffer</span>
            </div>

            <div className="border border-neutral-900 p-4 bg-black">
              <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Rating Downgrades</span>
              <span className="text-xl font-black text-amber-400">
                {stressResult.impact.borrowers_downgraded} borrowers
              </span>
              <span className="text-[10px] text-neutral-500 block mt-1">
                {stressResult.impact.downgrade_percentage}% of active book
              </span>
            </div>
          </div>
        )}
      </div>

      {/* SECTION 4: IFRS 9 STAGING & MARKOV RATING TRANSITION MATRIX */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* IFRS 9 Staging Breakdown */}
        <div className="border border-neutral-900 p-6 bg-neutral-950">
          <div className="flex items-center gap-2 mb-4">
            <Layers className="w-4 h-4 text-white" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-white">
              IFRS 9 / CECL Multi-Horizon Staging
            </h2>
          </div>
          <p className="text-[11px] text-neutral-500 mb-6">
            Classification based on Significant Increase in Credit Risk (SICR) and 12-Month vs. Lifetime provisioning.
          </p>

          <div className="space-y-4">
            <div className="border border-neutral-900 p-4 bg-black flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase block">Stage 1 (Performing)</span>
                <span className="text-[10px] text-neutral-500">12-Month Expected Credit Loss (ECL 12M)</span>
              </div>
              <span className="text-lg font-black text-white">
                {summary?.ifrs9_staging_distribution?.["Stage 1 (Performing)"] || 0} loans
              </span>
            </div>

            <div className="border border-neutral-900 p-4 bg-black flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-amber-400 uppercase block">Stage 2 (Underperforming - SICR)</span>
                <span className="text-[10px] text-neutral-500">Lifetime Expected Credit Loss</span>
              </div>
              <span className="text-lg font-black text-white">
                {summary?.ifrs9_staging_distribution?.["Stage 2 (SICR)"] || 0} loans
              </span>
            </div>

            <div className="border border-neutral-900 p-4 bg-black flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-red-500 uppercase block">Stage 3 (Credit-Impaired)</span>
                <span className="text-[10px] text-neutral-500">Defaulted / Objective Evidence</span>
              </div>
              <span className="text-lg font-black text-white">
                {summary?.ifrs9_staging_distribution?.["Stage 3 (Credit Impaired)"] || 0} loans
              </span>
            </div>
          </div>
        </div>

        {/* Markov Transition Matrix Term Structure */}
        <div className="border border-neutral-900 p-6 bg-neutral-950">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-white" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                {transitionTenure}-Year Cumulative Default Term Structure
              </h2>
            </div>
            <div className="flex gap-1.5">
              {[1, 3, 5].map((y) => (
                <button
                  key={y}
                  onClick={() => { setTransitionTenure(y); fetchTransitionMatrix(y); }}
                  className={`px-2 py-0.5 text-[9px] font-bold uppercase border transition-colors ${
                    transitionTenure === y ? 'border-white bg-white text-black' : 'border-neutral-800 text-neutral-400'
                  }`}
                >
                  {y}Y
                </button>
              ))}
            </div>
          </div>
          <p className="text-[11px] text-neutral-500 mb-4">
            Markov Chain rating migration probabilities (P^t) projecting cumulative probability of default by rating grade.
          </p>

          <div className="grid grid-cols-4 gap-2.5">
            {transitionData?.cumulative_default_probabilities &&
              Object.entries(transitionData.cumulative_default_probabilities).map(([grade, prob]) => (
                <div key={grade} className="border border-neutral-900 p-2.5 bg-black text-center">
                  <span className="text-xs font-black text-white block">{grade}</span>
                  <span className="text-xs font-mono text-neutral-400 block mt-1">
                    {(prob * 100).toFixed(2)}%
                  </span>
                  <span className="text-[8px] text-neutral-600 uppercase">Cum. Default</span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* SECTION 5: RAROC & RISK-ADJUSTED LOAN PRICING SOLVER */}
      <div className="border border-neutral-900 p-6 bg-neutral-950">
        <div className="flex items-center gap-2 mb-2">
          <DollarSign className="w-4 h-4 text-white" />
          <h2 className="text-sm font-bold uppercase tracking-wider text-white">
            Risk-Adjusted Return on Capital (RAROC) & Loan Pricing Engine
          </h2>
        </div>
        <p className="text-[11px] text-neutral-500 mb-6">
          Solves for the breakeven loan interest rate and recommended risk spread (bps) needed to achieve the bank's target hurdle rate on Economic Capital.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="text-[10px] uppercase text-neutral-400 font-bold block mb-1">Loan Principal ($)</label>
            <input
              type="number"
              value={pricingInput.amt_credit}
              onChange={(e) => setPricingInput({ ...pricingInput, amt_credit: e.target.value })}
              className="w-full bg-black border border-neutral-800 p-2 text-xs text-white focus:border-white outline-none font-mono"
            />
          </div>

          <div>
            <label className="text-[10px] uppercase text-neutral-400 font-bold block mb-1">Borrower PD (%)</label>
            <input
              type="number"
              step="0.1"
              value={pricingInput.pd_pct}
              onChange={(e) => setPricingInput({ ...pricingInput, pd_pct: e.target.value })}
              className="w-full bg-black border border-neutral-800 p-2 text-xs text-white focus:border-white outline-none font-mono"
            />
          </div>

          <div>
            <label className="text-[10px] uppercase text-neutral-400 font-bold block mb-1">Cost of Funds (%)</label>
            <input
              type="number"
              step="0.25"
              value={pricingInput.cost_of_funds_pct}
              onChange={(e) => setPricingInput({ ...pricingInput, cost_of_funds_pct: e.target.value })}
              className="w-full bg-black border border-neutral-800 p-2 text-xs text-white focus:border-white outline-none font-mono"
            />
          </div>

          <div>
            <label className="text-[10px] uppercase text-neutral-400 font-bold block mb-1">Target Hurdle Rate (ROE %)</label>
            <input
              type="number"
              step="1.0"
              value={pricingInput.target_hurdle_pct}
              onChange={(e) => setPricingInput({ ...pricingInput, target_hurdle_pct: e.target.value })}
              className="w-full bg-black border border-neutral-800 p-2 text-xs text-white focus:border-white outline-none font-mono"
            />
          </div>
        </div>

        <div className="flex justify-end mb-6">
          <button
            onClick={calculatePricing}
            disabled={loadingPricing}
            className="px-4 py-2 border border-white bg-black hover:bg-white text-white hover:text-black text-xs font-bold uppercase tracking-wider transition-colors"
          >
            Solve Optimal Rate
          </button>
        </div>

        {pricingResult && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border-t border-neutral-900 pt-6">
            <div className="border border-neutral-900 p-4 bg-black">
              <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Recommended Loan Rate</span>
              <span className="text-2xl font-black text-emerald-400">{pricingResult.recommended_interest_rate_pct}%</span>
              <span className="text-[9px] text-neutral-500 block mt-1">APR</span>
            </div>

            <div className="border border-neutral-900 p-4 bg-black">
              <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Recommended Spread</span>
              <span className="text-2xl font-black text-white">{pricingResult.recommended_spread_bps} bps</span>
              <span className="text-[9px] text-neutral-500 block mt-1">Above Cost of Funds</span>
            </div>

            <div className="border border-neutral-900 p-4 bg-black">
              <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Economic Capital Allocation</span>
              <span className="text-2xl font-black text-white">${pricingResult.economic_capital.toLocaleString()}</span>
              <span className="text-[9px] text-neutral-500 block mt-1">Pillar 2 Equity Required</span>
            </div>

            <div className="border border-neutral-900 p-4 bg-black">
              <span className="text-[10px] uppercase text-neutral-500 font-bold block mb-1">Standard Market RAROC</span>
              <span className="text-2xl font-black text-white">{pricingResult.current_market_raroc_pct}%</span>
              <span className="text-[9px] text-neutral-500 block mt-1">vs {pricingResult.target_hurdle_rate_pct}% Target</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuantPortfolioStudio;
