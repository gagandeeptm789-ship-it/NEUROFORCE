import React, { useState } from 'react';
import { QrCode, X, Camera, ArrowRight, ShieldCheck } from 'lucide-react';

const QRScannerModal = ({ isOpen, onClose, onScanSuccess }) => {
  const [manualCode, setManualCode] = useState('');

  if (!isOpen) return null;

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (manualCode.trim()) {
      onScanSuccess(manualCode.trim());
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-midnight-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="cyber-card w-full max-w-lg border-cyan-500/40 bg-midnight-900 shadow-cyber-md overflow-hidden">
        
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-midnight-950">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <QrCode className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white font-mono">
                QR CODE OPTICAL SCANNER
              </h3>
              <p className="text-[11px] text-slate-400">
                Institutional Document Optical Reader
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-midnight-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Camera Viewfinder */}
        <div className="p-6 flex flex-col items-center">
          <div className="relative w-64 h-64 sm:w-72 sm:h-72 rounded-2xl bg-midnight-950 border-2 border-slate-700 flex items-center justify-center overflow-hidden">
            
            {/* Viewfinder Corner Brackets */}
            <div className="absolute top-3 left-3 w-6 h-6 border-t-2 border-l-2 border-cyan-400"></div>
            <div className="absolute top-3 right-3 w-6 h-6 border-t-2 border-r-2 border-cyan-400"></div>
            <div className="absolute bottom-3 left-3 w-6 h-6 border-b-2 border-l-2 border-cyan-400"></div>
            <div className="absolute bottom-3 right-3 w-6 h-6 border-b-2 border-r-2 border-cyan-400"></div>

            {/* Scanning Laser Beam Animation */}
            <div className="absolute inset-x-4 top-4 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_#00E5FF] animate-scanBeam"></div>

            {/* Center Content */}
            <div className="flex flex-col items-center text-center p-4">
              <Camera className="w-12 h-12 text-slate-600 mb-2 animate-pulseSlow" />
              <p className="text-xs font-mono text-cyan-400">
                ALIGN QR SEAL IN FRAME
              </p>
              <p className="text-[10px] text-slate-400 mt-1 max-w-[200px]">
                Position the camera over the QR watermark printed on the official circular.
              </p>
            </div>
          </div>

          {/* Manual Scanned Data / Code Entry Form */}
          <form onSubmit={handleManualSubmit} className="w-full mt-6 pt-5 border-t border-slate-800 space-y-2">
            <label className="text-[11px] font-mono uppercase text-slate-400 block text-center">
              Direct QR Payload / Decoded Notice ID
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={manualCode}
                onChange={(e) => setManualCode(e.target.value)}
                placeholder="Paste or type decoded QR value..."
                className="flex-1 px-3 py-2 rounded-lg bg-midnight-950 border border-slate-700 text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400"
              />
              <button
                type="submit"
                disabled={!manualCode.trim()}
                className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 text-midnight-950 text-xs font-bold font-mono flex items-center gap-1"
              >
                <span>Apply</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>
        </div>

      </div>
    </div>
  );
};

export default QRScannerModal;
