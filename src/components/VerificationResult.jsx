import React from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  HelpCircle, 
  ShieldCheck, 
  ShieldAlert, 
  ShieldX, 
  RotateCcw, 
  Download, 
  ExternalLink,
  Cpu,
  Layers,
  Fingerprint,
  Calendar,
  Building,
  User,
  Info
} from 'lucide-react';

const STATUS_CONFIGS = {
  VERIFIED: {
    title: 'VERIFIED — AUTHENTIC NOTICE',
    subtitle: 'Official College Notice. Signature & Seal Intact.',
    badge: 'AUTHENTIC RECORD',
    icon: ShieldCheck,
    badgeColor: 'bg-emerald-950/80 text-emerald-400 border-emerald-500/50',
    borderColor: 'border-emerald-500/50',
    headerBg: 'from-emerald-950/40 via-midnight-900 to-midnight-950',
    accentColor: 'text-emerald-400',
    glowClass: 'shadow-cyber-success',
  },
  TAMPERING_DETECTED: {
    title: 'TAMPERING DETECTED — SUSPICIOUS MODIFICATIONS FOUND',
    subtitle: 'Warning: Pixel or text alterations detected. Do not rely on forwarded contents.',
    badge: 'FORGERY ALERT',
    icon: ShieldAlert,
    badgeColor: 'bg-red-950/80 text-red-400 border-red-500/50',
    borderColor: 'border-red-500/50',
    headerBg: 'from-red-950/40 via-midnight-900 to-midnight-950',
    accentColor: 'text-red-400',
    glowClass: 'shadow-cyber-danger',
  },
  AUTHENTIC_TRANSFORMED: {
    title: 'AUTHENTIC BUT TRANSFORMED (SURVIVABILITY VERIFIED)',
    subtitle: 'Content matches official record, but file underwent messaging compression or screenshot re-encoding.',
    badge: 'TRANSFORMED VARIANT',
    icon: AlertTriangle,
    badgeColor: 'bg-amber-950/80 text-amber-400 border-amber-500/50',
    borderColor: 'border-amber-500/50',
    headerBg: 'from-amber-950/40 via-midnight-900 to-midnight-950',
    accentColor: 'text-amber-400',
    glowClass: 'shadow-cyber-amber',
  },
  UNVERIFIABLE: {
    title: 'UNVERIFIABLE — INSUFFICIENT EVIDENCE',
    subtitle: 'Notice ID or document watermark was not found in the verified university registry.',
    badge: 'UNREGISTERED',
    icon: ShieldX,
    badgeColor: 'bg-slate-800 text-slate-300 border-slate-600',
    borderColor: 'border-slate-700',
    headerBg: 'from-slate-900/60 via-midnight-900 to-midnight-950',
    accentColor: 'text-slate-400',
    glowClass: '',
  },
};

