import React from 'react';
import { Outlet, Link, useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  LogOut, 
  ExternalLink
} from 'lucide-react';

const AdminLayout = () => {
  const navigate = useNavigate();

  const getAdminUser = () => {
    try {
      const stored = localStorage.getItem('fs_admin_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  };

  const adminUser = getAdminUser();

  const handleLogout = () => {
    localStorage.removeItem('fs_admin_token');
    localStorage.removeItem('fs_admin_user');
    navigate('/admin/login');
  };

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
              <span className="text-slate-300 font-medium">{adminUser?.name || 'Administrator'}</span>
              <span className="text-slate-500 font-mono text-[11px]">({adminUser?.role || 'Staff'})</span>
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
