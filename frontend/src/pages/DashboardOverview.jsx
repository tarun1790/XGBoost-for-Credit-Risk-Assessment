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

  // Monochrome colors for Risk tiers
  const pieData = summary ? [
    { name: 'Low Risk', value: summary.risk_distribution.low, color: '#ffffff' },       
    { name: 'Medium-Low', value: summary.risk_distribution.medium_low, color: '#cccccc' }, 
    { name: 'Medium Risk', value: summary.risk_distribution.medium, color: '#777777' },    
    { name: 'High Risk', value: summary.risk_distribution.high, color: '#222222' }       
  ].filter(item => item.value > 0) : [];

  const chartData = pieData.length > 0 ? pieData : [
    { name: 'No Assessments', value: 1, color: '#111111' }
  ];

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
        <div className="lg:col-span-2 glass-panel p-6 rounded-none border-neutral-800 space-y-4">
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
                      <stop offset="5%" stopColor="#ffffff" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#ffffff" stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#222222" />
                  <XAxis dataKey="date" stroke="#666666" fontSize={10} tickLine={false} />
                  <YAxis domain={[300, 850]} stroke="#666666" fontSize={10} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#000000', borderColor: '#ffffff', color: '#ffffff' }}
                    labelStyle={{ color: '#888888', fontfamily: 'monospace', fontWeight: 'bold', fontSize: 11 }}
                  />
                  <Area type="monotone" dataKey="avg_score" name="Avg Credit Score" stroke="#ffffff" strokeWidth={1.5} fillOpacity={1} fill="url(#colorScore)" />
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
        <div className="glass-panel p-6 rounded-none border-neutral-800 flex flex-col justify-between space-y-4">
          <div>
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">Risk Profile Breakdown</h4>
            <p className="text-neutral-500 text-[10px] uppercase tracking-wider">Borrowers group split</p>
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
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="#000000" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#000000', borderColor: '#ffffff', color: '#ffffff' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-32 h-32 rounded-full border border-neutral-800 flex items-center justify-center">
                <span className="text-neutral-600 text-[10px] font-bold uppercase tracking-wider">Empty</span>
              </div>
            )}
            
            {/* Center score indicator */}
            {summary?.total_assessments > 0 && (
              <div className="absolute flex flex-col items-center justify-center font-mono">
                <span className="text-2xl font-black text-white">{summary.total_assessments}</span>
                <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider">Reports</span>
              </div>
            )}
          </div>

          {/* Legend Grid */}
          <div className="grid grid-cols-2 gap-2 text-[10px] pt-4 border-t border-neutral-900 font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 border border-neutral-700 bg-white shrink-0" />
              <span className="text-neutral-400 truncate">Low Risk: <span className="font-bold text-white">{summary?.risk_distribution.low || 0}</span></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 border border-neutral-700 bg-neutral-300 shrink-0" />
              <span className="text-neutral-400 truncate">Good: <span className="font-bold text-white">{summary?.risk_distribution.medium_low || 0}</span></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 border border-neutral-700 bg-neutral-600 shrink-0" />
              <span className="text-neutral-400 truncate">Fair: <span className="font-bold text-white">{summary?.risk_distribution.medium || 0}</span></span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 border border-neutral-700 bg-neutral-850 shrink-0" />
              <span className="text-neutral-400 truncate">Poor: <span className="font-bold text-white">{summary?.risk_distribution.high || 0}</span></span>
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
