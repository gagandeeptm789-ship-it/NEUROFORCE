import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, ShieldAlert, FileText, CheckCircle2, Lock, ExternalLink } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="border-t border-slate-800/80 bg-midnight-950 text-slate-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="font-extrabold text-white tracking-wider font-mono">
                THE FORWARDED SEAL
              </span>
            </div>
            <p className="text-slate-400 text-sm max-w-md leading-relaxed">
              A university document security initiative engineered to protect students and academic communities against forged circulars, altered fee notices, and unauthorized campus declarations.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono bg-emerald-950/40 border border-emerald-600/30 text-emerald-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Verification Engine Architecture: Ready
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-white font-semibold font-mono tracking-wide text-xs uppercase mb-4 text-cyan-400">
              Platform
            </h3>
            <ul className="space-y-2.5">
              <li>
                <Link to="/" className="hover:text-cyan-400 transition-colors">Home Landing</Link>
              </li>
              <li>
                <Link to="/verify" className="hover:text-cyan-400 transition-colors flex items-center gap-1.5">
                  Verify Notice
                  <span className="text-[10px] px-1.5 py-0.2 bg-cyan-900/60 text-cyan-300 rounded border border-cyan-700/50">Core</span>
                </Link>
              </li>
              <li>
                <Link to="/how-it-works" className="hover:text-cyan-400 transition-colors">How Verification Works</Link>
              </li>
              <li>
                <Link to="/about" className="hover:text-cyan-400 transition-colors">About the Project</Link>
              </li>
              <li>
                <Link to="/admin/login" className="hover:text-cyan-400 transition-colors">College Admin Portal</Link>
              </li>
            </ul>
          </div>

          {/* Security Protocols & Pillars */}
          <div>
            <h3 className="text-white font-semibold font-mono tracking-wide text-xs uppercase mb-4 text-cyan-400">
              Security Pillars
            </h3>
            <ul className="space-y-2.5 text-xs">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <span><strong>Authenticity:</strong> Verifies institutional provenance.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <span><strong>Integrity:</strong> Detects font and pixel splicing tampering.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                <span><strong>Survivability:</strong> Preserves verification across WhatsApp lossy compression.</span>
              </li>
            </ul>
          </div>

        </div>

        {/* Bottom Bar & Cryptographic Notice */}
        <div className="pt-8 border-t border-slate-800/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div>
            &copy; {new Date().getFullYear()} The Forwarded Seal Project. University Cybersecurity Initiative.
          </div>
          <div className="px-3 py-1 rounded bg-slate-900 border border-slate-800 text-[11px] text-slate-400 text-center sm:text-right">
            Official College Document Authenticity & Integrity Verification Platform.
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;

