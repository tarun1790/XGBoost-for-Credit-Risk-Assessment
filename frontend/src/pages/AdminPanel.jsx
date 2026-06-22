import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI } from '../services/api';
import { 
  UserPlus, 
  ShieldAlert, 
  History, 
  Loader, 
  CheckCircle,
  AlertTriangle,
  UserCheck
} from 'lucide-react';

const AdminPanel = () => {
  const { user, isAdmin } = useAuth();
  const navigate = useNavigate();
  
  // Registration state
  const [regForm, setRegForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'ANALYST',
  });
  const [regSuccess, setRegSuccess] = useState('');
  const [regError, setRegError] = useState('');
  const [regLoading, setRegLoading] = useState(false);

  // Audit logs state
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [logsError, setLogsError] = useState('');
  const [logFilter, setLogFilter] = useState('');

  // Security Redirect: If not admin, bounce to dashboard
  useEffect(() => {
    if (!isAdmin()) {
      navigate('/');
    } else {
      fetchAuditLogs();
    }
  }, [user]);

  const fetchAuditLogs = async () => {
    setLogsLoading(true);
    setLogsError('');
    try {
      const data = await authAPI.getAuditLogs();
      setLogs(data);
    } catch (err) {
      console.error(err);
      setLogsError('Could not retrieve audit logs history.');
    } finally {
      setLogsLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setRegError('');
    setRegSuccess('');
    setRegLoading(true);
    
    try {
      await authAPI.register(regForm);
      setRegSuccess(`Account "${regForm.username}" registered successfully.`);
      setRegForm({
        username: '',
        email: '',
        password: '',
        role: 'ANALYST',
      });
      // Refresh logs because registration adds an audit log
      fetchAuditLogs();
    } catch (err) {
      console.error(err);
      setRegError(err.response?.data?.detail || 'Account registration failed.');
    } finally {
      setRegLoading(false);
    }
  };

  // Filter logs based on search query
  const filteredLogs = logs.filter(log => 
    log.action.toLowerCase().includes(logFilter.toLowerCase()) ||
    log.details.toLowerCase().includes(logFilter.toLowerCase()) ||
    log.username.toLowerCase().includes(logFilter.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white tracking-tight font-sans">Administrative Center</h1>
        <p className="text-slate-400 text-sm mt-1">Manage system user credentials and monitor evaluation audit logs.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Create User Form */}
        <div className="glass-panel p-6 rounded-xl h-fit">
          <h2 className="text-lg font-bold text-slate-100 mb-5 flex items-center gap-2 border-b border-slate-800 pb-3">
            <UserPlus className="text-brand-accent w-5 h-5" />
            Provision Credentials
          </h2>

          {regSuccess && (
            <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/25 text-emerald-400 rounded-lg text-xs flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{regSuccess}</span>
            </div>
          )}

          {regError && (
            <div className="mb-4 p-3 bg-rose-500/10 border border-rose-500/25 text-rose-400 rounded-lg text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{regError}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4 text-sm">
            <div>
              <label className="form-label text-xs">Username</label>
              <input 
                type="text" 
                value={regForm.username}
                onChange={(e) => setRegForm({...regForm, username: e.target.value})}
                className="form-input text-xs py-2" 
                placeholder="jdoe"
                required 
              />
            </div>
            <div>
              <label className="form-label text-xs">Email Address</label>
              <input 
                type="email" 
                value={regForm.email}
                onChange={(e) => setRegForm({...regForm, email: e.target.value})}
                className="form-input text-xs py-2" 
                placeholder="jane.doe@bank.com"
                required 
              />
            </div>
            <div>
              <label className="form-label text-xs">Temporary Password</label>
              <input 
                type="password" 
                value={regForm.password}
                onChange={(e) => setRegForm({...regForm, password: e.target.value})}
                className="form-input text-xs py-2" 
                placeholder="••••••••"
                required 
              />
            </div>
            <div>
              <label className="form-label text-xs">Access Authority Role</label>
              <select
                value={regForm.role}
                onChange={(e) => setRegForm({...regForm, role: e.target.value})}
                className="form-input text-xs py-2"
              >
                <option value="VIEWER">Viewer (Read-Only Dashboards)</option>
                <option value="ANALYST">Analyst (Run Models & Edit Profiles)</option>
                <option value="ADMIN">Administrator (Full Control)</option>
              </select>
            </div>

            <button 
              type="submit" 
              className="w-full btn-primary py-2 text-xs flex items-center justify-center gap-2 mt-2"
              disabled={regLoading}
            >
              {regLoading ? <Loader className="w-4 h-4 animate-spin" /> : <UserCheck className="w-4 h-4" />}
              Provision Account
            </button>
          </form>
        </div>

        {/* Right Column: Audit Logs Table */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-xl flex flex-col h-[600px]">
          <div className="border-b border-slate-800 pb-3 mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <History className="text-brand-accent w-5 h-5" />
              Security Audit Trails
            </h2>
            {/* Log Search Filter */}
            <input 
              type="text" 
              placeholder="Search audit logs..." 
              value={logFilter}
              onChange={(e) => setLogFilter(e.target.value)}
              className="bg-brand-panel border border-slate-800 rounded-lg px-3 py-1.5 text-xs placeholder-slate-500 text-slate-200 outline-none focus:ring-1 focus:ring-brand-accent/50 w-full sm:w-48"
            />
          </div>

          {/* Audit Logs Table */}
          <div className="flex-1 overflow-y-auto border border-slate-800/80 rounded-lg">
            {logsLoading ? (
              <div className="h-full flex flex-col items-center justify-center">
                <Loader className="w-6 h-6 animate-spin text-brand-accent mb-2" />
                <span className="text-slate-500 text-xs">Querying audit trail database...</span>
              </div>
            ) : logsError ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-4">
                <ShieldAlert className="w-10 h-10 text-rose-500 mb-2" />
                <span className="text-slate-400 text-xs">{logsError}</span>
              </div>
            ) : filteredLogs.length > 0 ? (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-900/60 text-slate-400 font-semibold border-b border-slate-800 sticky top-0 z-10">
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Operator</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Audit Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-850">
                  {filteredLogs.map((log) => {
                    let roleBadgeColor = "bg-slate-500/10 border-slate-500/20 text-slate-400";
                    let actionColor = "text-slate-300";
                    
                    if (log.action.includes("ASSESSMENT")) {
                      actionColor = "text-brand-accent font-semibold";
                    } else if (log.action.includes("LOGIN")) {
                      actionColor = "text-brand-emerald";
                    } else if (log.action.includes("DELETED")) {
                      actionColor = "text-brand-rose";
                    }

                    return (
                      <tr key={log.id} className="hover:bg-slate-800/10 transition-colors">
                        <td className="px-4 py-3 text-slate-400 font-mono">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 font-semibold text-slate-300">
                          {log.username}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`font-mono text-[10px] uppercase ${actionColor}`}>
                            {log.action}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-400 leading-normal">
                          {log.details}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                No security transactions logged matching filters.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
