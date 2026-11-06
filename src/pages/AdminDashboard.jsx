import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Plus, 
  Search, 
  Filter, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Eye, 
  Activity, 
  Layers,
  X,
  Clock,
  RefreshCw,
  WifiOff,
  Inbox
} from 'lucide-react';
import { noticeService } from '../services/noticeService';

const AdminDashboard = () => {
  const [notices, setNotices] = useState([]);
  const [stats, setStats] = useState({
    totalNotices: 0,
    publishedNotices: 0,
    flaggedTamperedAttempts: 0,
    activeVerificationsToday: 0,
  });
  const [recentActivities, setRecentActivities] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedNotice, setSelectedNotice] = useState(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [backendError, setBackendError] = useState('');

  // Form state for Create Notice Modal
  const [newNoticeTitle, setNewNoticeTitle] = useState('');
  const [newNoticeDept, setNewNoticeDept] = useState('Academic Affairs');
  const [noticeFile, setNoticeFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createNoticeMsg, setCreateNoticeMsg] = useState({ type: '', text: '' });

  useEffect(() => {
    fetchDashboardData();
  }, [searchTerm, statusFilter]);

  const fetchDashboardData = async () => {
    setIsLoading(true);
    setBackendError('');
    try {
      const response = await noticeService.getNotices({
        search: searchTerm,
        status: statusFilter,
      });
      setNotices(response.items || []);
      setStats(response.stats || {
        totalNotices: 0,
        publishedNotices: 0,
        flaggedTamperedAttempts: 0,
        activeVerificationsToday: 0,
      });
      setRecentActivities(response.recentActivities || []);
    } catch (err) {
      setBackendError(
        err.message || 'Backend connection pending. Unable to load notices from server.'
      );
      setNotices([]);
      setStats({
        totalNotices: 0,
        publishedNotices: 0,
        flaggedTamperedAttempts: 0,
        activeVerificationsToday: 0,
      });
      setRecentActivities([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateNotice = async (e) => {
    e.preventDefault();
    if (!newNoticeTitle.trim()) return;

    setIsSubmitting(true);
    setCreateNoticeMsg({ type: '', text: '' });

    const formData = new FormData();
    formData.append('title', newNoticeTitle.trim());
    formData.append('department', newNoticeDept);
    if (noticeFile) {
      formData.append('file', noticeFile);
    }

    try {
      await noticeService.createNotice(formData);
      setCreateNoticeMsg({
        type: 'success',
        text: 'Notice successfully published and cryptographically signed.',
      });
      setTimeout(() => {
        setCreateModalOpen(false);
        setNewNoticeTitle('');
        setNoticeFile(null);
        setCreateNoticeMsg({ type: '', text: '' });
        fetchDashboardData();
      }, 1500);
    } catch (err) {
      setCreateNoticeMsg({
        type: 'error',
        text: err.message || 'Failed to publish notice. Backend connection pending.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'VERIFIED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-emerald-950 text-emerald-400 border border-emerald-800/60">
            <CheckCircle2 className="w-3 h-3" />
            <span>VERIFIED</span>
          </span>
        );
      case 'TAMPERING_DETECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-red-950 text-red-400 border border-red-800/60">
            <AlertTriangle className="w-3 h-3" />
            <span>TAMPERED</span>
          </span>
        );
      case 'AUTHENTIC_TRANSFORMED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-amber-950 text-amber-400 border border-amber-800/60">
            <Layers className="w-3 h-3" />
            <span>TRANSFORMED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium bg-slate-800 text-slate-300 border border-slate-700">
            <XCircle className="w-3 h-3" />
            <span>UNVERIFIABLE</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      
      {/* Dashboard Top Header & CTA */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Institutional Registry & Notice Management
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Publish official college circulars, monitor cryptographic signatures, and audit verification requests.
          </p>
        </div>

        <button
          onClick={() => setCreateModalOpen(true)}
          className="px-4 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider bg-cyan-500 hover:bg-cyan-400 text-midnight-950 shadow-cyber-sm flex items-center gap-2 transition-all shrink-0"
        >
          <Plus className="w-4 h-4 stroke-[3]" />
          <span>Publish Notice</span>
        </button>
      </div>

      {/* Backend Status / Connection Banner */}
      {backendError && (
        <div className="p-4 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <WifiOff className="w-4 h-4 text-amber-400 shrink-0" />
            <span>{backendError}</span>
          </div>
          <button
            onClick={fetchDashboardData}
            className="px-3 py-1.5 rounded-lg bg-midnight-900 hover:bg-midnight-800 border border-amber-500/40 text-amber-300 hover:text-white text-xs font-mono flex items-center gap-1.5 self-start sm:self-center transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Connection</span>
          </button>
        </div>
      )}

      {/* 1. OVERVIEW CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* Card 1: Total Notices */}
        <div className="cyber-card p-5 bg-midnight-900/90 border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider">Total Notices</span>
            <FileText className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-white font-mono">
            {stats.totalNotices}
          </div>
          <span className="text-[11px] text-slate-500 font-mono mt-1 block">
            Indexed in college registry
          </span>
        </div>

        {/* Card 2: Published Notices */}
        <div className="cyber-card p-5 bg-midnight-900/90 border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider">Published & Sealed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black text-emerald-400 font-mono">
            {stats.publishedNotices}
          </div>
          <span className="text-[11px] text-emerald-500/80 font-mono mt-1 block">
            Cryptographically signed
          </span>
        </div>

        {/* Card 3: Tampering Alerts */}
        <div className="cyber-card p-5 bg-midnight-900/90 border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider">Tamper Detections</span>
            <AlertTriangle className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-black text-red-400 font-mono">
            {stats.flaggedTamperedAttempts}
          </div>
          <span className="text-[11px] text-red-400/80 font-mono mt-1 block">
            Flagged anomalous queries
          </span>
        </div>

        {/* Card 4: Daily Verifications */}
        <div className="cyber-card p-5 bg-midnight-900/90 border-slate-800">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider">Today's Audits</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-black text-cyan-400 font-mono">
            {stats.activeVerificationsToday}
          </div>
          <span className="text-[11px] text-slate-500 font-mono mt-1 block">
            Processed verifications
          </span>
        </div>

      </div>

      {/* 2. NOTICE MANAGEMENT TABLE & FILTERS */}
      <div className="cyber-card overflow-hidden bg-midnight-900/90 border-slate-800">
        
        {/* Table Controls Header */}
        <div className="p-5 border-b border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white">
              Official Notices Registry
            </h2>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-midnight-800 text-slate-300 border border-slate-700">
              {notices.length} Records
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
            {/* Search Input */}
            <div className="relative w-full sm:w-64">
              <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search title, ID, dept..."
                className="w-full pl-9 pr-3 py-2 rounded-lg bg-midnight-950 border border-slate-800 focus:border-cyan-400 text-xs text-white placeholder-slate-500 font-mono focus:outline-none"
              />
            </div>

            {/* Filter Dropdown */}
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <Filter className="w-4 h-4 text-slate-500 shrink-0" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full sm:w-auto px-3 py-2 rounded-lg bg-midnight-950 border border-slate-800 text-xs text-slate-300 font-mono focus:outline-none focus:border-cyan-400"
              >
                <option value="ALL">All Statuses</option>
                <option value="VERIFIED">Verified</option>
                <option value="TAMPERING_DETECTED">Tampered</option>
                <option value="AUTHENTIC_TRANSFORMED">Transformed</option>
                <option value="UNVERIFIABLE">Unverifiable</option>
              </select>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-midnight-950/80 text-slate-400 uppercase font-mono border-b border-slate-800 text-[11px]">
              <tr>
                <th className="px-5 py-3.5">Notice ID</th>
                <th className="px-5 py-3.5">Document Title</th>
                <th className="px-5 py-3.5">Department</th>
                <th className="px-5 py-3.5">Issuance Date</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center gap-2">
                      <RefreshCw className="w-5 h-5 text-cyan-400 animate-spin" />
                      <span className="font-mono text-xs">Loading institutional notices...</span>
                    </div>
                  </td>
                </tr>
              ) : notices.length > 0 ? (
                notices.map((n) => (
                  <tr key={n.id} className="hover:bg-midnight-850/60 transition-colors">
                    <td className="px-5 py-4 font-mono font-bold text-white whitespace-nowrap">
                      {n.id}
                    </td>
                    <td className="px-5 py-4 max-w-xs sm:max-w-md">
                      <div className="font-semibold text-white truncate">{n.title}</div>
                      {n.fileName && <div className="text-[11px] text-slate-400 truncate">{n.fileName}</div>}
                    </td>
                    <td className="px-5 py-4 text-slate-400 whitespace-nowrap">
                      {n.department}
                    </td>
                    <td className="px-5 py-4 text-slate-400 font-mono whitespace-nowrap">
                      {n.issueDate && n.issueDate !== 'Unknown' ? new Date(n.issueDate).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-5 py-4 whitespace-nowrap">
                      {getStatusBadge(n.status)}
                    </td>
                    <td className="px-5 py-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => setSelectedNotice(n)}
                        className="px-3 py-1.5 rounded bg-midnight-800 hover:bg-midnight-700 border border-slate-700 text-cyan-300 hover:text-cyan-200 text-xs font-mono inline-flex items-center gap-1.5 transition-all"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect</span>
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                /* Empty state */
                <tr>
                  <td colSpan={6} className="px-5 py-14 text-center text-slate-400">
                    <div className="flex flex-col items-center justify-center space-y-2">
                      <div className="w-12 h-12 rounded-xl bg-midnight-950 border border-slate-800 flex items-center justify-center text-slate-500">
                        <Inbox className="w-6 h-6" />
                      </div>
                      <h4 className="text-sm font-semibold text-slate-200">No notices available</h4>
                      <p className="text-xs text-slate-400 max-w-sm">
                        {searchTerm || statusFilter !== 'ALL'
                          ? 'No notices match the selected search or filter criteria.'
                          : 'No notices have been published to the registry yet.'}
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

      </div>

      {/* 3. RECENT ACTIVITY LOG */}
      <div className="cyber-card p-5 bg-midnight-900/90 border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-bold text-white font-mono uppercase tracking-wider">
              Verification History Stream
            </h3>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">Live Audit Events</span>
        </div>

        {recentActivities.length > 0 ? (
          <div className="space-y-2.5">
            {recentActivities.map((act) => (
              <div
                key={act.id}
                className="p-3 rounded-lg bg-midnight-950/70 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
              >
                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-mono text-slate-400 shrink-0">{act.time}</span>
                  <span className="text-slate-200 font-medium">{act.action}</span>
                </div>
                <div className="flex items-center gap-2 self-start sm:self-center">
                  {act.ip && <span className="text-[11px] font-mono text-slate-400">IP: {act.ip}</span>}
                  {getStatusBadge(act.result)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Empty state for activities */
          <div className="p-8 text-center rounded-lg bg-midnight-950/60 border border-slate-800/60">
            <p className="text-xs text-slate-400 font-mono">No verification history yet</p>
            <p className="text-[11px] text-slate-400 mt-1">
              Events will record automatically when students verify notices via the verification engine.
            </p>
          </div>
        )}
      </div>

      {/* MODAL: Notice Inspector */}
      {selectedNotice && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-midnight-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="cyber-card w-full max-w-2xl bg-midnight-900 border-cyan-500/40 p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2 font-mono">
                <span className="text-sm font-bold text-white">Notice Record Details</span>
                <span className="text-xs text-cyan-400">[{selectedNotice.id}]</span>
              </div>
              <button
                onClick={() => setSelectedNotice(null)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-slate-400 block mb-0.5">Title:</span>
                <p className="text-sm font-semibold text-white">{selectedNotice.title}</p>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 rounded bg-midnight-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Department</span>
                  <span className="text-slate-200 font-medium">{selectedNotice.department}</span>
                </div>
                <div className="p-3 rounded bg-midnight-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Signatory</span>
                  <span className="text-slate-200 font-medium">{selectedNotice.issuer || 'Institutional Signatory'}</span>
                </div>
              </div>

              {selectedNotice.securityAudit?.sha256Digest && (
                <div className="p-3 rounded bg-midnight-950 border border-slate-800 space-y-1">
                  <span className="text-slate-400 block">Cryptographic Hash Digest:</span>
                  <p className="font-mono text-[11px] text-cyan-300 break-all">
                    {selectedNotice.securityAudit.sha256Digest}
                  </p>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedNotice(null)}
                className="px-4 py-2 rounded-lg bg-midnight-800 hover:bg-midnight-700 text-xs font-semibold text-slate-200 border border-slate-700"
              >
                Close Record
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Create Notice Modal */}
      {createModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-midnight-950/80 backdrop-blur-sm animate-fadeIn">
          <div className="cyber-card w-full max-w-lg bg-midnight-900 border-cyan-500/40 p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Plus className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white font-mono uppercase">
                  Publish Notice & Sign Cryptographically
                </h3>
              </div>
              <button
                onClick={() => setCreateModalOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateNotice} className="space-y-4 text-xs">
              <div>
                <label className="block text-slate-300 font-mono mb-1">Notice Title / Subject</label>
                <input
                  type="text"
                  required
                  value={newNoticeTitle}
                  onChange={(e) => setNewNoticeTitle(e.target.value)}
                  placeholder="e.g. Schedule of Re-evaluation for Odd Semester"
                  className="w-full px-3 py-2 rounded-lg bg-midnight-950 border border-slate-700 text-white focus:outline-none focus:border-cyan-400"
                />
              </div>

              <div>
                <label className="block text-slate-300 font-mono mb-1">Issuing Department</label>
                <select
                  value={newNoticeDept}
                  onChange={(e) => setNewNoticeDept(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-midnight-950 border border-slate-700 text-white focus:outline-none focus:border-cyan-400"
                >
                  <option value="Academic Affairs">Academic Affairs & Examinations</option>
                  <option value="Finance">Finance & Student Accounts</option>
                  <option value="Registrar">Office of the University Registrar</option>
                  <option value="Dean Students">Dean of Student Welfare</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 font-mono mb-1">Official Document File (PDF / Image)</label>
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setNoticeFile(e.target.files[0] || null)}
                  className="w-full px-3 py-2 rounded-lg bg-midnight-950 border border-slate-700 text-slate-300 file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-cyan-950 file:text-cyan-300"
                />
              </div>

              {createNoticeMsg.text && (
                <div className={`p-3 rounded text-xs ${
                  createNoticeMsg.type === 'success'
                    ? 'bg-emerald-950/60 border border-emerald-500/40 text-emerald-300'
                    : 'bg-red-950/60 border border-red-500/40 text-red-300'
                }`}>
                  {createNoticeMsg.text}
                </div>
              )}

              <div className="pt-3 border-t border-slate-800 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setCreateModalOpen(false)}
                  className="px-4 py-2 rounded-lg bg-midnight-800 text-slate-300 hover:bg-midnight-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-midnight-950 font-bold uppercase tracking-wider"
                >
                  {isSubmitting ? 'Signing & Publishing...' : 'Publish & Sign Notice'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default AdminDashboard;
