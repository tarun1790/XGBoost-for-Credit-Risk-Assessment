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
  Cell,
  BarChart,
  Bar,
  Legend
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
      setError('Failed to fetch dashboard metrics. Verify backend connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-100px)]">
        <RefreshCw className="w-8 h-8 animate-spin text-brand-accent" />
        <span className="ml-3 text-slate-400 font-medium">Loading analytics dashboard...</span>
      </div>
    );
  }

  // Define data for Risk Distribution Pie Chart
  const pieData = summary ? [
    { name: 'Low Risk', value: summary.risk_distribution.low, color: '#10b981' },
    { name: 'Medium-Low', value: summary.risk_distribution.medium_low, color: '#60a5fa' },
    { name: 'Medium Risk', value: summary.risk_distribution.medium, color: '#fbbf24' },
    { name: 'High Risk', value: summary.risk_distribution.high, color: '#f43f5e' }
  ].filter(item => item.value > 0) : [];

  // Fallback if no pie data
  const chartData = pieData.length > 0 ? pieData : [
    { name: 'No Assessments', value: 1, color: '#1e2942' }
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Upper header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Credit Risk Overview</h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time aggregate credit ratings and portfolio risk monitoring.
          </p>
        </div>
        <button 
          onClick={fetchData} 
          className="btn-secondary self-start md:self-auto flex items-center gap-2 text-sm"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Stats
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/25 text-rose-400 rounded-xl text-sm flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* Total Customers */}
        <div className="glass-card p-6 rounded-xl flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Borrowers</span>
            <h3 className="text-2xl font-bold text-white">{summary?.total_customers || 0}</h3>
            <span className="text-emerald-400 text-xs flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5" />
              Active in DB
            </span>
          </div>
          <div className="p-3 bg-blue-500/10 border border-blue-500/25 text-brand-accent rounded-lg shadow-glow">
            <Users className="w-6 h-6" />
          </div>
        </div>

        {/* Total Assessments */}
        <div className="glass-card p-6 rounded-xl flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Assessments</span>
            <h3 className="text-2xl font-bold text-white">{summary?.total_assessments || 0}</h3>
            <span className="text-slate-400 text-xs">Evaluations logged</span>
          </div>
          <div className="p-3 bg-violet-500/10 border border-violet-500/25 text-violet-400 rounded-lg">
            <Activity className="w-6 h-6" />
          </div>
        </div>

        {/* Avg Credit Score */}
        <div className="glass-card p-6 rounded-xl flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Portfolio Avg Score</span>
            <h3 className="text-2xl font-bold text-white">
              {summary?.avg_credit_score && summary.avg_credit_score > 0 ? summary.avg_credit_score : 'N/A'}
            </h3>
            <span className={`text-xs flex items-center gap-1 ${
              (summary?.avg_credit_score || 0) >= 650 ? 'text-emerald-400' : 'text-slate-400'
            }`}>
              <Gauge className="w-3.5 h-3.5" />
              Scale: 300 - 850
            </span>
          </div>
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/25 text-brand-emerald rounded-lg shadow-glow-emerald">
            <Gauge className="w-6 h-6" />
          </div>
        </div>

        {/* Default Rate */}
        <div className="glass-card p-6 rounded-xl flex items-center justify-between">
          <div className="space-y-1">
            <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Avg Default Prob (PD)</span>
            <h3 className="text-2xl font-bold text-white">
              {summary?.default_rate ? `${summary.default_rate}%` : 'N/A'}
            </h3>
            <span className={`text-xs flex items-center gap-1 ${
              (summary?.default_rate || 0) > 10 ? 'text-rose-400' : 'text-emerald-400'
            }`}>
              {summary?.default_rate > 10 ? (
                <TrendingUp className="w-3.5 h-3.5" />
              ) : (
                <TrendingDown className="w-3.5 h-3.5" />
              )}
              XGBoost Estimate
            </span>
          </div>
          <div className="p-3 bg-rose-500/10 border border-rose-500/25 text-brand-rose rounded-lg shadow-glow-rose">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-xl space-y-4">
          <div>
            <h4 className="text-lg font-semibold text-slate-100">Scorecard Calibration Trend</h4>
            <p className="text-slate-400 text-xs">Weighted credit scores evaluated over calendar dates</p>
          </div>
          <div className="h-72">
            {summary?.history && summary.history.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={summary.history} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4}/>
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f293d" />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis domain={[300, 850]} stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#161d30', borderColor: '#334155', color: '#f8fafc' }}
                    labelStyle={{ color: '#94a3b8', fontWeight: 600 }}
                  />
                  <Area type="monotone" dataKey="avg_score" name="Avg Credit Score" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorScore)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center border border-dashed border-slate-800 rounded-lg">
                <span className="text-slate-500 text-sm">Insufficient data to plot scoring history. Run assessments.</span>
              </div>
            )}
          </div>
        </div>

        {/* Risk Distribution Chart */}
        <div className="glass-panel p-6 rounded-xl flex flex-col justify-between space-y-4">
          <div>
            <h4 className="text-lg font-semibold text-slate-100">Risk Profile Split</h4>
            <p className="text-slate-400 text-xs">Borrower breakdown by credit risk categories</p>
          </div>
          
          <div className="h-56 relative flex items-center justify-center">
            {summary?.total_assessments > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#161d30', borderColor: '#334155', color: '#f8fafc' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-32 h-32 rounded-full border-[8px] border-slate-800 flex items-center justify-center">
                <span className="text-slate-500 text-xs font-semibold">Empty</span>
              </div>
            )}
            
            {/* Center score indicator */}
            {summary?.total_assessments > 0 && (
              <div className="absolute flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-white">{summary.total_assessments}</span>
                <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Reports</span>
              </div>
            )}
          </div>

          {/* Legend Grid */}
          <div className="grid grid-cols-2 gap-2 text-xs pt-4 border-t border-slate-800/60">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-emerald shrink-0" />
              <span className="text-slate-400 truncate">Low Risk: <span className="font-semibold text-slate-200">{summary?.risk_distribution.low || 0}</span></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-400 shrink-0" />
              <span className="text-slate-400 truncate">Good: <span className="font-semibold text-slate-200">{summary?.risk_distribution.medium_low || 0}</span></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-amber shrink-0" />
              <span className="text-slate-400 truncate">Fair: <span className="font-semibold text-slate-200">{summary?.risk_distribution.medium || 0}</span></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-brand-rose shrink-0" />
              <span className="text-slate-400 truncate">Poor: <span className="font-semibold text-slate-200">{summary?.risk_distribution.high || 0}</span></span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="glass-panel rounded-xl overflow-hidden shadow-lg border border-slate-800/80">
        <div className="p-6 border-b border-slate-800/60 flex items-center justify-between">
          <div>
            <h4 className="text-lg font-semibold text-slate-100">Latest Evaluations</h4>
            <p className="text-slate-400 text-xs">Recent automated risk scorecard calculations</p>
          </div>
          <Link to="/customers" className="text-brand-accent hover:text-blue-400 text-sm font-medium flex items-center gap-1 transition-colors">
            Assess New Client
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          {history.length > 0 ? (
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="bg-slate-900/50 text-slate-400 font-semibold border-b border-slate-800">
                  <th className="px-6 py-4">Borrower Name</th>
                  <th className="px-6 py-4">App ID (SK_ID)</th>
                  <th className="px-6 py-4">Credit Score</th>
                  <th className="px-6 py-4">Risk Level</th>
                  <th className="px-6 py-4">Default Prob (PD)</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {history.map((pred) => {
                  const score = pred.credit_score;
                  let scoreColor = "text-rose-400 bg-rose-500/10 border-rose-500/25";
                  if (score >= 750) scoreColor = "text-emerald-400 bg-emerald-500/10 border-emerald-500/25";
                  else if (score >= 700) scoreColor = "text-blue-400 bg-blue-500/10 border-blue-500/25";
                  else if (score >= 600) scoreColor = "text-amber-400 bg-amber-500/10 border-amber-500/25";

                  return (
                    <tr key={pred.id} className="hover:bg-slate-800/20 transition-colors">
                      <td className="px-6 py-4 font-medium text-slate-100">
                        {pred.customer ? `${pred.customer.first_name} ${pred.customer.last_name}` : 'Unknown'}
                      </td>
                      <td className="px-6 py-4 text-slate-300 font-mono">
                        {pred.customer?.sk_id_curr || 'N/A'}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-1 border rounded-md font-semibold text-xs ${scoreColor}`}>
                          {score}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        {pred.risk_category.replace(/Risk \(.+\)/, 'Risk')}
                      </td>
                      <td className="px-6 py-4 text-slate-300">
                        {(pred.probability_of_default * 100).toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => navigate(`/predictions/${pred.id}`)}
                          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-brand-accent hover:text-white rounded-lg text-xs font-semibold border border-slate-700/80 transition-all duration-150"
                        >
                          View Report
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          ) : (
            <div className="p-8 text-center text-slate-500">
              No recent credit assessments found. Please register and evaluate a customer.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
