import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FileEdit, 
  Hash, 
  KeyRound, 
  QrCode, 
  Share2, 
  UploadCloud, 
  ShieldCheck, 
  ArrowDown, 
  ArrowRight, 
  CheckCircle2,
  Lock,
  Layers,
  FileCheck2,
  RefreshCw
} from 'lucide-react';

const STEPS = [
  {
    step: '01',
    phase: 'Issuance',
    title: 'College Creates Official Notice',
    description: 'Authorized department heads and the Controller of Examinations draft the official circular in the college administration portal.',
    icon: FileEdit,
    badge: 'Admin Stage',
    badgeColor: 'bg-blue-950 text-blue-300 border-blue-800',
  },
  {
    step: '02',
    phase: 'Indexing',
    title: 'Unique Notice ID Generated',
    description: 'The core security engine allocates an immutable, standardized identifier (e.g. FS-2026-ENG-8492) registered into the institution ledger.',
    icon: Hash,
    badge: 'Registry Stage',
    badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-800',
  },
  {
    step: '03',
    phase: 'Signing',
    title: 'Metadata Digitally Signed',
    description: 'Document content, issuance timestamps, and signatory credentials are encrypted using ECDSA private keys maintained in hardware security modules.',
    icon: KeyRound,
    badge: 'Cryptographic Stage',
    badgeColor: 'bg-purple-950 text-purple-300 border-purple-800',
  },
  {
    step: '04',
    phase: 'Stamping',
    title: 'QR Code & Watermark Embedded',
    description: 'A tamper-evident optical QR watermark and invisible steganographic pattern are embedded into the PDF canvas prior to distribution.',
    icon: QrCode,
    badge: 'Survivability Stage',
    badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800',
  },
  {
    step: '05',
    phase: 'Distribution',
    title: 'Student Receives Forwarded Notice',
    description: 'The document circulates across student WhatsApp groups, Telegram channels, Discord servers, and student club boards as forwarded images or PDFs.',
    icon: Share2,
    badge: 'Transit Stage',
    badgeColor: 'bg-amber-950 text-amber-300 border-amber-800',
  },
  {
    step: '06',
    phase: 'Ingestion',
    title: 'Student Uploads the Notice',
    description: 'A student seeking verification uploads the file or types the Notice ID into The Forwarded Seal web app from their phone or laptop.',
    icon: UploadCloud,
    badge: 'Verification Stage',
    badgeColor: 'bg-cyan-950 text-cyan-300 border-cyan-800',
  },
  {
    step: '07',
    phase: 'Forensics',
    title: 'Authenticity & Integrity Analysis',
    description: 'The verification engine checks digital signatures, extracts steganographic marks, inspects pixel compression noise, and outputs a decisive verdict.',
    icon: ShieldCheck,
    badge: 'Verdict Stage',
    badgeColor: 'bg-emerald-950 text-emerald-300 border-emerald-800',
  },
];

const HowItWorks = () => {
  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-16">
      
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-950/60 border border-cyan-500/30 text-cyan-300">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>END-TO-END SECURITY ARCHITECTURE</span>
        </div>
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight">
          How The Forwarded Seal Works
        </h1>
        <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
          From the moment a dean clicks "Publish" to when a student scans a forwarded WhatsApp screenshot in their dorm room, discover how our 7-step integrity loop defeats forgery.
        </p>
      </div>

      {/* Visual Workflow Overview Card */}
      <div className="cyber-card p-6 sm:p-8 bg-midnight-900/90 border-cyan-500/30">
        <h2 className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400 mb-6 text-center">
          SYSTEM WORKFLOW SCHEMATIC
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
          
          {/* Phase 1: Institutional Issuance */}
          <div className="p-5 rounded-xl bg-midnight-950/80 border border-slate-800 relative">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono text-cyan-400 font-bold">PHASE A</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">College Administration</span>
            </div>
            <h3 className="text-base font-bold text-white mb-2">Publish & Seal</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Dean drafts notice &rarr; Unique Notice ID registered &rarr; Private cryptographic key signs metadata &rarr; Steganographic watermark applied.
            </p>
          </div>

          {/* Phase 2: Uncontrolled Distribution */}
          <div className="p-5 rounded-xl bg-midnight-950/80 border border-slate-800 relative">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono text-amber-400 font-bold">PHASE B</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">Uncontrolled Transit</span>
            </div>
            <h3 className="text-base font-bold text-white mb-2">Messaging Forwards</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Shared via WhatsApp, Telegram, Discord & social media. Vulnerable to bad actors tampering with exam dates or account numbers.
            </p>
          </div>

          {/* Phase 3: Instant Student Verification */}
          <div className="p-5 rounded-xl bg-midnight-950/80 border border-slate-800 relative">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono text-emerald-400 font-bold">PHASE C</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">Student Verification</span>
            </div>
            <h3 className="text-base font-bold text-white mb-2">Forensic Check</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Student uploads file or scans QR &rarr; Multi-vector verification checks signature, pixel splicing & watermark &rarr; Instant verdict delivered.
            </p>
          </div>

        </div>
      </div>

      {/* Complete 7-Step Step-by-Step Breakdown */}
      <div className="space-y-6">
        <div className="text-center max-w-xl mx-auto space-y-2 mb-8">
          <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
            DETAILED TECHNICAL WALKTHROUGH
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-white">
            The 7-Step Verification Lifecycle
          </h2>
        </div>

        <div className="space-y-4">
          {STEPS.map((s, index) => {
            const Icon = s.icon;
            return (
              <div
                key={s.step}
                className="cyber-card p-5 sm:p-6 bg-midnight-900/80 border-slate-800 hover:border-cyan-500/40 transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
              >
                <div className="flex items-start sm:items-center gap-4">
                  {/* Step Number Circle */}
                  <div className="w-12 h-12 rounded-xl bg-midnight-800 border border-slate-700/80 flex items-center justify-center text-cyan-400 font-mono font-bold text-sm shrink-0">
                    {s.step}
                  </div>

                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono border ${s.badgeColor}`}>
                        {s.badge}
                      </span>
                      <span className="text-xs text-slate-400 font-mono">
                        Phase: {s.phase}
                      </span>
                    </div>
                    <h3 className="text-base sm:text-lg font-bold text-white">
                      {s.title}
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
                      {s.description}
                    </p>
                  </div>
                </div>

                <div className="self-end sm:self-center shrink-0">
                  <div className="w-10 h-10 rounded-lg bg-midnight-950 border border-slate-800 flex items-center justify-center text-slate-400">
                    <Icon className="w-5 h-5 text-cyan-400" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="p-8 rounded-2xl bg-gradient-to-r from-midnight-900 via-midnight-850 to-midnight-900 border border-cyan-500/30 text-center space-y-4">
        <h3 className="text-xl font-bold text-white">
          Ready to verify a college circular?
        </h3>
        <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto">
          Verify authentic university circulars and examine forensic integrity directly through our portal.
        </p>
        <div className="pt-2">
          <Link
            to="/verify"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-wider bg-cyan-500 hover:bg-cyan-400 text-midnight-950 transition-all shadow-cyber-sm"
          >
            <span>Go to Verification Engine</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

    </div>
  );
};

export default HowItWorks;

