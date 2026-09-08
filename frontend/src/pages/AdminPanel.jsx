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
  UserCheck,
  ShieldCheck,
  Lock,
  Zap,
  Key,
  Globe,
  Fingerprint
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

  // Cryptographic Blockchain Verification State
  const [verifyStatus, setVerifyStatus] = useState(null);
  const [verifyingChain, setVerifyingChain] = useState(false);

  // Security Telemetry State
  const [telemetry, setTelemetry] = useState(null);

  useEffect(() => {
    if (!isAdmin()) {
      navigate('/');
    } else {
      fetchAuditLogs();
      fetchTelemetry();
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

  const fetchTelemetry = async () => {
    try {
      const data = await authAPI.getSecurityTelemetry();
      setTelemetry(data);
    } catch (err) {
      console.error("Telemetry fetch error:", err);
    }
  };

  const handleVerifyChain = async () => {
    setVerifyingChain(true);
    try {
      const result = await authAPI.verifyAuditChain();
      setVerifyStatus(result);
    } catch (err) {
      console.error("Verification failed:", err);
    } finally {
      setVerifyingChain(false);
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
    log.username.toLowerCase().includes(logFilter.toLowerCase()) ||
    (log.ip_address && log.ip_address.includes(logFilter))
  );

  return (
    <div className="space-y-8 animate-fadeIn font-mono text-white bg-black">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-neutral-900 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black uppercase tracking-wider">Security Command Center</h1>
            <span className="px-2.5 py-0.5 border border-emerald-500 text-emerald-400 text-[10px] font-bold uppercase tracking-widest bg-emerald-950/20 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              SOC 2 / ISO 27001
            </span>
          </div>
          <p className="text-neutral-500 text-xs mt-1 uppercase tracking-widest">
            Cryptographic SHA-256 Audit Blockchain, RTR Token Defense & Access Governance
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={verifyingChain}
          className="px-4 py-2.5 bg-white text-black hover:bg-neutral-200 text-xs font-bold uppercase tracking-wider transition-colors flex items-center gap-2 self-start md:self-auto"
        >
          <Fingerprint className={`w-4 h-4 ${verifyingChain ? 'animate-spin' : ''}`} />
          Verify SHA-256 Audit Chain
        </button>
      </div>

      {/* Security Telemetry & Audit Integrity Verification Banner */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="border border-neutral-900 p-4 bg-neutral-950">
          <div className="flex items-center gap-2 text-neutral-500 text-[10px] font-bold uppercase mb-1">
            <Key className="w-3.5 h-3.5 text-white" />
            <span>Token Security Architecture</span>
          </div>
          <span className="text-base font-black text-white block">15m Access / 7d RTR</span>
          <span className="text-[9px] text-neutral-500 block mt-0.5 uppercase">Rotating Refresh Tokens</span>
        </div>

        <div className="border border-neutral-900 p-4 bg-neutral-950">
          <div className="flex items-center gap-2 text-neutral-500 text-[10px] font-bold uppercase mb-1">
            <Lock className="w-3.5 h-3.5 text-white" />
            <span>Progressive Lockout</span>
          </div>
          <span className="text-base font-black text-emerald-400 block">
            {telemetry ? `${telemetry.active_locked_accounts} Locked Accounts` : "Active (5 Max)"}
          </span>
          <span className="text-[9px] text-neutral-500 block mt-0.5 uppercase">15-Min Lockout on Brute-Force</span>
        </div>

        <div className="border border-neutral-900 p-4 bg-neutral-950">
          <div className="flex items-center gap-2 text-neutral-500 text-[10px] font-bold uppercase mb-1">
            <Zap className="w-3.5 h-3.5 text-white" />
            <span>Sliding-Window Rate Limit</span>
          </div>
          <span className="text-base font-black text-white block">5 Req/Min (Auth)</span>
          <span className="text-[9px] text-neutral-500 block mt-0.5 uppercase">IP-Level DoS Protection</span>
        </div>

        <div className={`p-4 border ${verifyStatus?.is_valid ? 'border-emerald-500/80 bg-emerald-950/10' : verifyStatus?.tampered_count > 0 ? 'border-red-500 bg-red-950/20' : 'border-neutral-900 bg-neutral-950'}`}>
          <div className="flex items-center gap-2 text-neutral-500 text-[10px] font-bold uppercase mb-1">
            <Fingerprint className="w-3.5 h-3.5 text-white" />
            <span>Cryptographic Blockchain</span>
          </div>
          <span className={`text-base font-black block ${verifyStatus?.is_valid ? 'text-emerald-400' : verifyStatus?.tampered_count > 0 ? 'text-red-400' : 'text-white'}`}>
            {verifyStatus ? (verifyStatus.is_valid ? "Chain Verified" : "Tampering Detected!") : "Ready to Audit"}
          </span>
          <span className="text-[9px] text-neutral-400 block mt-0.5 uppercase">
            {verifyStatus ? `${verifyStatus.total_records} Records Unbroken` : "SHA-256 Sequential Hash"}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Create User Form */}
        <div className="glass-panel p-6 rounded-none border-neutral-800 h-fit">
          <h2 className="text-xs font-bold text-white mb-5 uppercase tracking-widest flex items-center gap-2 border-b border-neutral-900 pb-3">
            <UserPlus className="w-4 h-4" />
            Provision Operator Identity
          </h2>

          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider block mb-1.5">
                Username
              </label>
              <input 
                type="text" 
                required
                value={regForm.username}
                onChange={(e) => setRegForm({...regForm, username: e.target.value})}
                placeholder="OPERATOR_ID"
                className="input-field uppercase text-xs"
              />
            </div>

            <div>
              <label className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider block mb-1.5">
                Institutional Email
              </label>
              <input 
                type="email" 
                required
                value={regForm.email}
                onChange={(e) => setRegForm({...regForm, email: e.target.value})}
                placeholder="OPERATOR@INSTITUTION.COM"
                className="input-field text-xs uppercase"
              />
            </div>

            <div>
              <label className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider block mb-1.5">
                Master Password
              </label>
              <input 
                type="password" 
                required
                value={regForm.password}
                onChange={(e) => setRegForm({...regForm, password: e.target.value})}
                placeholder="••••••••••••"
                className="input-field text-xs font-mono"
              />
            </div>

            <div>
              <label className="text-[10px] uppercase font-bold text-neutral-400 tracking-wider block mb-1.5">
                Access Tier (RBAC)
              </label>
              <select 
                value={regForm.role}
                onChange={(e) => setRegForm({...regForm, role: e.target.value})}
                className="input-field text-xs uppercase"
              >
                <option value="ANALYST">Analyst (Assess & Edit PII)</option>
                <option value="VIEWER">Viewer (Masked PII Only)</option>
                <option value="ADMIN">Administrator (Full Access)</option>
              </select>
            </div>

            {regError && (
              <div className="p-3 border border-red-500 bg-black text-red-400 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>{regError}</span>
              </div>
            )}

            {regSuccess && (
              <div className="p-3 border border-white bg-black text-white text-xs flex items-center gap-2">
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>{regSuccess}</span>
              </div>
            )}

            <button 
              type="submit" 
              disabled={regLoading}
              className="btn-primary w-full mt-2 uppercase text-xs font-bold py-2.5"
            >
              {regLoading ? 'Provisioning...' : 'Provision Identity'}
            </button>
          </form>
        </div>

        {/* Right Column: Cryptographic Audit Trail Table */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-none border-neutral-800 flex flex-col h-[650px]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-900 pb-4 mb-4">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-white" />
              <h2 className="text-xs font-bold text-white uppercase tracking-widest">
                Cryptographically Chained Audit Ledger
              </h2>
            </div>
            <input 
              type="text" 
              placeholder="SEARCH BY IP, USER, ACTION..." 
              value={logFilter}
              onChange={(e) => setLogFilter(e.target.value)}
              className="bg-black border border-neutral-800 px-3 py-1.5 text-xs text-white outline-none focus:border-white w-full sm:w-64 uppercase"
            />
          </div>

          {/* Audit Logs Table */}
          <div className="flex-1 overflow-y-auto border border-neutral-900">
            {logsLoading ? (
              <div className="h-full flex flex-col items-center justify-center">
                <Loader className="w-6 h-6 animate-spin text-white mb-2" />
                <span className="text-neutral-600 text-[10px] uppercase font-bold tracking-widest">Validating audit ledger...</span>
              </div>
            ) : logsError ? (
              <div className="h-full flex flex-col items-center justify-center text-center p-4">
                <ShieldAlert className="w-10 h-10 text-white mb-2" />
                <span className="text-neutral-500 text-xs">{logsError}</span>
              </div>
            ) : filteredLogs.length > 0 ? (
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-neutral-950 text-neutral-500 font-semibold border-b border-neutral-900 sticky top-0 z-10 uppercase tracking-wider text-[10px]">
                    <th className="px-3 py-2.5">Timestamp</th>
                    <th className="px-3 py-2.5">Operator</th>
                    <th className="px-3 py-2.5">Action</th>
                    <th className="px-3 py-2.5">Network IP</th>
                    <th className="px-3 py-2.5">Details</th>
                    <th className="px-3 py-2.5 text-right">SHA-256 Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900">
                  {filteredLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-neutral-950/80 transition-colors">
                      <td className="px-3 py-2.5 text-neutral-500 font-mono text-[10px] whitespace-nowrap">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="px-3 py-2.5 font-bold text-white uppercase text-[11px]">
                        {log.username}
                      </td>
                      <td className="px-3 py-2.5">
                        <span className={`font-mono text-[9px] uppercase font-bold px-1.5 py-0.5 border ${
                          log.action.includes('FAILURE') ? 'border-red-500/50 text-red-400 bg-red-950/20' :
                          log.action.includes('PII') ? 'border-amber-500/50 text-amber-400 bg-amber-950/20' :
                          'border-neutral-800 text-neutral-300'
                        }`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-neutral-400 font-mono text-[10px] whitespace-nowrap">
                        {log.ip_address || "127.0.0.1"}
                      </td>
                      <td className="px-3 py-2.5 text-neutral-300 text-[11px] leading-relaxed">
                        {log.details}
                      </td>
                      <td className="px-3 py-2.5 text-right whitespace-nowrap">
                        <span 
                          title={log.record_hash || "Genesis"}
                          className="font-mono text-[9px] text-neutral-500 border border-neutral-900 px-1.5 py-0.5 bg-black"
                        >
                          {log.record_hash ? `${log.record_hash.substring(0, 8)}...` : "GENESIS"}
                        </span>
                      </td>
                    </tr>
                  ))}
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
