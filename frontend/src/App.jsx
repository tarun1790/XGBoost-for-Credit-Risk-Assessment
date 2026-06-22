import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, Link, useLocation, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import DashboardOverview from './pages/DashboardOverview';
import CustomerDirectory from './pages/CustomerDirectory';
import RiskAssessmentDetails from './pages/RiskAssessmentDetails';
import AdminPanel from './pages/AdminPanel';
import { 
  Shield, 
  LayoutDashboard, 
  Users, 
  UserSquare2, 
  LogOut, 
  User,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

// Wrapper for checking Authentication
const ProtectedRoute = ({ children, requireAnalyst = false, requireAdmin = false }) => {
  const { user, loading, isAnalyst, isAdmin } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-brand-dark">
        <div className="w-8 h-8 border-4 border-brand-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAnalyst && !isAnalyst()) {
    return <Navigate to="/" replace />;
  }

  if (requireAdmin && !isAdmin()) {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Main Navigation Layout Sidebar
const Layout = ({ children }) => {
  const { user, logout, isAdmin, isAnalyst } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard, permission: () => true },
    { name: 'Borrowers', path: '/customers', icon: Users, permission: () => true },
    { name: 'System Admin', path: '/admin', icon: UserSquare2, permission: () => isAdmin() },
  ];

  return (
    <div className="h-screen flex bg-brand-dark overflow-hidden">
      {/* Sidebar Panel */}
      <aside className="hidden md:flex md:flex-col md:w-64 bg-[#101625] border-r border-slate-800/80 shrink-0">
        {/* Brand Logo header */}
        <div className="p-6 border-b border-slate-800/60 flex items-center gap-3">
          <Shield className="text-brand-accent w-7 h-7" />
          <div>
            <div className="font-bold text-white text-base tracking-wide leading-none">Luffy <span className="text-brand-accent text-xs">Risk Management</span></div>
            <span className="text-[10px] text-slate-500 font-semibold tracking-wider uppercase">Risk Scorecard</span>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {menuItems.filter(item => item.permission()).map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center justify-between px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive 
                    ? 'bg-gradient-to-r from-blue-600/15 to-blue-500/5 text-brand-accent border-l-4 border-brand-accent pl-3' 
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/20'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5 shrink-0" />
                  <span>{item.name}</span>
                </div>
                {isActive && <ChevronRight className="w-4 h-4" />}
              </Link>
            );
          })}
        </nav>

        {/* User Card Profile & Logout */}
        <div className="p-4 border-t border-slate-800/60 bg-[#0d121e]">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-slate-800 rounded-lg text-slate-300">
              <User className="w-5 h-5" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold text-slate-200 truncate">{user?.username}</div>
              <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-bold border mt-1 capitalize ${
                user?.role === 'ADMIN' 
                  ? 'bg-rose-500/10 border-rose-500/20 text-brand-rose'
                  : user?.role === 'ANALYST'
                    ? 'bg-blue-500/10 border-blue-500/20 text-brand-accent'
                    : 'bg-slate-500/10 border-slate-500/20 text-slate-400'
              }`}>
                {user?.role.toLowerCase()}
              </span>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              navigate('/login');
            }}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 bg-slate-800 hover:bg-rose-950/20 text-slate-400 hover:text-rose-400 rounded-lg text-xs font-semibold border border-slate-700/60 hover:border-rose-900/30 transition-all duration-150"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="md:hidden bg-[#101625] border-b border-slate-800/80 px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <Shield className="text-brand-accent w-6 h-6" />
            <span className="font-bold text-white text-sm">Luffy Risk Management</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs text-slate-400 font-medium capitalize font-mono">👤 {user?.username}</span>
            <button 
              onClick={() => { logout(); navigate('/login'); }} 
              className="text-slate-400 hover:text-rose-400"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Scrollable container */}
        <main className="flex-1 overflow-y-auto bg-brand-dark p-6 md:p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Authentication page */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected Platform routes */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <Layout>
                  <DashboardOverview />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/customers" 
            element={
              <ProtectedRoute>
                <Layout>
                  <CustomerDirectory />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/predictions/:id" 
            element={
              <ProtectedRoute>
                <Layout>
                  <RiskAssessmentDetails />
                </Layout>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute requireAdmin={true}>
                <Layout>
                  <AdminPanel />
                </Layout>
              </ProtectedRoute>
            } 
          />
          
          {/* Catch-all Redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
