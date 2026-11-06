import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  ShieldCheck, 
  Menu, 
  X, 
  FileSearch, 
  HelpCircle, 
  Info, 
  Lock, 
  ExternalLink,
  ChevronRight
} from 'lucide-react';

const Navbar = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Verify Notice', path: '/verify', icon: FileSearch, highlight: true },
    { name: 'How It Works', path: '/how-it-works', icon: HelpCircle },
    { name: 'About', path: '/about', icon: Info },
  ];

  const isActive = (path) => {
    if (path === '/' && location.pathname !== '/') return false;
    return location.pathname.startsWith(path);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-midnight-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18 py-3">
          
          {/* Brand Logo & Name */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 group-hover:border-cyan-400 group-hover:shadow-cyber-sm transition-all duration-300">
              <ShieldCheck className="w-6 h-6 stroke-[2.2]" />
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold tracking-wider text-base sm:text-lg text-white font-mono flex items-center gap-2">
                THE FORWARDED SEAL
                <span className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] uppercase font-mono font-semibold bg-cyan-950/70 border border-cyan-700/60 text-cyan-400 rounded">
                  v1.0
                </span>
              </span>
              <span className="text-[11px] text-slate-400 tracking-tight">
                Document Authenticity Verification
              </span>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-2">
            {navLinks.map((link) => {
              const active = isActive(link.path);
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-1.5 ${
                    active
                      ? 'text-cyan-400 bg-midnight-800/80 border border-cyan-500/30 shadow-cyber-sm'
                      : link.highlight
                      ? 'text-cyan-300 bg-cyan-950/40 border border-cyan-500/20 hover:bg-cyan-900/30 hover:border-cyan-400/40'
                      : 'text-slate-300 hover:text-white hover:bg-midnight-800'
                  }`}
                >
                  {link.icon && <link.icon className={`w-4 h-4 ${active ? 'text-cyan-400' : 'text-slate-400'}`} />}
                  {link.name}
                </Link>
              );
            })}
          </nav>

          {/* Right Action: Admin Portal CTA */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              to={localStorage.getItem('fs_admin_token') ? "/admin/dashboard" : "/admin/login"}
              className="px-4 py-2 rounded-lg text-sm font-medium text-slate-200 bg-midnight-850 hover:bg-midnight-800 border border-slate-700/80 hover:border-slate-600 transition-all duration-200 flex items-center gap-2"
            >
              <Lock className="w-3.5 h-3.5 text-cyan-400" />
              <span>{localStorage.getItem('fs_admin_token') ? 'Admin Dashboard' : 'Admin Portal'}</span>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-midnight-800 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-slate-800 bg-midnight-900/98 px-4 pt-3 pb-5 space-y-2">
          {navLinks.map((link) => {
            const active = isActive(link.path);
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg text-base font-medium ${
                  active
                    ? 'text-cyan-400 bg-midnight-800 border border-cyan-500/40'
                    : 'text-slate-300 hover:bg-midnight-800/80'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  {link.icon && <link.icon className="w-5 h-5 text-slate-400" />}
                  <span>{link.name}</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-500" />
              </Link>
            );
          })}
          <div className="pt-3 border-t border-slate-800">
            <Link
              to="/admin/login"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg text-sm font-medium text-slate-200 bg-midnight-800 border border-slate-700 hover:bg-midnight-700"
            >
              <Lock className="w-4 h-4 text-cyan-400" />
              <span>Admin Portal Login</span>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};

export default Navbar;

