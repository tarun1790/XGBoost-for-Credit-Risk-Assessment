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
      setLogsError('Could not retrieve audit logs.');
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
      setRegSuccess(`Account "${regForm.username}" registered.`);
      setRegForm({
        username: '',
        email: '',
        password: '',
        role: 'ANALYST',
      });
      fetchAuditLogs();
    } catch (err) {
      console.error(err);
      setRegError(err.response?.data?.detail || 'Account registration failed.');
    } finally {
      setRegLoading(false);
    }
  };

  const filteredLogs = logs.filter(log => 
    log.action.toLowerCase().includes(logFilter.toLowerCase()) ||
    log.details.toLowerCase().includes(logFilter.toLowerCase()) ||
    log.username.toLowerCase().includes(logFilter.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-fadeIn font-mono">
      {/* Header */}
      <div className="border-b border-neutral-900 pb-5">
        <h1 className="text-2xl font-black text-white uppercase tracking-wider">Administrative Center</h1>
        <p className="text-neutral-500 text-xs mt-1 uppercase tracking-widest">Manage system user credentials & audit logs</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Create User Form */}
        <div className="glass-panel p-6 rounded-none border-neutral-800 h-fit">
          <h2 className="text-xs font-bold text-white mb-5 uppercase tracking-widest flex items-center gap-2 border-b border-neutral-900 pb-3">
            <UserPlus className="w-4 h-4" />
            Provision Credentials
          </h2>

          {regSuccess && (
            <div className="mb-4 p-3 border border-white text-white bg-black text-xs flex items-center gap-2">
              <CheckCircle className="w-4 h-4 shrink-0" />
              <span>{regSuccess}</span>
            </div>
          )}

          {regError && (
            <div className="mb-4 p-3 border border-neutral-800 text-neutral-400 bg-black text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{regError}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4 text-xs font-mono">
            <div>
              <label className="form-label text-[10px]">Username</label>
              <input 
                type="text" 
                value={regForm.username}
                onChange={(e) => setRegForm({...regForm, username: e.target.value})}
                className="form-input text-xs py-2" 
                placeholder="USERNAME"
                required 
              />
            </div>
            <div>
              <label className="form-label text-[10px]">Email Address</label>
              <input 
                type="email" 
                value={regForm.email}
                onChange={(e) => setRegForm({...regForm, email: e.target.value})}
                className="form-input text-xs py-2" 
                placeholder="EMAIL@BANK.COM"
                required 
              />
            </div>
            <div>
              <label className="form-label text-[10px]">Temporary Password</label>
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
              <label className="form-label text-[10px]">Access Authority Role</label>
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
              className="w-full btn-primary py-2.5 text-xs flex items-center justify-center gap-2 mt-2"
              disabled={regLoading}
            >
              {regLoading ? <Loader className="w-4 h-4 animate-spin" /> : <UserCheck className="w-4 h-4" />}
              Provision Account
            </button>
          </form>
        </div>

        {/* Right Column: Audit Logs Table */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-none border-neutral-800 flex flex-col h-[600px]">
          <div className="border-b border-neutral-900 pb-3 mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2">
              <History className="w-4 h-4" />
              Security Audit Trails
            </h2>
            <input 
              type="text" 
              placeholder="SEARCH AUDIT LOGS..." 
              value={logFilter}
              onChange={(e) => setLogFilter(e.target.value)}
              className="bg-black border border-neutral-800 rounded-none px-3 py-1.5 text-xs placeholder-neutral-600 text-white outline-none focus:border-white w-full sm:w-48 uppercase"
            />
          </div>

          {/* Audit Logs Table */}
          <div className="flex-1 overflow-y-auto border border-neutral-900 rounded-none">
            {logsLoading ? (
              <div className="h-full flex flex-col items-center justify-center">
                <Loader className="w-6 h-6 animate-spin text-white mb-2" />
                <span className="text-neutral-600 text-[10px] uppercase font-bold tracking-widest">Querying audit logs...</span>
              </div>
            ) : logsError ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-4">
                <ShieldAlert className="w-10 h-10 text-white mb-2" />
                <span className="text-neutral-500 text-xs">{logsError}</span>
              </div>
            ) : filteredLogs.length > 0 ? (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-neutral-950 text-neutral-500 font-semibold border-b border-neutral-900 sticky top-0 z-10 uppercase tracking-wider">
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Operator</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Audit Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900">
                  {filteredLogs.map((log) => {
                    return (
                      <tr key={log.id} className="hover:bg-neutral-950 transition-colors">
                        <td className="px-4 py-3 text-neutral-500 font-mono">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 font-bold text-white uppercase">
                          {log.username}
                        </td>
                        <td className="px-4 py-3">
                          <span className="font-mono text-[9px] uppercase font-bold text-neutral-300">
                            {log.action}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-neutral-400 leading-normal uppercase">
                          {log.details}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <div className="h-full flex items-center justify-center text-neutral-600 text-xs uppercase tracking-widest">
                No logs matching filters.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
