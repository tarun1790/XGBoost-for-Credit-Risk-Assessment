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
  ChevronRight
} from 'lucide-react';

// Wrapper for checking Authentication
const ProtectedRoute = ({ children, requireAnalyst = false, requireAdmin = false }) => {
  const { user, loading, isAnalyst, isAdmin } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
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
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard, permission: () => true },
    { name: 'Borrowers', path: '/customers', icon: Users, permission: () => true },
    { name: 'System Admin', path: '/admin', icon: UserSquare2, permission: () => isAdmin() },
  ];

  return (
    <div className="h-screen flex bg-black overflow-hidden font-mono">
      {/* Sidebar Panel */}
      <aside className="hidden md:flex md:flex-col md:w-64 bg-black border-r border-neutral-900 shrink-0">
        {/* Brand Logo header */}
        <div className="p-6 border-b border-neutral-900 flex items-center gap-3">
          <div className="p-1.5 border border-white text-white shrink-0">
            <Shield className="w-5 h-5" />
          </div>
          <div>
            <div className="font-extrabold text-white text-base tracking-[0.2em] leading-none uppercase">LUFFY</div>
            <span className="text-[9px] text-neutral-500 font-semibold tracking-normal uppercase">Risk Management</span>
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
                className={`flex items-center justify-between px-4 py-3 rounded-none text-xs font-semibold uppercase tracking-wider transition-all duration-150 ${
                  isActive 
                    ? 'bg-white text-black font-bold border-l-4 border-black pl-3' 
                    : 'text-neutral-400 hover:text-white hover:bg-neutral-950 border border-transparent hover:border-neutral-900'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </div>
                {isActive && <ChevronRight className="w-3.5 h-3.5" />}
              </Link>
            );
          })}
        </nav>

        {/* User Card Profile & Logout */}
        <div className="p-4 border-t border-neutral-900 bg-black">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 border border-neutral-850 rounded-none text-neutral-400 bg-neutral-950">
              <User className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-bold text-neutral-200 truncate font-mono uppercase">{user?.username}</div>
              <span className="inline-flex items-center px-1.5 py-0.5 border border-neutral-800 text-neutral-500 rounded-none text-[9px] font-bold mt-1 uppercase font-mono tracking-wider">
                {user?.role}
              </span>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              navigate('/login');
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-black hover:bg-white text-white hover:text-black rounded-none text-[10px] font-bold border border-neutral-800 hover:border-white uppercase tracking-wider transition-all duration-150"
          >
            <LogOut className="w-3.5 h-3.5 shrink-0" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile Header */}
        <header className="md:hidden bg-black border-b border-neutral-900 px-6 py-4 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <Shield className="text-white w-5 h-5" />
            <span className="font-bold text-white text-xs tracking-widest uppercase">LUFFY RISK</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-[10px] text-neutral-400 font-bold uppercase font-mono">👤 {user?.username}</span>
            <button 
              onClick={() => { logout(); navigate('/login'); }} 
              className="text-neutral-400 hover:text-white"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Scrollable container */}
        <main className="flex-1 overflow-y-auto bg-black p-6 md:p-8">
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
