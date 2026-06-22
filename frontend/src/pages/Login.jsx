import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { User, Lock, AlertCircle, Loader, ChevronDown } from 'lucide-react';

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
      setError('Credentials required.');
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
        'Authentication failed.'
      );
    } finally {
      setLoading(false);
    }
  };

  const scrollToLogin = () => {
    const loginSection = document.getElementById('login-fold');
    if (loginSection) {
      loginSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="bg-black min-h-screen text-white select-none">
      
      {/* FOLD 1: LUFFY BRANDING SPLASH SCREEN (100vh) */}
      <div className="h-screen w-full flex flex-col justify-center items-center bg-black relative px-4">
        
        {/* Large Luffy letter space, Risk management tight fit */}
        <div className="text-center space-y-2 max-w-4xl">
          <h1 className="text-[14vw] md:text-[10rem] font-extrabold tracking-[0.4em] pl-[0.4em] leading-none text-white uppercase select-none">
            LUFFY
          </h1>
          <div className="border-t border-white pt-3">
            <p className="text-base md:text-xl font-bold tracking-normal uppercase text-neutral-300">
              RISK MANAGEMENT
            </p>
          </div>
        </div>

        {/* Scroll Indicator */}
        <button 
          onClick={scrollToLogin}
          className="absolute bottom-10 flex flex-col items-center gap-2 cursor-pointer group text-neutral-500 hover:text-white transition-colors duration-200"
        >
          <span className="text-[10px] uppercase font-mono tracking-[0.25em]">Scroll to Access</span>
          <ChevronDown className="w-5 h-5 animate-bounce group-hover:translate-y-0.5 transition-transform" />
        </button>
      </div>

      {/* FOLD 2: LOGIN INTERFACE */}
      <div 
        id="login-fold" 
        className="min-h-screen w-full flex items-center justify-center bg-black border-t border-neutral-900 px-4"
      >
        <div className="w-full max-w-md space-y-8 py-12">
          
          {/* Header */}
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight text-white uppercase">
              Sign In
            </h2>
            <p className="text-neutral-500 text-xs mt-1 uppercase tracking-widest font-mono">
              Luffy Risk management platform
            </p>
          </div>

          {/* Form Panel */}
          <div className="border border-white p-8 bg-black rounded-none shadow-[0_0_30px_rgba(255,255,255,0.02)]">
            {error && (
              <div className="mb-6 p-4 border border-white text-white bg-neutral-950 text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-white" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="username" className="form-label">
                  Username
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-neutral-600">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    id="username"
                    type="text"
                    placeholder="USERNAME"
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
                  <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-neutral-600">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    id="password"
                    type="password"
                    placeholder="PASSWORD"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="form-input pl-10"
                    disabled={loading}
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full btn-primary py-3.5 flex justify-center items-center gap-2"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin text-black" />
                    Authenticating...
                  </>
                ) : (
                  'Login'
                )}
              </button>
            </form>

            {/* Help block */}
            <div className="mt-8 pt-6 border-t border-neutral-900 text-[10px] font-mono text-neutral-500 space-y-2">
              <span className="font-semibold text-neutral-400 block uppercase tracking-wider">
                System Credentials:
              </span>
              <div className="space-y-1.5 bg-neutral-950 p-2.5 border border-neutral-900">
                <div className="flex justify-between">
                  <span>ADMIN: <code className="text-white">admin</code></span>
                  <span>PASS: <code className="text-white">AdminPassword123</code></span>
                </div>
                <div className="flex justify-between border-t border-neutral-900 pt-1.5">
                  <span>ANALYST: <code className="text-white">analyst</code></span>
                  <span>PASS: <code className="text-white">AnalystPassword123</code></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
