import React, { useState, useRef } from 'react';
import { 
  UploadCloud, 
  FileText, 
  Image as ImageIcon, 
  X, 
  AlertCircle, 
  CheckCircle2,
  FileCheck
} from 'lucide-react';

const ALLOWED_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'image/jpg'
];

const MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024; // 15 MB

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const FileUpload = ({ selectedFile, onFileSelect, onFileRemove }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  const validateAndSetFile = (file) => {
    setErrorMsg('');

    if (!file) return;

    // Validate type
    if (!ALLOWED_TYPES.includes(file.type)) {
      setErrorMsg('Invalid file format. Please upload an official notice in PDF, PNG, or JPG format.');
      return;
    }

    // Validate size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setErrorMsg(`File exceeds size limit of 15 MB (${formatBytes(file.size)}).`);
      return;
    }

    // Create thumbnail preview if image
    if (file.type.startsWith('image/')) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }

    onFileSelect(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  const handleRemove = (e) => {
    e.stopPropagation();
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    setErrorMsg('');
    onFileRemove();
  };

  const isPdf = selectedFile && selectedFile.type === 'application/pdf';

  return (
    <div className="w-full space-y-3">
      {/* Hidden native input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        onChange={handleInputChange}
        className="hidden"
        id="notice-file-input"
      />

      {!selectedFile ? (
        /* Drag & Drop Zone */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-10 text-center cursor-pointer transition-all duration-200 group ${
            isDragging
              ? 'border-cyan-400 bg-cyan-950/30 shadow-cyber-md scale-[1.01]'
              : 'border-slate-700/80 hover:border-cyan-500/50 bg-midnight-900/60 hover:bg-midnight-850/60'
          }`}
        >
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-midnight-800 border border-slate-700 flex items-center justify-center text-cyan-400 group-hover:scale-105 group-hover:border-cyan-500/50 transition-all duration-300">
              <UploadCloud className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <p className="text-base font-medium text-white">
                Drag and drop your circular / notice here
              </p>
              <p className="text-xs text-slate-400">
                Supports official documents, WhatsApp forwards, screenshots, and scans
              </p>
            </div>

            <div className="pt-2">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                className="px-5 py-2.5 rounded-lg text-xs font-semibold uppercase tracking-wider text-cyan-300 bg-cyan-950/60 border border-cyan-500/40 hover:bg-cyan-900/40 hover:border-cyan-400 transition-all shadow-sm"
              >
                Browse Files
              </button>
            </div>

            <div className="flex items-center gap-4 text-slate-400 text-xs pt-2">
              <span className="flex items-center gap-1 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span> PDF
              </span>
              <span className="flex items-center gap-1 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span> PNG
              </span>
              <span className="flex items-center gap-1 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span> JPG / JPEG
              </span>
              <span className="text-slate-500 font-mono">Max: 15 MB</span>
            </div>
          </div>
        </div>
      ) : (
        /* Selected File Card */
        <div className="cyber-card p-5 border-cyan-500/40 bg-midnight-900/90 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4 w-full sm:w-auto">
            {previewUrl ? (
              <div className="relative w-14 h-14 rounded-lg overflow-hidden border border-slate-700 bg-midnight-950 shrink-0">
                <img src={previewUrl} alt="Document Preview" className="w-full h-full object-cover" />
              </div>
            ) : (
              <div className="w-14 h-14 rounded-lg bg-midnight-800 border border-slate-700 flex items-center justify-center text-cyan-400 shrink-0">
                {isPdf ? <FileText className="w-7 h-7 text-red-400" /> : <ImageIcon className="w-7 h-7" />}
              </div>
            )}

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-semibold text-white truncate max-w-xs sm:max-w-md">
                  {selectedFile.name}
                </h4>
                <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono bg-cyan-950 text-cyan-400 border border-cyan-800/60 uppercase">
                  {isPdf ? 'PDF DOC' : 'IMAGE'}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                {formatBytes(selectedFile.size)} • Ready for forensic verification
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={handleRemove}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-red-400 hover:bg-red-950/30 border border-slate-700 hover:border-red-800/60 transition-all flex items-center gap-1.5"
            >
              <X className="w-4 h-4" />
              <span>Remove</span>
            </button>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {errorMsg && (
        <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-500/50 text-red-300 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
          <span>{errorMsg}</span>
        </div>
      )}
    </div>
  );
};

export default FileUpload;

