import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  ArrowRight, 
  FileSearch, 
  HelpCircle, 
  Key, 
  Stamp, 
  Eye, 
  UploadCloud, 
  Cpu, 
  FileCheck2, 
  AlertTriangle, 
  Lock,
  ChevronRight,
  Sparkles,
  CheckCircle2,
  Share2
} from 'lucide-react';
import FeatureCard from '../components/FeatureCard';

const Home = () => {
  return (
    <div className="space-y-24 py-8 sm:py-16">
      
      {/* 1. HERO SECTION */}
      <section className="relative px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        
        {/* Subtle background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none -z-10"></div>

        <div className="text-center max-w-4xl mx-auto space-y-6">
          
          {/* Trust Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono bg-cyan-950/60 border border-cyan-500/30 text-cyan-300">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            <span>UNIVERSITY DOCUMENT AUTHENTICITY PLATFORM</span>
          </div>

          {/* Main Hero Headline */}
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight text-white leading-tight">
            Don't Trust the Forward.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500">
              Verify the Source.
            </span>
          </h1>

          {/* Problem Statement Supporting Description */}
          <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Every semester, thousands of university students fall victim to forged circulars, altered fee deadlines, and manipulated holiday announcements circulating through unofficial messaging forwards.
            <strong className="text-white block mt-1"> The Forwarded Seal</strong> restores uncompromised cryptographic trust.
          </p>

          {/* CTA Group */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/verify"
              className="w-full sm:w-auto px-8 py-3.5 rounded-xl font-bold text-sm tracking-wide bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-midnight-950 shadow-cyber-md flex items-center justify-center gap-2 transition-all transform hover:scale-[1.02]"
            >
              <FileSearch className="w-4 h-4 stroke-[2.5]" />
              <span>Verify a Notice</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <Link
              to="/how-it-works"
              className="w-full sm:w-auto px-7 py-3.5 rounded-xl font-semibold text-sm text-slate-200 bg-midnight-900 hover:bg-midnight-850 border border-slate-700/80 hover:border-cyan-500/40 flex items-center justify-center gap-2 transition-all"
            >
              <HelpCircle className="w-4 h-4 text-cyan-400" />
              <span>How It Works</span>
            </Link>
          </div>

          {/* Key Stat Badges */}
          <div className="pt-8 grid grid-cols-2 sm:grid-cols-3 gap-4 max-w-2xl mx-auto text-left">
            <div className="p-3.5 rounded-lg bg-midnight-900/60 border border-slate-800">
              <span className="text-[11px] font-mono text-cyan-400 block uppercase">Tamper Resistance</span>
              <span className="text-xs text-slate-300 font-medium">Detects pixel-level edits</span>
            </div>
            <div className="p-3.5 rounded-lg bg-midnight-900/60 border border-slate-800">
              <span className="text-[11px] font-mono text-cyan-400 block uppercase">Forward Survivability</span>
              <span className="text-xs text-slate-300 font-medium">Survives WhatsApp compression</span>
            </div>
            <div className="p-3.5 rounded-lg bg-midnight-900/60 border border-slate-800 col-span-2 sm:col-span-1">
              <span className="text-[11px] font-mono text-cyan-400 block uppercase">Instant Audit</span>
              <span className="text-xs text-slate-300 font-medium">Zero app installation required</span>
            </div>
          </div>

        </div>
      </section>

      {/* 2. THE THREE CORE SECURITY FEATURES */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <h2 className="text-xs font-mono uppercase tracking-widest text-cyan-400 font-bold">
            ARCHITECTURAL ADVANTAGE
          </h2>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-white">
            Three Layers of Multi-Vector Defense
          </h3>
          <p className="text-sm text-slate-400">
            Forged college circulars easily deceive human eyes. Our forensic pipeline combines institutional cryptography with advanced perceptual image forensics.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            icon={Key}
            badge="Layer 1"
            title="1. Cryptographic Authentication"
            description="Every genuine circular is paired with an institutional digital signature issued exclusively by authorized college administrative controllers. An unalterable hash seals the notice at creation."
            highlight={true}
          />

          <FeatureCard
            icon={Stamp}
            badge="Layer 2"
            title="2. Digital Watermarking"
            description="Imperceptible steganographic watermarks and robust QR anchors are embedded directly across document pages, engineered specifically to survive photo captures, printing, and lossy messaging compression."
          />

          <FeatureCard
            icon={Eye}
            badge="Layer 3"
            title="3. Image Forensics"
            description="Our analysis pipeline uses Error Level Analysis (ELA) and pixel variance diagnostics to pinpoint spliced text, modified dates, altered fee account numbers, and copy-pasted signatures."
          />
        </div>
      </section>

      {/* 3. THREE-STEP EXPLANATION: UPLOAD -> ANALYZE -> VERIFY */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="cyber-card p-8 sm:p-12 border-slate-800/80 bg-gradient-to-b from-midnight-900 to-midnight-950">
          
          <div className="text-center max-w-2xl mx-auto mb-12 space-y-2">
            <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold">
              STUDENT WORKFLOW
            </span>
            <h2 className="text-2xl sm:text-3xl font-black text-white">
              Verify in Three Simple Steps
            </h2>
            <p className="text-xs sm:text-sm text-slate-400">
              Designed for speed when urgent rumors spread across college group chats.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            
            {/* Step 1 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-midnight-800 border-2 border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-cyber-sm">
                <UploadCloud className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase">Step 01</span>
                <h4 className="text-lg font-bold text-white">Upload or Enter ID</h4>
                <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
                  Drag & drop the received PDF, PNG, or screenshot photo, or simply type in the printed Notice ID.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-midnight-800 border-2 border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-cyber-sm">
                <Cpu className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase">Step 02</span>
                <h4 className="text-lg font-bold text-white">Automated Forensics</h4>
                <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
                  The engine matches the document against the college's verified cryptographic ledger and inspects pixels for tampering.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="flex flex-col items-center text-center space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-midnight-800 border-2 border-emerald-500/40 flex items-center justify-center text-emerald-400 shadow-cyber-success">
                <FileCheck2 className="w-8 h-8" />
              </div>
              <div className="space-y-1">
                <span className="text-xs font-mono font-bold text-emerald-400 uppercase">Step 03</span>
                <h4 className="text-lg font-bold text-white">Instant Verdict</h4>
                <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
                  Receive an unequivocal status: Authentic, Tampered, Transformed, or Unverifiable, with an official forensic summary.
                </p>
              </div>
            </div>

          </div>

          {/* CTA Banner Inside Card */}
          <div className="mt-12 pt-8 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-center sm:text-left">
            <div>
              <h4 className="text-base font-bold text-white">
                Have a suspicious notice right now?
              </h4>
              <p className="text-xs text-slate-400">
                Check whether your upcoming exams or fee dates are genuine.
              </p>
            </div>
            <Link
              to="/verify"
              className="px-6 py-2.5 rounded-lg font-bold text-xs uppercase tracking-wider bg-cyan-500 hover:bg-cyan-400 text-midnight-950 transition-all shadow-cyber-sm"
            >
              Verify Now
            </Link>
          </div>

        </div>
      </section>

      {/* 4. CALLOUT: THE PROBLEM OF FORGED NOTICES */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="p-8 rounded-2xl bg-gradient-to-r from-red-950/30 via-midnight-900 to-midnight-900 border border-red-900/40">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-red-950/80 border border-red-500/40 flex items-center justify-center text-red-400 shrink-0">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">
                  Why Fake College Circulars Cause Real Harm
                </h3>
                <p className="text-xs sm:text-sm text-slate-300 mt-1 max-w-2xl leading-relaxed">
                  Bad actors frequently manipulate official letterheads to create false panic: fake holiday notices causing missed lab exams, spoofed bank accounts for fee payments, or fake disciplinary notices. The Forwarded Seal gives colleges and students an immutable source of truth.
                </p>
              </div>
            </div>
            <Link
              to="/about"
              className="px-5 py-2.5 rounded-lg text-xs font-semibold text-white bg-midnight-800 hover:bg-midnight-700 border border-slate-700 hover:border-slate-600 transition-all shrink-0"
            >
              Read Our Mission
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
};

export default Home;

