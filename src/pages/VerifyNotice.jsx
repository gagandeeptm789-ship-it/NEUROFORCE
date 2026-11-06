import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Search, 
  QrCode, 
  FileText, 
  AlertCircle, 
  Loader2, 
  CheckCircle2, 
  HelpCircle,
  WifiOff
} from 'lucide-react';
import FileUpload from '../components/FileUpload';
import VerificationResult from '../components/VerificationResult';
import QRScannerModal from '../components/QRScannerModal';
import { noticeService } from '../services/noticeService';

const VerifyNotice = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [noticeId, setNoticeId] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [validationError, setValidationError] = useState('');
  const [serviceError, setServiceError] = useState('');
  const [qrModalOpen, setQrModalOpen] = useState(false);

  const handleVerify = async () => {
    setValidationError('');
    setServiceError('');
    const targetNoticeId = noticeId.trim();

    if (!selectedFile && !targetNoticeId) {
      setValidationError('Please upload a notice document or enter a valid Notice ID to verify.');
      return;
    }

    setIsVerifying(true);
    setVerificationResult(null);

    try {
      const response = await noticeService.verifyNotice({
        file: selectedFile,
        noticeId: targetNoticeId,
      });

      if (response && response.data) {
        setVerificationResult(response);
      } else {
        setServiceError('No verification record returned by the backend engine.');
      }
    } catch (err) {
      setServiceError(
        err.message || 'Verification service temporarily unavailable. Backend connection pending.'
      );
    } finally {
      setIsVerifying(false);
    }
  };

  const handleQRScanSuccess = (scannedId) => {
    setNoticeId(scannedId);
  };

  const handleReset = () => {
    setSelectedFile(null);
    setNoticeId('');
    setVerificationResult(null);
    setValidationError('');
    setServiceError('');
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 space-y-8">
      
      {/* Page Title & Instructions */}
      <div className="text-center max-w-3xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-950/60 border border-cyan-500/30 text-cyan-300">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>STUDENT VERIFICATION PORTAL</span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
          Verify Official College Circular
        </h1>
        <p className="text-sm text-slate-300 leading-relaxed">
          Upload any official circular, forwarded screenshot, or notice PDF received via messaging platforms. The verification engine validates issuing credentials and identifies forensic alterations.
        </p>
      </div>

      {/* Results View (Only displayed upon receiving a valid backend verification response) */}
      {verificationResult ? (
        <VerificationResult result={verificationResult} onReset={handleReset} />
      ) : (
        /* Verification Input Form */
        <div className="space-y-6">
          
          {/* Main Card */}
          <div className="cyber-card p-6 sm:p-8 bg-midnight-900/90 border-slate-800">
            
            {/* Method 1: File Upload */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <FileText className="w-4 h-4 text-cyan-400" />
                  <span>Method 1: Upload Notice Document or Screenshot</span>
                </label>
                <span className="text-[11px] text-slate-400 font-mono">PDF, PNG, JPG (Max 15MB)</span>
              </div>

              <FileUpload
                selectedFile={selectedFile}
                onFileSelect={(file) => {
                  setSelectedFile(file);
                  setValidationError('');
                  setServiceError('');
                }}
                onFileRemove={() => setSelectedFile(null)}
              />
            </div>

            {/* Divider OR */}
            <div className="relative my-8 text-center">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-800"></div>
              </div>
              <span className="relative px-4 text-xs font-mono uppercase tracking-wider bg-midnight-900 text-slate-400">
                OR VERIFY BY UNIQUE NOTICE ID / QR CODE
              </span>
            </div>

            {/* Method 2: Notice ID & QR Scan */}
            <div className="space-y-3">
              <label className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <Search className="w-4 h-4 text-cyan-400" />
                <span>Method 2: Enter Notice ID or Scan QR Watermark</span>
              </label>

              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <input
                    type="text"
                    value={noticeId}
                    onChange={(e) => {
                      setNoticeId(e.target.value);
                      setValidationError('');
                      setServiceError('');
                    }}
                    placeholder="Enter Notice ID (e.g., FS-ENG-2026-001)"
                    className="w-full px-4 py-3 rounded-xl bg-midnight-950 border border-slate-700/80 focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400 text-sm font-mono text-white placeholder-slate-500 uppercase tracking-wider transition-all"
                  />
                  {noticeId && (
                    <button
                      type="button"
                      onClick={() => setNoticeId('')}
                      className="absolute right-3 top-3 text-slate-400 hover:text-white text-xs font-mono"
                    >
                      CLEAR
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => setQrModalOpen(true)}
                  className="px-4 py-3 rounded-xl bg-midnight-850 hover:bg-midnight-800 border border-slate-700 hover:border-cyan-500/40 text-xs font-semibold text-slate-200 flex items-center justify-center gap-2 transition-all shrink-0"
                >
                  <QrCode className="w-4 h-4 text-cyan-400" />
                  <span>Scan QR Code</span>
                </button>
              </div>
              <p className="text-[11px] text-slate-400">
                The Notice ID is registered on the institutional ledger and typically printed on the footer of authentic circulars.
              </p>
            </div>

            {/* Validation Error Alert */}
            {validationError && (
              <div className="mt-5 p-3 rounded-lg bg-red-950/40 border border-red-500/50 text-red-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                <span>{validationError}</span>
              </div>
            )}

            {/* Service / Backend Offline Error Alert */}
            {serviceError && (
              <div className="mt-5 p-4 rounded-xl bg-amber-950/40 border border-amber-500/50 text-amber-200 text-xs space-y-1">
                <div className="flex items-center gap-2 font-semibold text-amber-300">
                  <WifiOff className="w-4 h-4 shrink-0 text-amber-400" />
                  <span>Service Temporarily Unavailable / Backend Pending</span>
                </div>
                <p className="text-slate-300 pl-6 leading-relaxed">
                  {serviceError}
                </p>
              </div>
            )}

            {/* Verification Button */}
            <div className="mt-8 pt-6 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-slate-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                <span>Cryptographic integrity check via backend verification API</span>
              </div>

              <button
                type="button"
                onClick={handleVerify}
                disabled={isVerifying}
                className="w-full sm:w-auto px-8 py-3.5 rounded-xl font-bold text-sm tracking-wide bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-midnight-950 shadow-cyber-md flex items-center justify-center gap-2 transition-all transform hover:scale-[1.01]"
              >
                {isVerifying ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-midnight-950" />
                    <span>Connecting to Verification Engine...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4 stroke-[2.5]" />
                    <span>Verify Notice Authenticity</span>
                  </>
                )}
              </button>
            </div>

          </div>

          {/* Verification Guidelines / Help Box */}
          <div className="p-4 rounded-xl bg-midnight-950 border border-slate-800 text-xs text-slate-400 space-y-2">
            <h4 className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
              <HelpCircle className="w-4 h-4 text-cyan-400" />
              <span>Guidelines for Verification:</span>
            </h4>
            <ul className="list-disc pl-5 space-y-1 text-slate-400">
              <li>Ensure the notice text and margins containing institutional identifiers are clear and readable.</li>
              <li>Verification results require an active connection to the institutional FastAPI backend.</li>
              <li>Only notices registered in the official college ledger can be cryptographically verified.</li>
            </ul>
          </div>

        </div>
      )}

      {/* QR Scanner Modal */}
      <QRScannerModal
        isOpen={qrModalOpen}
        onClose={() => setQrModalOpen(false)}
        onScanSuccess={handleQRScanSuccess}
      />

    </div>
  );
};

export default VerifyNotice;
