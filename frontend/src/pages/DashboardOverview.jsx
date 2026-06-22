import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { dashboardAPI, predictionAPI } from '../services/api';
import { 
  Users, 
  Activity, 
  Gauge, 
  TrendingUp, 
  AlertTriangle, 
  RefreshCw,
  ArrowRight,
  TrendingDown
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const DashboardOverview = () => {
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const summaryData = await dashboardAPI.getSummary();
      setSummary(summaryData);
      
      const historyData = await predictionAPI.getHistory(0, 5);
      setHistory(historyData);
    } catch (err) {
      console.error(err);
      setError('Could not connect to database.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading && !summary) {
    return (
      <div className="flex flex-col items-center justify-center h-[calc(100vh-100px)]">
        <RefreshCw className="w-6 h-6 animate-spin text-white mb-2" />
        <span className="text-neutral-500 font-bold uppercase text-[10px] tracking-widest font-mono">Querying Platform...</span>
      </div>
    );
  }

  // Calculate monochrome percentages for the custom concentric SVG ring scanner
  const totalAssessments = summary?.total_assessments || 0;
  const pLow = totalAssessments > 0 ? ((summary?.risk_distribution?.low || 0) / totalAssessments) * 100 : 0;
  const pMedLow = totalAssessments > 0 ? ((summary?.risk_distribution?.medium_low || 0) / totalAssessments) * 100 : 0;
  const pMed = totalAssessments > 0 ? ((summary?.risk_distribution?.medium || 0) / totalAssessments) * 100 : 0;
  const pHigh = totalAssessments > 0 ? ((summary?.risk_distribution?.high || 0) / totalAssessments) * 100 : 0;

  const lowCount = summary?.risk_distribution?.low || 0;
  const medLowCount = summary?.risk_distribution?.medium_low || 0;
  const medCount = summary?.risk_distribution?.medium || 0;
  const highCount = summary?.risk_distribution?.high || 0;

  return (
    <div className="space-y-8 animate-fadeIn font-mono bg-black">
      {/* Upper header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-neutral-900 pb-5">
        <div>
          <h1 className="text-2xl font-black text-white uppercase tracking-wider">Credit Risk Audit</h1>
          <p className="text-neutral-500 text-xs mt-1 uppercase tracking-widest">
            Portfolio Aggregate Analytics & Risk Scorecards
          </p>
        </div>
        <button 
          onClick={fetchData} 
          className="btn-secondary self-start md:self-auto flex items-center gap-2 text-xs uppercase"
          disabled={loading}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Stats
        </button>
      </div>

      {error && (
        <div className="p-4 border border-white text-white bg-black text-xs flex items-center gap-2 font-mono">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Customers */}
        <div className="glass-card p-6 rounded-none flex items-center justify-between border-neutral-800">
          <div className="space-y-1">
            <span className="text-neutral-500 text-[10px] font-bold uppercase tracking-wider">Borrowers</span>
            <h3 className="text-2xl font-black text-white">{summary?.total_customers || 0}</h3>
            <span className="text-neutral-400 text-[10px] flex items-center gap-1 uppercase">
              <TrendingUp className="w-3 h-3" />
              Active in DB
            </span>
          </div>
          <div className="p-3 border border-neutral-800 text-white rounded-none bg-neutral-950">
            <Users className="w-5 h-5" />
          </div>
        </div>

        {/* Total Assessments */}
        <div className="glass-card p-6 rounded-none flex items-center justify-between border-neutral-800">
          <div className="space-y-1">
            <span className="text-neutral-500 text-[10px] font-bold uppercase tracking-wider">Evaluations</span>
            <h3 className="text-2xl font-black text-white">{summary?.total_assessments || 0}</h3>
            <span className="text-neutral-400 text-[10px] uppercase">Assessments run</span>
          </div>
          <div className="p-3 border border-neutral-800 text-white rounded-none bg-neutral-950">
            <Activity className="w-5 h-5" />
          </div>
        </div>

        {/* Avg Credit Score */}
        <div className="glass-card p-6 rounded-none flex items-center justify-between border-neutral-800">
          <div className="space-y-1">
            <span className="text-neutral-500 text-[10px] font-bold uppercase tracking-wider">Avg Credit Rating</span>
            <h3 className="text-2xl font-black text-white">
              {summary?.avg_credit_score && summary.avg_credit_score > 0 ? summary.avg_credit_score : 'N/A'}
            </h3>
            <span className="text-neutral-400 text-[10px] flex items-center gap-1 uppercase">
              <Gauge className="w-3 h-3" />
              Scale: 300 - 850
            </span>
          </div>
          <div className="p-3 border border-neutral-800 text-white rounded-none bg-neutral-950">
            <Gauge className="w-5 h-5" />
          </div>
        </div>

        {/* Default Rate */}
        <div className="glass-card p-6 rounded-none flex items-center justify-between border-neutral-800">
          <div className="space-y-1">
            <span className="text-neutral-500 text-[10px] font-bold uppercase tracking-wider">Avg Default Prob</span>
            <h3 className="text-2xl font-black text-white">
              {summary?.default_rate ? `${summary.default_rate}%` : 'N/A'}
            </h3>
            <span className="text-neutral-400 text-[10px] flex items-center gap-1 uppercase">
              {summary?.default_rate > 10 ? (
                <TrendingUp className="w-3 h-3" />
              ) : (
                <TrendingDown className="w-3 h-3" />
              )}
              XGBoost Model
            </span>
          </div>
          <div className="p-3 border border-neutral-800 text-white rounded-none bg-neutral-950">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-none border-neutral-800 space-y-4 relative overflow-hidden">
          <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-neutral-800" />
          <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-neutral-800" />
          <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-neutral-800" />
          <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-neutral-800" />
          
          <div>
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">Scoring Calibration History</h4>
            <p className="text-neutral-500 text-[10px] uppercase tracking-wider">Mean credit ratings evaluated over dates</p>
          </div>
          <div className="h-72">
            {summary?.history && summary.history.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={summary.history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ffffff" stopOpacity={0.12}/>
                      <stop offset="95%" stopColor="#ffffff" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="none" stroke="#111111" />
                  <XAxis dataKey="date" stroke="#444444" fontSize={10} tickLine={false} />
                  <YAxis domain={[300, 850]} stroke="#444444" fontSize={10} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#000000', borderColor: '#ffffff', color: '#ffffff', fontFamily: 'monospace' }}
                    labelStyle={{ color: '#888888', fontfamily: 'monospace', fontWeight: 'bold', fontSize: 10 }}
                  />
                  <ReferenceLine y={600} stroke="#333333" strokeDasharray="3 3" label={{ value: "APPROVAL LIMIT (600)", fill: "#666666", fontSize: 8, position: "top", fontFamily: 'monospace' }} />
                  <Area type="step" dataKey="avg_score" name="Avg Credit Score" stroke="#ffffff" strokeWidth={2} fillOpacity={1} fill="url(#colorScore)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center border border-dashed border-neutral-900">
                <span className="text-neutral-600 text-xs font-mono uppercase tracking-widest">No history data logged</span>
              </div>
            )}
          </div>
        </div>

        {/* Risk Distribution Chart */}
        <div className="glass-panel p-6 rounded-none border-neutral-800 flex flex-col justify-between space-y-4 relative overflow-hidden">
          <div className="absolute top-2 left-2 w-3 h-3 border-t-2 border-l-2 border-neutral-800" />
          <div className="absolute top-2 right-2 w-3 h-3 border-t-2 border-r-2 border-neutral-800" />
          <div className="absolute bottom-2 left-2 w-3 h-3 border-b-2 border-l-2 border-neutral-800" />
          <div className="absolute bottom-2 right-2 w-3 h-3 border-b-2 border-r-2 border-neutral-800" />
          
          <div>
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">Risk Profile Breakdown</h4>
            <p className="text-neutral-500 text-[10px] uppercase tracking-wider">Concentric Ring Radar Telemetry</p>
          </div>
          
          <div className="h-56 relative flex items-center justify-center">
            {summary?.total_assessments > 0 ? (
              <div className="relative w-48 h-48 flex items-center justify-center">
                {/* Custom Concentric SVG Radar Ring Scanner */}
                <svg viewBox="0 0 240 240" className="w-full h-full">
                  {/* Background crosshair grid markings */}
                  <line x1="120" y1="10" x2="120" y2="230" stroke="#141414" strokeWidth="1" strokeDasharray="2 3" />
                  <line x1="10" y1="120" x2="270" y2="120" stroke="#141414" strokeWidth="1" strokeDasharray="2 3" />
                  
                  {/* Concentric Circle Guides */}
                  <circle cx="120" cy="120" r="45" fill="none" stroke="#111111" strokeWidth="1" strokeDasharray="2 4" />
                  <circle cx="120" cy="120" r="62" fill="none" stroke="#111111" strokeWidth="1" strokeDasharray="2 4" />
                  <circle cx="120" cy="120" r="79" fill="none" stroke="#111111" strokeWidth="1" strokeDasharray="2 4" />
                  <circle cx="120" cy="120" r="96" fill="none" stroke="#111111" strokeWidth="1" strokeDasharray="2 4" />

                  {/* Low Risk Ring (radius 45) */}
                  <circle cx="120" cy="120" r="45" fill="none" stroke="#141414" strokeWidth="4.5" />
                  {pLow > 0 && (
                    <circle cx="120" cy="120" r="45" fill="none" stroke="#ffffff" strokeWidth="4.5"
                      strokeDasharray={2 * Math.PI * 45} strokeDashoffset={2 * Math.PI * 45 - (pLow / 100) * (2 * Math.PI * 45)}
                      strokeLinecap="square" className="transition-all duration-1000 ease-out" transform="rotate(-90 120 120)" />
                  )}

                  {/* Medium-Low Ring (radius 62) */}
                  <circle cx="120" cy="120" r="62" fill="none" stroke="#141414" strokeWidth="4.5" />
                  {pMedLow > 0 && (
                    <circle cx="120" cy="120" r="62" fill="none" stroke="#a3a3a3" strokeWidth="4.5"
                      strokeDasharray={2 * Math.PI * 62} strokeDashoffset={2 * Math.PI * 62 - (pMedLow / 100) * (2 * Math.PI * 62)}
                      strokeLinecap="square" className="transition-all duration-1000 ease-out" transform="rotate(-90 120 120)" />
                  )}

                  {/* Medium Ring (radius 79) */}
                  <circle cx="120" cy="120" r="79" fill="none" stroke="#141414" strokeWidth="4.5" />
                  {pMed > 0 && (
                    <circle cx="120" cy="120" r="79" fill="none" stroke="#525252" strokeWidth="4.5"
                      strokeDasharray={2 * Math.PI * 79} strokeDashoffset={2 * Math.PI * 79 - (pMed / 100) * (2 * Math.PI * 79)}
                      strokeLinecap="square" className="transition-all duration-1000 ease-out" transform="rotate(-90 120 120)" />
                  )}

                  {/* High Risk Ring (radius 96) */}
                  <circle cx="120" cy="120" r="96" fill="none" stroke="#141414" strokeWidth="4.5" />
                  {pHigh > 0 && (
                    <circle cx="120" cy="120" r="96" fill="none" stroke="#ffffff" strokeWidth="4.5" strokeDasharray="2 3"
                      strokeDashoffset={2 * Math.PI * 96 - (pHigh / 100) * (2 * Math.PI * 96)}
                      strokeLinecap="square" className="transition-all duration-1000 ease-out" transform="rotate(-90 120 120)" />
                  )}
                  
                  {/* Center Hub */}
                  <circle cx="120" cy="120" r="28" fill="#000000" stroke="#222222" strokeWidth="1" />
                </svg>
                
                {/* Center score readout */}
                <div className="absolute flex flex-col items-center justify-center font-mono pointer-events-none">
                  <span className="text-xl font-black text-white">{summary.total_assessments}</span>
                  <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider">Reports</span>
                </div>
              </div>
            ) : (
              <div className="w-32 h-32 rounded-full border border-neutral-800 flex items-center justify-center">
                <span className="text-neutral-600 text-[10px] font-bold uppercase tracking-wider">Empty</span>
              </div>
            )}
          </div>

          {/* Legend Grid */}
          <div className="grid grid-cols-2 gap-3 text-[10px] pt-4 border-t border-neutral-900 font-mono">
            <div className="flex flex-col border-l-2 border-white pl-2">
              <span className="text-neutral-500 uppercase font-bold tracking-wider">LOW RISK [I]</span>
              <span className="text-white text-xs font-black mt-0.5">{lowCount} ({pLow.toFixed(1)}%)</span>
            </div>
            <div className="flex flex-col border-l-2 border-neutral-450 pl-2">
              <span className="text-neutral-500 uppercase font-bold tracking-wider">GOOD [II]</span>
              <span className="text-neutral-300 text-xs font-black mt-0.5">{medLowCount} ({pMedLow.toFixed(1)}%)</span>
            </div>
            <div className="flex flex-col border-l-2 border-neutral-600 pl-2">
              <span className="text-neutral-500 uppercase font-bold tracking-wider">FAIR [III]</span>
              <span className="text-neutral-450 text-xs font-black mt-0.5">{medCount} ({pMed.toFixed(1)}%)</span>
            </div>
            <div className="flex flex-col border-l-2 border-white border-dashed pl-2">
              <span className="text-neutral-500 uppercase font-bold tracking-wider">POOR [IV]</span>
              <span className="text-neutral-500 text-xs font-black mt-0.5">{highCount} ({pHigh.toFixed(1)}%)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="glass-panel rounded-none overflow-hidden border-neutral-850">
        <div className="p-6 border-b border-neutral-900 flex items-center justify-between">
          <div>
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">Latest Portfolio Audits</h4>
            <p className="text-neutral-500 text-[10px] uppercase tracking-wider">Automated risk scorecard calculations log</p>
          </div>
          <Link to="/customers" className="text-white hover:underline text-xs font-bold flex items-center gap-1 uppercase tracking-wider">
            Run Evaluation
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          {history.length > 0 ? (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-neutral-950 text-neutral-500 font-semibold border-b border-neutral-900 uppercase tracking-wider">
                  <th className="px-6 py-4">Borrower Name</th>
                  <th className="px-6 py-4">App ID</th>
                  <th className="px-6 py-4">Credit Score</th>
                  <th className="px-6 py-4">Risk Level</th>
                  <th className="px-6 py-4">Default Prob (PD)</th>
                  <th className="px-6 py-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900">
                {history.map((pred) => {
                  return (
                    <tr key={pred.id} className="hover:bg-neutral-950 transition-colors">
                      <td className="px-6 py-4 font-bold text-white uppercase">
                        {pred.customer ? `${pred.customer.first_name} ${pred.customer.last_name}` : 'Unknown'}
                      </td>
                      <td className="px-6 py-4 text-neutral-300 font-mono">
                        {pred.customer?.sk_id_curr || 'N/A'}
                      </td>
                      <td className="px-6 py-4 font-mono">
                        <span className="px-2 py-0.5 border border-white font-bold text-white bg-black">
                          {pred.credit_score}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-neutral-300 uppercase">
                        {pred.risk_category.replace(/Risk \(.+\)/, 'Risk')}
                      </td>
                      <td className="px-6 py-4 text-neutral-300 font-mono">
                        {(pred.probability_of_default * 100).toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => navigate(`/predictions/${pred.id}`)}
                          className="px-3 py-1.5 bg-black hover:bg-white text-white hover:text-black border border-neutral-800 hover:border-white text-[10px] font-bold uppercase transition-all duration-150"
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-neutral-600 uppercase text-xs tracking-wider">
              No recent credit assessments found.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
