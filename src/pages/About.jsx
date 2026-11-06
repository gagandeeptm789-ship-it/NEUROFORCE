import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Target, 
  CheckCircle2, 
  Cpu, 
  Layers, 
  Sparkles,
  ArrowRight,
  Fingerprint,
  FileKey,
  Globe2
} from 'lucide-react';

const About = () => {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-16 space-y-16">
      
      {/* Header */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-950/60 border border-cyan-500/30 text-cyan-300">
          <Target className="w-3.5 h-3.5 text-cyan-400" />
          <span>MISSION & ARCHITECTURE</span>
        </div>
        <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight">
          About The Forwarded Seal
        </h1>
        <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
          Rebuilding informational trust in university campuses through cryptographic document provenance and digital forensics.
        </p>
      </div>

      {/* 1. WHY FAKE NOTICES ARE DANGEROUS */}
      <section className="cyber-card p-6 sm:p-8 bg-midnight-900/90 border-slate-800 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-950/80 border border-red-500/40 flex items-center justify-center text-red-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <h2 className="text-xl font-bold text-white">
            The Danger of Forged College Circulars
          </h2>
        </div>
        
        <p className="text-sm text-slate-300 leading-relaxed">
          In higher education institutions, vital information travels primarily through peer-to-peer messaging applications like WhatsApp, Telegram, and student Reddit forums. When notices are forwarded as screenshots, their authentic vector PDF origins are stripped of digital signatures and metadata.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-midnight-950 border border-slate-800">
            <h3 className="text-xs font-bold text-red-400 uppercase font-mono mb-1">Academic Chaos</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Altered exam schedules cause students to miss critical deadlines, practicals, or university final examinations.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-midnight-950 border border-slate-800">
            <h3 className="text-xs font-bold text-red-400 uppercase font-mono mb-1">Financial Fraud</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Forged circulars replace official university bank details and fee portals with spoofed UPI QR codes and malicious accounts.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-midnight-950 border border-slate-800">
            <h3 className="text-xs font-bold text-red-400 uppercase font-mono mb-1">Campus Distress</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Fake notices declaring emergency closures or bogus disciplinary crackdowns create unrest across thousands of students.
            </p>
          </div>
        </div>
      </section>

      {/* 2. PURPOSE OF THE PROJECT */}
      <section className="space-y-4">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-bold">
            FOUNDATIONAL GOAL
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-white">
            The Purpose of The Forwarded Seal
          </h2>
          <p className="text-xs sm:text-sm text-slate-400">
            To provide an open, accessible, and mathematically robust mechanism for students to verify institutional provenance within seconds — without requiring them to install specialized proprietary software.
          </p>
        </div>
      </section>

      {/* 3. THE THREE PILLARS */}
      <section className="space-y-6">
        <h2 className="text-xl font-bold text-white text-center">
          The Three Architectural Pillars
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Pillar 1: Authenticity */}
          <div className="cyber-card p-6 bg-midnight-900 border-emerald-500/30 space-y-3">
            <div className="w-12 h-12 rounded-xl bg-emerald-950/60 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <span className="text-xs font-mono font-bold text-emerald-400 uppercase">Pillar 1</span>
            <h3 className="text-lg font-bold text-white">Authenticity</h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Guarantees the document originated strictly from an authorized college administrative account and was not generated by an unauthorized external party.
            </p>
          </div>

          {/* Pillar 2: Integrity */}
          <div className="cyber-card p-6 bg-midnight-900 border-cyan-500/30 space-y-3">
            <div className="w-12 h-12 rounded-xl bg-cyan-950/60 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <Fingerprint className="w-6 h-6" />
            </div>
            <span className="text-xs font-mono font-bold text-cyan-400 uppercase">Pillar 2</span>
            <h3 className="text-lg font-bold text-white">Integrity</h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Detects any alteration to text, numbers, dates, or signatures after issuance. Even a single changed digit in a date or fee amount triggers a tampering verdict.
            </p>
          </div>

          {/* Pillar 3: Survivability */}
          <div className="cyber-card p-6 bg-midnight-900 border-amber-500/30 space-y-3">
            <div className="w-12 h-12 rounded-xl bg-amber-950/60 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <Layers className="w-6 h-6" />
            </div>
            <span className="text-xs font-mono font-bold text-amber-400 uppercase">Pillar 3</span>
            <h3 className="text-lg font-bold text-white">Survivability</h3>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              Ensures that valid verification remains achievable even after heavy JPEG lossy recompression, screenshot conversions, and WhatsApp stripping of file metadata.
            </p>
          </div>

        </div>
      </section>

      {/* 4. TECHNOLOGY APPROACH */}
      <section className="cyber-card p-6 sm:p-8 bg-midnight-900/80 border-slate-800 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              Technology Approach & Two-Phase Roadmap
            </h2>
            <span className="text-xs text-slate-400 font-mono">
              Designed for clean microservice and API separation
            </span>
          </div>
        </div>

        <p className="text-sm text-slate-300 leading-relaxed">
          The Forwarded Seal architecture is cleanly partitioned into two collaborative tiers:
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-4 rounded-xl bg-midnight-950 border border-cyan-500/30 space-y-2">
            <span className="text-xs font-mono font-bold text-cyan-400 uppercase">
              Phase 1 (Current Frontend Core)
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">
              A high-performance React + Tailwind CSS client with React Router DOM, robust drag-and-drop validation, forensic diagnostic display, and institutional administration management.
            </p>
          </div>

          <div className="p-4 rounded-xl bg-midnight-950 border border-blue-500/30 space-y-2">
            <span className="text-xs font-mono font-bold text-blue-400 uppercase">
              Phase 2 (Python FastAPI Backend)
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">
              Provides the cryptographic signing engine, OpenCV & PIL forensic computer vision pipelines, Notice ID ledger database, and token-based admin authentication.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <div className="text-center pt-4">
        <Link
          to="/verify"
          className="inline-flex items-center gap-2 px-8 py-3.5 rounded-xl font-bold text-sm bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-midnight-950 shadow-cyber-md transition-all"
        >
          <span>Try the Student Verification Tool</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

    </div>
  );
};

export default About;