const VerificationResult = ({ result, onReset }) => {
  if (!result || !result.data) return null;

  const notice = result.data;
  const status = notice.status || 'UNVERIFIABLE';
  const config = STATUS_CONFIGS[status] || STATUS_CONFIGS.UNVERIFIABLE;
  const StatusIcon = config.icon;
  const audit = notice.securityAudit || {};

  const formatDate = (isoString) => {
    if (!isoString || isoString === 'Unknown') return 'Unspecified';
    try {
      return new Date(isoString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className={`cyber-card overflow-hidden border ${config.borderColor} ${config.glowClass} transition-all duration-300 animate-fadeIn`}>
      
      {/* Header Verdict Section */}
      <div className={`p-6 sm:p-8 bg-gradient-to-b ${config.headerBg} border-b border-slate-800`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className={`w-14 h-14 rounded-xl border flex items-center justify-center shrink-0 ${config.badgeColor}`}>
              <StatusIcon className="w-8 h-8" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase tracking-wider border ${config.badgeColor}`}>
                  {config.badge}
                </span>
                <span className="text-xs text-slate-400 font-mono">
                  Confidence Score: <strong className={config.accentColor}>{notice.matchScore}%</strong>
                </span>
              </div>
              <h2 className={`text-xl sm:text-2xl font-black tracking-tight ${config.accentColor}`}>
                {config.title}
              </h2>
              <p className="text-sm text-slate-300 mt-1 max-w-2xl">
                {config.subtitle}
              </p>
            </div>
          </div>

          {/* Quick Action Button */}
          <div className="flex items-center gap-2 self-start md:self-center shrink-0">
            <button
              onClick={onReset}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-300 hover:text-white bg-midnight-800 hover:bg-midnight-700 border border-slate-700 flex items-center gap-1.5 transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Verify Another</span>
            </button>
          </div>
        </div>
      </div>

      {/* Notice Metadata & Overview */}
      <div className="p-6 border-b border-slate-800/80 bg-midnight-900/50">
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
          <Fingerprint className="w-4 h-4 text-cyan-400" />
          <span>Notice Metadata & Registry Ledger</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-lg bg-midnight-950/60 border border-slate-800">
            <span className="text-[11px] text-slate-400 block mb-1">Official Notice ID</span>
            <span className="font-mono text-sm font-bold text-white break-all">
              {notice.id}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-midnight-950/60 border border-slate-800">
            <span className="text-[11px] text-slate-400 block mb-1 flex items-center gap-1">
              <Building className="w-3 h-3 text-cyan-400" /> Issuing Department
            </span>
            <span className="text-xs font-semibold text-slate-200">
              {notice.department}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-midnight-950/60 border border-slate-800">
            <span className="text-[11px] text-slate-400 block mb-1 flex items-center gap-1">
              <User className="w-3 h-3 text-cyan-400" /> Authorized Signatory
            </span>
            <span className="text-xs font-semibold text-slate-200">
              {notice.issuer}
            </span>
          </div>

          <div className="p-3.5 rounded-lg bg-midnight-950/60 border border-slate-800">
            <span className="text-[11px] text-slate-400 block mb-1 flex items-center gap-1">
              <Calendar className="w-3 h-3 text-cyan-400" /> Date of Issuance
            </span>
            <span className="text-xs font-mono text-slate-200">
              {formatDate(notice.issueDate)}
            </span>
          </div>
        </div>

        {/* Circular Title Banner */}
        <div className="mt-4 p-4 rounded-lg bg-midnight-950 border border-slate-800">
          <span className="text-[11px] uppercase font-mono text-cyan-400 block mb-1">
            Registered Document Title
          </span>
          <p className="text-base font-semibold text-white">
            {notice.title}
          </p>
          {notice.contentSnippet && (
            <p className="text-xs text-slate-400 mt-2 font-mono bg-midnight-900/80 p-2.5 rounded border border-slate-800/80">
              "{notice.contentSnippet}"
            </p>
          )}
        </div>
      </div>

      {/* Forensic Diagnostics Grid */}
      <div className="p-6 space-y-6">
        <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          <span>Forensic Verification Diagnostic Matrix</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          
          {/* Card 1: Cryptographic Authentication */}
          <div className="p-4 rounded-xl bg-midnight-950/80 border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-300">1. Cryptographic Seal</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                audit.cryptographicSignature === 'VALID_MATCH'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-700/50'
                  : audit.cryptographicSignature === 'INDIRECT_MATCH'
                  ? 'bg-amber-950 text-amber-400 border border-amber-700/50'
                  : 'bg-red-950 text-red-400 border border-red-700/50'
              }`}>
                {audit.cryptographicSignature || 'N/A'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Algorithm: <span className="font-mono text-slate-300">{audit.signatureAlgorithm || 'None'}</span>
            </p>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              Integrity check validates against authorized college public keys.
            </p>
          </div>

          {/* Card 2: Digital Watermark & Steganography */}
          <div className="p-4 rounded-xl bg-midnight-950/80 border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-300">2. Watermark Survivability</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                audit.watermarkIntegrity === 'INTACT'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-700/50'
                  : audit.watermarkIntegrity === 'DEGRADED_BY_COMPRESSION'
                  ? 'bg-amber-950 text-amber-400 border border-amber-700/50'
                  : 'bg-red-950 text-red-400 border border-red-700/50'
              }`}>
                {audit.watermarkIntegrity || 'ABSENT'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Pattern: <span className="font-mono text-slate-300">{audit.watermarkDetected ? 'Detected' : 'Not Found'}</span>
            </p>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              Steganographic spatial watermark resilient to messaging crops.
            </p>
          </div>

          {/* Card 3: Pixel Forensics */}
          <div className="p-4 rounded-xl bg-midnight-950/80 border border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-300">3. Pixel Forensics & Noise</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                audit.pixelForensics === 'CLEAN_NO_ALTERATION'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-700/50'
                  : audit.pixelForensics === 'JPEG_COMPRESSION_ARTIFACTS_ONLY'
                  ? 'bg-amber-950 text-amber-400 border border-amber-700/50'
                  : 'bg-red-950 text-red-400 border border-red-700/50'
              }`}>
                {audit.pixelForensics || 'UNCHECKED'}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Metadata: <span className="font-mono text-slate-300">{audit.metadataIntegrity || 'None'}</span>
            </p>
            <p className="text-xs text-slate-500 mt-1 font-mono">
              Error Level Analysis (ELA) scans for font splicing & cloned regions.
            </p>
          </div>

        </div>

        {/* Detected Anomalies (if any) */}
        {audit.detectedAnomalies && audit.detectedAnomalies.length > 0 && (
          <div className="p-4 rounded-xl bg-midnight-950 border border-slate-800">
            <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-amber-400 mb-2 flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" />
              <span>Forensic Anomaly Log</span>
            </h4>
            <ul className="space-y-1.5">
              {audit.detectedAnomalies.map((anomaly, idx) => (
                <li key={idx} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="text-amber-400 font-mono mt-0.5">•</span>
                  <span>{anomaly}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Verdict Summary Box */}
        <div className="p-4 rounded-xl bg-midnight-950/90 border border-cyan-500/20 text-xs text-slate-300 leading-relaxed">
          <strong className="text-cyan-400 font-mono block mb-1">Forensic Analysis Summary:</strong>
          {audit.verdictSummary}
        </div>

      </div>

      {/* Footer Actions */}
      <div className="p-4 bg-midnight-950 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
        <div className="font-mono">
          Audit Ref: <span className="text-slate-300">{notice.id}-VER-{Date.now().toString().slice(-6)}</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => window.print()}
            className="px-3.5 py-1.5 rounded-lg text-slate-300 hover:text-white bg-midnight-800 hover:bg-midnight-700 border border-slate-700 flex items-center gap-1.5 transition-all"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span>Export / Print Certificate</span>
          </button>
          <button
            onClick={onReset}
            className="px-3.5 py-1.5 rounded-lg text-cyan-300 hover:text-cyan-200 bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-600/40 flex items-center gap-1.5 transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Verify Another Document</span>
          </button>
        </div>
      </div>

    </div>
  );
};

export default VerificationResult;

