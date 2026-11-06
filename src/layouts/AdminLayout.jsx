import React, { useEffect, useState } from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  LogOut, 
  ExternalLink,
  Loader2
} from 'lucide-react';
import { authApi } from '../services/api';

const AdminLayout = () => {
  const navigate = useNavigate();
  const [adminUser, setAdminUser] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    let active = true;
    const token = localStorage.getItem('fs_admin_token');
    if (!token) {
      navigate('/admin/login', { replace: true });
      return undefined;
    }

    authApi.getCurrentAdmin()
      .then(({ data }) => {
        if (!active) return;
        setAdminUser(data);
        localStorage.setItem('fs_admin_user', JSON.stringify(data));
      })
      .catch((error) => {
        localStorage.removeItem('fs_admin_token');
        localStorage.removeItem('fs_admin_user');
        const loginError = error.response
          ? 'Your session expired. Please sign in again.'
          : 'The authentication server is unreachable. Start the backend and try again.';
        navigate('/admin/login', { replace: true, state: { loginError } });
      })
      .finally(() => {
        if (active) setIsCheckingSession(false);
      });

    return () => {
      active = false;
    };
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('fs_admin_token');
    localStorage.removeItem('fs_admin_user');
    navigate('/admin/login');
  };

  const displayRole = adminUser?.role
    ? adminUser.role
      .split('_')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ')
    : 'Staff';

  if (isCheckingSession || !adminUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-midnight-950 text-cyan-400">
        <Loader2 className="w-6 h-6 animate-spin" aria-label="Verifying administrator session" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-midnight-950 text-slate-100 font-sans">
      
      {/* Admin Top Navigation Bar */}
      <header className="sticky top-0 z-40 border-b border-slate-800 bg-midnight-900/95 backdrop-blur-md px-4 sm:px-6 lg:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          
          {/* Brand & Portal Badge */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <span className="font-extrabold text-white font-mono tracking-wider text-sm sm:text-base">
                  THE FORWARDED SEAL
                </span>
                <span className="block text-[11px] text-cyan-400 font-mono">
                  ADMINISTRATION & REGISTRY PORTAL
                </span>
              </div>
            </Link>

            <span className="hidden md:inline-block px-2.5 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
              Institutional Environment
            </span>
          </div>

          {/* Right Admin Controls */}
          <div className="flex items-center gap-3 sm:gap-4">
            
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-midnight-850 border border-slate-800 text-xs">
              <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
              <span className="text-slate-300 font-medium">{adminUser?.full_name || adminUser?.name || 'Administrator'}</span>
              <span className="text-slate-500 font-mono text-[11px]">({displayRole})</span>
            </div>

            <Link
              to="/"
              className="text-xs text-slate-400 hover:text-cyan-400 flex items-center gap-1 transition-colors px-2.5 py-1.5 rounded-lg hover:bg-midnight-800"
              title="View Public Verification Portal"
            >
              <span>Public Portal</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>

            <button
              onClick={handleLogout}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-red-400 hover:text-red-300 hover:bg-red-950/40 border border-red-900/40 transition-all flex items-center gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Sign Out</span>
            </button>
          </div>

        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Admin Footer */}
      <footer className="border-t border-slate-800/80 bg-midnight-950 px-4 py-4 text-center text-xs text-slate-500 font-mono">
        The Forwarded Seal • Institutional Document Integrity & Notice Registry
      </footer>
    </div>
  );
};

export default AdminLayout;
