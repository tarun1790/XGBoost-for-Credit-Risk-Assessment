import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, User, AlertCircle, Loader } from 'lucide-react';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please enter all credentials');
      return;
    }

    setError('');
    setLoading(true);
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || 
        'Login failed. Please verify your credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#070b13] bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-900/25 via-[#0b0f19] to-brand-dark px-4">
      {/* Decorative Blur Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl -z-10 pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl -z-10 pointer-events-none" />

      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center p-3.5 bg-blue-500/10 border border-blue-500/25 rounded-2xl mb-4 text-brand-accent shadow-glow">
            <Shield className="w-9 h-9" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-1.5">
            Luffy <span className="text-brand-accent">Risk Management</span>
          </h1>
          <p className="text-slate-400 text-sm">
            Credit Risk Analytics & Assessment Engine
          </p>
        </div>

        {/* Card */}
        <div className="glass-panel p-8 rounded-2xl shadow-xl">
          <h2 className="text-xl font-semibold text-slate-100 mb-6">
            Sign In to Platform
          </h2>

          {error && (
            <div className="mb-5 p-3.5 bg-rose-500/10 border border-rose-500/25 text-rose-400 rounded-lg text-sm flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="username" className="form-label">
                Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <User className="w-5 h-5" />
                </div>
                <input
                  id="username"
                  type="text"
                  placeholder="Enter username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="form-input pl-10"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-5 h-5" />
                </div>
                <input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="form-input pl-10"
                  disabled={loading}
                />
              </div>
            </div>

            <button
              type="submit"
              className="w-full btn-primary py-3 flex justify-center items-center gap-2"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" />
                  Authenticating...
                </>
              ) : (
                'Access Dashboard'
              )}
            </button>
          </form>

          {/* Credentials helper */}
          <div className="mt-8 pt-6 border-t border-slate-800 text-xs text-slate-400 space-y-2 leading-relaxed">
            <span className="font-semibold text-slate-300 block mb-1">
              Enterprise Demo Accounts:
            </span>
            <div className="flex justify-between items-center bg-slate-900/50 p-2 border border-slate-800 rounded">
              <span>👤 User: <code className="text-blue-400">admin</code></span>
              <span>🔑 Pass: <code className="text-blue-400">AdminPassword123</code></span>
              <span className="px-1.5 py-0.5 bg-blue-500/10 border border-blue-500/20 text-brand-accent rounded text-[10px]">ADMIN</span>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-2 border border-slate-800 rounded">
              <span>👤 User: <code className="text-blue-400">analyst</code></span>
              <span>🔑 Pass: <code className="text-blue-400">AnalystPassword123</code></span>
              <span className="px-1.5 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-brand-emerald rounded text-[10px]">ANALYST</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
