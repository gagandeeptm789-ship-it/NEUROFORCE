import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  ShieldCheck, 
  Lock, 
  Mail, 
  Eye, 
  EyeOff, 
  ArrowLeft, 
  AlertCircle, 
  Loader2, 
  KeyRound
} from 'lucide-react';
import { noticeService } from '../services/noticeService';

const AdminLogin = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(location.state?.loginError || '');
  const [forgotMsg, setForgotMsg] = useState('');

  const validateForm = () => {
    if (!email.trim()) {
      setErrorMsg('Institutional email address is required.');
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setErrorMsg('Please enter a valid institutional email address.');
      return false;
    }
    if (!password) {
      setErrorMsg('Password is required.');
      return false;
    }
    if (password.length < 6) {
      setErrorMsg('Password must be at least 6 characters.');
      return false;
    }
    return true;
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setForgotMsg('');

    if (!validateForm()) return;

    setIsLoading(true);
    try {
      const response = await noticeService.adminLogin({ email: email.trim(), password });
      if (response && response.access_token) {
        localStorage.setItem('fs_admin_token', response.access_token);
        if (response.admin) {
          localStorage.setItem('fs_admin_user', JSON.stringify(response.admin));
        }
        navigate('/admin/dashboard', { state: { loginSuccess: true } });
      } else if (response && response.token) {
        localStorage.setItem('fs_admin_token', response.token);
        navigate('/admin/dashboard', { state: { loginSuccess: true } });
      } else {
        setErrorMsg('Invalid response from authentication server.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Login failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = () => {
    setForgotMsg('Password reset instructions will be handled through your university directory administrator.');
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-midnight-950 cyber-grid-pattern">
      
      {/* Back to Home Link */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-6">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-xs font-medium text-slate-400 hover:text-cyan-400 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Public Verification Portal</span>
        </Link>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        
        {/* Brand Card */}
        <div className="cyber-card p-8 bg-midnight-900 border-slate-800 shadow-cyber-md space-y-6">
          
          {/* Header */}
          <div className="text-center space-y-2">
            <div className="w-12 h-12 mx-auto rounded-xl bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <ShieldCheck className="w-7 h-7" />
            </div>
            <h1 className="text-2xl font-black text-white tracking-tight">
              Institutional Admin Portal
            </h1>
            <p className="text-xs text-slate-400">
              Authorized access for College Registrars and Exam Controllers
            </p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            
            {/* Email Field */}
            <div>
              <label className="block text-xs font-mono uppercase text-slate-300 mb-1.5">
                Institutional Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setErrorMsg('');
                  }}
                  placeholder="admin@college.edu"
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-midnight-950 border border-slate-700 focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400 text-sm text-white placeholder-slate-500 transition-all"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-mono uppercase text-slate-300">
                  Security Password
                </label>
                <button
                  type="button"
                  onClick={handleForgotPassword}
                  className="text-[11px] text-cyan-400 hover:underline"
                >
                  Forgot Password?
                </button>
              </div>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setErrorMsg('');
                  }}
                  placeholder="••••••••••••"
                  className="w-full pl-10 pr-11 py-2.5 rounded-xl bg-midnight-950 border border-slate-700 focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400 text-sm text-white placeholder-slate-500 transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {errorMsg && (
              <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/50 text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{errorMsg}</span>
              </div>
            )}

            {/* Forgot Password Message */}
            {forgotMsg && (
              <div className="p-3 rounded-lg bg-amber-950/40 border border-amber-500/50 text-amber-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-amber-400" />
                <span>{forgotMsg}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded-xl font-bold text-xs uppercase tracking-wider bg-cyan-500 hover:bg-cyan-400 text-midnight-950 shadow-cyber-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin text-midnight-950" />
                  <span>Verifying Credentials...</span>
                </>
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>Authorize & Sign In</span>
                </>
              )}
            </button>

          </form>

        </div>

      </div>

    </div>
  );
};

export default AdminLogin;
