import React, { useState, useEffect } from 'react';
import { 
  Play, Video, Sparkles, Send, BarChart3, RefreshCw, Eye, 
  Clock, ShieldCheck, Film, Copy, Check, ExternalLink, Calendar, 
  Sliders, Mic, Layers, ArrowUpRight, Flame, AlertCircle, X, ChevronRight, ChevronLeft, Trash2, Cpu, Key,
  Upload, FileText, CheckCircle2, Download, Zap, Info
} from 'lucide-react';

function formatScheduleDate(isoStr) {
  if (!isoStr) return "Scheduled on YouTube";
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' · ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
  } catch {
    return isoStr;
  }
}

function Pagination({
  currentPage,
  totalItems,
  perPage,
  onPageChange,
  onPerPageChange,
  perPageOptions = [5, 10, 20, 50],
}) {
  const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
  const safePage = Math.min(Math.max(1, currentPage), totalPages);
  const startItem = totalItems === 0 ? 0 : (safePage - 1) * perPage + 1;
  const endItem = Math.min(totalItems, safePage * perPage);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 bg-slate-900/60 border-t border-slate-800/80 text-xs">
      <div className="flex items-center space-x-3 text-slate-400">
        <span>
          Showing <span className="font-mono font-bold text-white">{startItem}</span> - <span className="font-mono font-bold text-white">{endItem}</span> of <span className="font-mono font-bold text-white">{totalItems}</span>
        </span>
        <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-800">
          <span className="text-slate-400">Per page:</span>
          <select
            value={perPage}
            onChange={(e) => {
              onPerPageChange(Number(e.target.value));
              onPageChange(1);
            }}
            className="bg-slate-950 border border-slate-800 text-slate-200 rounded-lg px-2 py-1 outline-none font-mono focus:border-violet-500 cursor-pointer transition text-xs"
          >
            {perPageOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <span className="text-slate-400 font-mono text-xs pr-1">
          Page {safePage} of {totalPages}
        </span>
        <button
          onClick={() => onPageChange(Math.max(1, safePage - 1))}
          disabled={safePage <= 1}
          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 transition"
          title="Previous Page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        <div className="flex items-center space-x-1">
          {Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter((p) => p === 1 || p === totalPages || Math.abs(p - safePage) <= 1)
            .reduce((acc, p, idx, arr) => {
              if (idx > 0 && p - arr[idx - 1] > 1) {
                acc.push({ type: 'ellipsis', key: `ell-${p}` });
              }
              acc.push({ type: 'page', page: p, key: `page-${p}` });
              return acc;
            }, [])
            .map((item) =>
              item.type === 'ellipsis' ? (
                <span key={item.key} className="px-1 text-slate-600 font-mono">...</span>
              ) : (
                <button
                  key={item.key}
                  onClick={() => onPageChange(item.page)}
                  className={`min-w-[28px] h-7 px-2 rounded-lg font-mono font-bold transition text-xs ${
                    safePage === item.page
                      ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30'
                      : 'bg-slate-800/60 hover:bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  {item.page}
                </button>
              )
            )}
        </div>

        <button
          onClick={() => onPageChange(Math.min(totalPages, safePage + 1))}
          disabled={safePage >= totalPages}
          className="p-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed text-slate-300 transition"
          title="Next Page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function AuthScreen({ onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Email and password are required');
      return;
    }

    if (isRegister) {
      if (password.length < 6) {
        setError('Password must be at least 6 characters');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        return;
      }
    }

    setLoading(true);
    try {
      const endpoint = isRegister ? '/api/auth/register' : '/api/auth/login';
      const payload = isRegister ? { email, password, name } : { email, password };
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || (isRegister ? 'Registration failed' : 'Invalid email or password'));
      }
      onAuthSuccess(data.access_token, data.user);
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090e] flex items-center justify-center p-4 relative overflow-hidden font-sans">
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none"></div>

      <div className="w-full max-w-md relative z-10">
        <div className="bg-[#0d0d14]/90 border border-slate-800/80 rounded-2xl p-8 shadow-2xl backdrop-blur-xl">
          <div className="flex flex-col items-center text-center mb-6">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-violet-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/30 mb-3">
              <Film className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              SHADOWMIND STUDIO
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              YouTube Shorts Automation Engine • NestJS Protected
            </p>
          </div>

          <div className="grid grid-cols-2 gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800/80 mb-6">
            <button
              type="button"
              onClick={() => { setIsRegister(false); setError(''); }}
              className={`py-2 text-xs font-mono font-bold rounded-lg transition-all ${
                !isRegister 
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setIsRegister(true); setError(''); }}
              className={`py-2 text-xs font-mono font-bold rounded-lg transition-all ${
                isRegister 
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30' 
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Create Account
            </button>
          </div>

          {error && (
            <div className="mb-4 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-400 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1.5">Creator Name (Optional)</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. ShadowMind Creator"
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 font-mono"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1.5">Email Address</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="creator@shadowmind.studio"
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-mono text-slate-300 mb-1.5">Password</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 font-mono"
              />
            </div>

            {isRegister && (
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1.5">Confirm Password</label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-violet-500 focus:outline-none focus:ring-1 focus:ring-violet-500 font-mono"
                />
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 rounded-xl bg-gradient-to-r from-violet-600 via-purple-600 to-cyan-500 py-3 text-xs font-mono font-bold text-white shadow-lg shadow-violet-600/30 hover:opacity-95 transition-opacity disabled:opacity-50"
            >
              {loading ? 'AUTHENTICATING...' : isRegister ? 'CREATE ACCOUNT & ACCESS STUDIO' : 'SIGN IN TO SHADOWMIND STUDIO'}
            </button>
          </form>

          <div className="mt-6 pt-4 border-t border-slate-800/80 text-center">
            <span className="text-[11px] font-mono text-slate-500 flex items-center justify-center gap-1.5">
              <span>🔒</span> Secured by NestJS Auth Gateway & JWT
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  // Authentication State
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('yt_studio_jwt') || '');
  const [currentUser, setCurrentUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

  // Modern Toast Notification System
  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3800);
  };

  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState(null);
  const [videos, setVideos] = useState([]);
  const [niches, setNiches] = useState([]);
  const [loadingStats, setLoadingStats] = useState(false);
  
  // Selected video for modal player
  const [previewVideo, setPreviewVideo] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  // Idea Lab state
  const [selectedNiche, setSelectedNiche] = useState('dark_psychology');
  const [ideaConcept, setIdeaConcept] = useState('');
  const [generatingIdea, setGeneratingIdea] = useState(false);
  const [generatedIdea, setGeneratedIdea] = useState(null);

  // Studio Production State
  const [studioVideoId, setStudioVideoId] = useState('short_08');
  const [studioVoice, setStudioVoice] = useState('en-US-ChristopherNeural');
  const [studioScript, setStudioScript] = useState('');
  const [studioKeywords, setStudioKeywords] = useState('mystery, shadows, thinking, city, dark');
  const [studioTitle, setStudioTitle] = useState('');
  const [studioDesc, setStudioDesc] = useState('');
  const [studioComment, setStudioComment] = useState('What do you think of this psychological truth? Comment below. 👇');
  const [activeTaskId, setActiveTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [isProducing, setIsProducing] = useState(false);

  // Dispatcher State
  const [dispatchVideoId, setDispatchVideoId] = useState('');
  const [dispatchMode, setDispatchMode] = useState('public');
  const [dispatchTime, setDispatchTime] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  // Video Vault State
  const [loadingVideos, setLoadingVideos] = useState(false);

  // Daily Quota & Usage Tracker
  const [usage, setUsage] = useState(null);
  const [loadingUsage, setLoadingUsage] = useState(false);

  // AI Flash Model State
  const [aiSettings, setAiSettings] = useState(null);
  const [showAiModal, setShowAiModal] = useState(false);
  const [inputApiKey, setInputApiKey] = useState('');
  const [savingKey, setSavingKey] = useState(false);
  const [aiKeyError, setAiKeyError] = useState('');

  // Channel & YouTube Connection State
  const [showChannelModal, setShowChannelModal] = useState(false);
  const [channelData, setChannelData] = useState({ channel_handle: '', channel_url: '', has_youtube_token: false, has_client_secret: false });
  const [inputChannelHandle, setInputChannelHandle] = useState('');
  const [inputYoutubeToken, setInputYoutubeToken] = useState('');
  const [savingChannel, setSavingChannel] = useState(false);
  const [oauthStep, setOauthStep] = useState('initial'); // 'initial' | 'awaiting_code'
  const [oauthAuthUrl, setOauthAuthUrl] = useState('');
  const [inputOauthCode, setInputOauthCode] = useState('');
  const [exchangingOauth, setExchangingOauth] = useState(false);
  const [uploadingTokenFile, setUploadingTokenFile] = useState(false);
  const [tokenUploadError, setTokenUploadError] = useState('');
  const [showManualJson, setShowManualJson] = useState(false);
  const [showChangeCredentials, setShowChangeCredentials] = useState(false);

  // Table Subtab & Pagination State
  const [tableTab, setTableTab] = useState('live'); // 'live' | 'scheduled' | 'all'
  const [vaultPage, setVaultPage] = useState(1);
  const [vaultPerPage, setVaultPerPage] = useState(6);

  const [tablePage, setTablePage] = useState(1);
  const [tablePerPage, setTablePerPage] = useState(10);

  const allTableVideos = stats?.videos || [];
  const topBreakout = allTableVideos.reduce((max, v) => (v.views > (max?.views || 0) ? v : max), null);
  const topBreakoutViews = topBreakout?.views || 0;
  const topBreakoutLabel = topBreakout && topBreakout.views > 0 ? (topBreakout.short_id?.replace('_', ' ') || 'Short') : 'None yet';

  const filteredTableVideos = allTableVideos
    .filter((v) => {
      if (tableTab === 'live') return v.status === 'LIVE' || v.status === 'PRIVATE' || v.views > 0;
      if (tableTab === 'scheduled') return v.status === 'SCHEDULED' || (v.publish_at && new Date(v.publish_at) > new Date());
      return true;
    })
    .sort((a, b) => {
      if (tableTab === 'scheduled') {
        const dateA = a.publish_at ? new Date(a.publish_at).getTime() : NaN;
        const dateB = b.publish_at ? new Date(b.publish_at).getTime() : NaN;
        const timeA = isNaN(dateA) ? Infinity : dateA;
        const timeB = isNaN(dateB) ? Infinity : dateB;
        if (timeA !== timeB) return timeA - timeB;
        return (a.short_id || '').localeCompare(b.short_id || '');
      }
      return 0;
    });

  // Clamping effects when lists resize
  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(videos.length / vaultPerPage));
    if (vaultPage > maxPage) setVaultPage(maxPage);
  }, [videos.length, vaultPerPage, vaultPage]);

  useEffect(() => {
    const total = filteredTableVideos.length;
    const maxPage = Math.max(1, Math.ceil(total / tablePerPage));
    if (tablePage > maxPage) setTablePage(maxPage);
  }, [filteredTableVideos.length, tablePerPage, tablePage]);

  // Derived Paginated Data
  const paginatedVaultVideos = videos.slice(
    (vaultPage - 1) * vaultPerPage,
    vaultPage * vaultPerPage
  );

  const paginatedTableVideos = filteredTableVideos.slice(
    (tablePage - 1) * tablePerPage,
    tablePage * tablePerPage
  );

  // Authenticated fetch wrapper
  const authFetch = (url, options = {}) => {
    const headers = { ...(options.headers || {}) };
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
    return fetch(url, { ...options, headers }).then(res => {
      if (res.status === 401) {
        localStorage.removeItem('yt_studio_jwt');
        setAuthToken('');
        setCurrentUser(null);
        throw new Error('Unauthorized');
      }
      return res;
    });
  };

  // Keyboard Shortcuts (1-5 Tabs, Escape for Modals)
  useEffect(() => {
    const handleKeyDown = (e) => {
      const tag = e.target.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select' || e.target.isContentEditable) {
        if (e.key === 'Escape') e.target.blur();
        return;
      }
      if (e.key === 'Escape') {
        setPreviewVideo(null);
        setShowAiModal(false);
        setShowChannelModal(false);
      } else if (e.key === '1') {
        setActiveTab('overview');
      } else if (e.key === '2') {
        setActiveTab('vault');
      } else if (e.key === '3') {
        setActiveTab('ideas');
      } else if (e.key === '4') {
        setActiveTab('studio');
      } else if (e.key === '5') {
        setActiveTab('dispatcher');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Check current auth token on mount
  useEffect(() => {
    const token = localStorage.getItem('yt_studio_jwt');
    if (!token) {
      setAuthChecking(false);
      return;
    }
    fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => {
        if (!res.ok) throw new Error('Unauthorized');
        return res.json();
      })
      .then(user => {
        setCurrentUser(user);
        setAuthToken(token);
        setAuthChecking(false);
      })
      .catch(() => {
        localStorage.removeItem('yt_studio_jwt');
        setAuthToken('');
        setCurrentUser(null);
        setAuthChecking(false);
      });
  }, []);

  // Fetch initial data (only when authenticated)
  useEffect(() => {
    if (!authToken) return;
    fetchStats();
    fetchVideos();
    fetchNiches();
    fetchAiSettings();
    fetchChannelSettings();
    fetchUsage();
  }, [authToken]);

  // Poll task status if producing
  useEffect(() => {
    if (!activeTaskId || !isProducing) return;
    const interval = setInterval(async () => {
      try {
        const res = await authFetch(`/api/produce/status/${activeTaskId}`);
        if (res.ok) {
          const data = await res.json();
          setTaskStatus(data);
          if (data.status === 'completed' || data.status === 'failed') {
            setIsProducing(false);
            fetchVideos();
          }
        }
      } catch (err) {
        console.error("Poll error:", err);
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [activeTaskId, isProducing]);

  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const res = await authFetch('/api/stats');
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (e) {
      console.error("Stats fetch error:", e);
    } finally {
      setLoadingStats(false);
    }
  };

  const fetchVideos = async () => {
    setLoadingVideos(true);
    try {
      const res = await authFetch('/api/videos');
      if (res.ok) {
        const data = await res.json();
        setVideos(data);
        if (data.length > 0 && !dispatchVideoId) {
          setDispatchVideoId(data[data.length - 1].id);
        }
      }
    } catch (e) {
      console.error("Videos fetch error:", e);
    } finally {
      setLoadingVideos(false);
    }
  };

  const fetchUsage = async () => {
    setLoadingUsage(true);
    try {
      const [uRes, aiRes] = await Promise.all([
        authFetch('/api/usage'),
        authFetch('/api/settings/ai')
      ]);
      if (uRes.ok) {
        const data = await uRes.json();
        setUsage(data);
      }
      if (aiRes.ok) {
        const aiData = await aiRes.json();
        setAiSettings(aiData);
      }
    } catch (e) {
      console.error("Usage fetch error:", e);
    } finally {
      setTimeout(() => setLoadingUsage(false), 500);
    }
  };

  const fetchNiches = async () => {
    try {
      const res = await authFetch('/api/niches');
      if (res.ok) {
        const data = await res.json();
        setNiches(data);
      }
    } catch (e) {
      console.error("Niches fetch error:", e);
    }
  };

  const fetchAiSettings = async () => {
    try {
      const res = await authFetch('/api/settings/ai');
      if (res.ok) {
        const data = await res.json();
        setAiSettings(data);
      }
    } catch (e) {
      console.error("AI settings fetch error:", e);
    }
  };

  const handleSaveAiKey = async () => {
    if (!inputApiKey.trim()) return;
    setSavingKey(true);
    setAiKeyError('');
    try {
      const res = await authFetch('/api/settings/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: inputApiKey.trim() })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to verify API key with Google.");
      }
      showToast("Gemini Flash API Key verified with Google and saved!", "success");
      setShowAiModal(false);
      setInputApiKey('');
      fetchAiSettings();
      fetchUsage();
    } catch (e) {
      setAiKeyError(e.message);
    } finally {
      setSavingKey(false);
    }
  };

  const handleResetAiKey = async () => {
    if (!confirm("Revert to default pre-configured Gemini Flash key?")) return;
    setSavingKey(true);
    setAiKeyError('');
    try {
      const res = await authFetch('/api/settings/ai', { method: 'DELETE' });
      if (res.ok) {
        fetchAiSettings();
        fetchUsage();
        showToast("Reverted to pre-configured system key.", "info");
      }
    } catch (e) {
      showToast("Error resetting key: " + e.message, "error");
    } finally {
      setSavingKey(false);
    }
  };

  const fetchChannelSettings = async () => {
    try {
      const res = await authFetch('/api/settings/channel');
      if (res && res.ok) {
        const data = await res.json();
        setChannelData(data);
        setInputChannelHandle(data.channel_handle || '');
      }
    } catch (e) {
      console.error("Channel settings fetch error:", e);
    }
  };

  const handleTokenFileUpload = async (file) => {
    if (!file) return;
    setUploadingTokenFile(true);
    setTokenUploadError('');
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const res = await authFetch('/api/settings/youtube-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token_json: JSON.stringify(parsed) })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to process credential file.");
      }
      if (data.auth_required && data.auth_url) {
        setOauthAuthUrl(data.auth_url);
        setOauthStep('awaiting_code');
      } else {
        fetchChannelSettings();
        fetchUsage();
        fetchStats();
        setShowChannelModal(false);
        setOauthStep('initial');
        setShowChangeCredentials(false);
        showToast(data.message || "YouTube channel connected successfully!", "success");
      }
    } catch (err) {
      setTokenUploadError(err.message);
    } finally {
      setUploadingTokenFile(false);
    }
  };

  const handleStartGoogleAuth = async () => {
    setUploadingTokenFile(true);
    setTokenUploadError('');
    try {
      const res = await authFetch('/api/settings/youtube-auth-url');
      const data = await res.json();
      if (data.has_client_secret && data.auth_url) {
        setOauthAuthUrl(data.auth_url);
        setOauthStep('awaiting_code');
      } else {
        showToast("No Google OAuth client credentials found on server. Please upload your client_secret.json file.", "error");
      }
    } catch (err) {
      setTokenUploadError(err.message);
    } finally {
      setUploadingTokenFile(false);
    }
  };

  const handleCompleteOauthCode = async () => {
    if (!inputOauthCode.trim()) {
      showToast("Please paste the authorization code or redirect URL from Google.", "error");
      return;
    }
    setExchangingOauth(true);
    setTokenUploadError('');
    try {
      const res = await authFetch('/api/settings/youtube-oauth-callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code_or_url: inputOauthCode.trim() })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Failed to exchange OAuth code.");
      }
      setInputOauthCode('');
      setOauthStep('initial');
      setShowChangeCredentials(false);
      fetchChannelSettings();
      fetchUsage();
      fetchStats();
      setShowChannelModal(false);
      showToast("YouTube channel connected successfully!", "success");
    } catch (err) {
      setTokenUploadError(err.message);
    } finally {
      setExchangingOauth(false);
    }
  };

  const handleSaveChannel = async () => {
    setSavingChannel(true);
    setTokenUploadError('');
    try {
      if (inputChannelHandle.trim()) {
        await authFetch('/api/settings/channel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ channel_handle: inputChannelHandle.trim() })
        });
      }
      if (inputYoutubeToken.trim()) {
        const res = await authFetch('/api/settings/youtube-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token_json: inputYoutubeToken.trim() })
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || data.message || "Failed to save YouTube token.");
        }
        if (data.auth_required && data.auth_url) {
          setOauthAuthUrl(data.auth_url);
          setOauthStep('awaiting_code');
          setSavingChannel(false);
          return;
        }
        setInputYoutubeToken('');
      }
      setShowChannelModal(false);
      setOauthStep('initial');
      setShowChangeCredentials(false);
      fetchChannelSettings();
      fetchUsage();
      fetchStats();
      showToast("Channel settings updated successfully!", "success");
    } catch (e) {
      setTokenUploadError(e.message);
      showToast("Error saving channel settings: " + e.message, "error");
    } finally {
      setSavingChannel(false);
    }
  };

  const handleDisconnectYoutube = async () => {
    if (!confirm("Disconnect your YouTube channel OAuth token?")) return;
    try {
      await authFetch('/api/settings/youtube-token', { method: 'DELETE' });
      fetchChannelSettings();
      fetchUsage();
      fetchStats();
      setOauthStep('initial');
      setShowChangeCredentials(false);
      showToast("YouTube channel disconnected.", "info");
    } catch (e) {
      showToast("Error disconnecting: " + e.message, "error");
    }
  };

  const handleGenerateIdea = async (overrideNiche = null) => {
    setGeneratingIdea(true);
    try {
      const targetNiche = overrideNiche || selectedNiche;
      const res = await authFetch('/api/ideas/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niche: targetNiche, concept: overrideNiche === 'random' ? '' : ideaConcept })
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedIdea(data);
        if (data.next_id) {
          setStudioVideoId(data.next_id);
        }
      }
    } catch (e) {
      console.error("Idea generation error:", e);
    } finally {
      setGeneratingIdea(false);
      fetchUsage();
    }
  };

  const autoGenerateAndFillStudio = async () => {
    setGeneratingIdea(true);
    try {
      const res = await authFetch('/api/ideas/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niche: 'random', concept: '' })
      });
      if (res.ok) {
        const data = await res.json();
        setGeneratedIdea(data);
        setStudioVideoId(data.next_id || 'short_08');
        setStudioTitle(data.title);
        setStudioScript(data.script);
        setStudioKeywords(data.keywords.join(', '));
        setStudioDesc(data.description);
        setStudioComment(data.pinned_comment);
        if (data.voice) {
          setStudioVoice(data.voice);
        }
      }
    } catch (e) {
      console.error("Auto generate error:", e);
    } finally {
      setGeneratingIdea(false);
      fetchUsage();
    }
  };

  const sendIdeaToStudio = (idea) => {
    if (idea.next_id) {
      setStudioVideoId(idea.next_id);
    }
    setStudioTitle(idea.title);
    setStudioScript(idea.script);
    setStudioKeywords(idea.keywords.join(', '));
    setStudioDesc(idea.description);
    setStudioComment(idea.pinned_comment);
    if (idea.voice) {
      setStudioVoice(idea.voice);
    }
    setActiveTab('studio');
  };

  const handleQuickProduce = async (idea) => {
    sendIdeaToStudio(idea);
    showToast(`Quick starting ${idea.next_id || studioVideoId} in Studio...`, 'info');
    setIsProducing(true);
    setTaskStatus({ status: 'queued', progress: 5, log: ['Initializing production request from Idea Lab...'] });

    try {
      const kws = Array.isArray(idea.keywords) ? idea.keywords : (idea.keywords || '').split(',').map(s => s.trim()).filter(Boolean);
      const res = await authFetch('/api/produce', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: idea.next_id || studioVideoId,
          script_text: idea.script,
          clip_keywords: kws,
          title: idea.title || `${idea.next_id || studioVideoId} #shorts`,
          description: idea.description,
          pinned_comment: idea.pinned_comment,
          voice: idea.voice || studioVoice
        })
      });

      if (res.ok) {
        const data = await res.json();
        setActiveTaskId(data.task_id);
        showToast("Production started in Studio!", "success");
      } else {
        const err = await res.json();
        showToast(`Error starting production: ${err.detail}`, "error");
        setIsProducing(false);
      }
    } catch (e) {
      showToast(`Network error: ${e.message}`, "error");
      setIsProducing(false);
    }
  };

  const handleStartProduction = async () => {
    if (!studioScript.trim()) {
      showToast("Please enter a script first.", "error");
      return;
    }
    setIsProducing(true);
    setTaskStatus({ status: 'queued', progress: 5, log: ['Initializing production request...'] });

    try {
      const kws = studioKeywords.split(',').map(s => s.trim()).filter(Boolean);
      const res = await authFetch('/api/produce', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_id: studioVideoId,
          script_text: studioScript,
          clip_keywords: kws,
          title: studioTitle || `${studioVideoId} #shorts`,
          description: studioDesc,
          pinned_comment: studioComment,
          voice: studioVoice
        })
      });

      if (res.ok) {
        const data = await res.json();
        setActiveTaskId(data.task_id);
      } else {
        const err = await res.json();
        showToast(`Error starting production: ${err.detail}`, "error");
        setIsProducing(false);
      }
    } catch (e) {
      showToast(`Network error: ${e.message}`, "error");
      setIsProducing(false);
    }
  };

  const handleUpload = async () => {
    setUploading(true);
    setUploadResult(null);
    try {
      const payload = {
        video_id: dispatchVideoId,
        privacy_status: dispatchMode,
        publish_at: dispatchMode === 'scheduled' && dispatchTime ? new Date(dispatchTime).toISOString() : null
      };

      const res = await authFetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok) {
        setUploadResult({ success: true, ...data });
        fetchStats();
        fetchUsage();
      } else {
        setUploadResult({ success: false, error: data.detail });
      }
    } catch (e) {
      setUploadResult({ success: false, error: e.message });
    } finally {
      setUploading(false);
    }
  };

  const copyMetadata = (v) => {
    const text = `TITLE:\n${v.title}\n\nDESCRIPTION:\n${v.description}\n\nPINNED COMMENT:\n${v.pinned_comment}`;
    navigator.clipboard.writeText(text);
    setCopiedId(v.id);
    showToast(`Copied SEO metadata for ${v.id}!`, "success");
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDeleteVideo = async (videoId) => {
    if (!window.confirm(`Are you sure you want to permanently delete '${videoId}' and all its media files?`)) {
      return;
    }
    try {
      const res = await authFetch(`/api/videos/${videoId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || `Deleted ${videoId}`, "success");
        if (previewVideo?.id === videoId) {
          setPreviewVideo(null);
        }
        fetchVideos();
        fetchStats();
      } else {
        showToast(`Failed to delete: ${data.detail}`, "error");
      }
    } catch (e) {
      showToast(`Error deleting: ${e.message}`, "error");
    }
  };

  if (authChecking) {
    return (
      <div className="min-h-screen bg-[#09090e] flex items-center justify-center text-slate-400 font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-violet-500 border-t-cyan-400 rounded-full animate-spin"></div>
          <span className="font-mono text-xs text-slate-400 tracking-wider">VERIFYING STUDIO ACCESS...</span>
        </div>
      </div>
    );
  }

  if (!authToken || !currentUser) {
    return (
      <AuthScreen
        onAuthSuccess={(token, user) => {
          localStorage.setItem('yt_studio_jwt', token);
          setAuthToken(token);
          setCurrentUser(user);
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#09090e] text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="h-16 border-b border-slate-800/80 bg-[#0d0d14]/90 backdrop-blur sticky top-0 z-40 px-6 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-violet-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <Film className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-extrabold tracking-wider text-base bg-clip-text text-transparent bg-gradient-to-r from-violet-400 via-purple-300 to-cyan-400">
                SHADOWMIND
              </span>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-800/50">
                STUDIO v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400">Faceless Shorts Automation Engine</p>
          </div>
        </div>

        {/* Global Channel Telemetry Bar */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1">
            <button 
              onClick={() => setShowChannelModal(true)}
              title="Configure YouTube Channel & OAuth Token"
              className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 transition text-xs cursor-pointer"
            >
              <span className={`w-2 h-2 rounded-full ${channelData?.has_youtube_token ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`}></span>
              <span className="font-mono text-slate-300">{stats?.channel_handle || "Configure Channel"}</span>
              <Sliders className="w-3.5 h-3.5 text-slate-400" />
            </button>
            {stats?.channel_url && (
              <a 
                href={stats.channel_url}
                target="_blank" 
                rel="noreferrer"
                className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:text-white text-slate-400 transition"
                title="Open YouTube Channel"
              >
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>

          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-violet-950/40 border border-violet-800/40 text-xs">
            <Eye className="w-3.5 h-3.5 text-violet-400" />
            <span className="text-slate-400">Total Views:</span>
            <span className="font-bold text-violet-300 font-mono text-sm">{stats ? stats.total_views : '...'}</span>
          </div>

          <button
            onClick={() => setShowAiModal(true)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border text-xs transition ${
              aiSettings?.has_key 
                ? 'bg-cyan-950/60 border-cyan-700/60 text-cyan-300' 
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>{aiSettings?.has_key ? 'Gemini Flash Active' : 'Connect Free AI'}</span>
            <span className={`w-1.5 h-1.5 rounded-full ${aiSettings?.has_key ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`}></span>
          </button>

          <button 
            onClick={() => { fetchStats(); fetchVideos(); }}
            disabled={loadingStats}
            title="Refresh Live Metrics"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <RefreshCw className={`w-4 h-4 ${loadingStats ? 'animate-spin text-violet-400' : ''}`} />
          </button>

          {currentUser && (
            <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs">
              <span className="text-cyan-400">👤</span>
              <span className="font-mono text-slate-300 truncate max-w-[130px]">{currentUser.email}</span>
              <button
                onClick={() => {
                  localStorage.removeItem('yt_studio_jwt');
                  setAuthToken('');
                  setCurrentUser(null);
                }}
                className="text-[11px] font-bold text-red-400 hover:text-red-300 ml-1 transition"
                title="Sign Out"
              >
                SIGN OUT
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Sidebar */}
        <aside className="w-64 border-r border-slate-800/60 bg-[#0d0d14]/50 p-4 flex flex-col justify-between">
          <nav className="space-y-1.5">
            <button
              onClick={() => setActiveTab('overview')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                activeTab === 'overview' 
                  ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/10 text-violet-300 border border-violet-500/30' 
                  : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Overview & Views</span>
            </button>

            <button
              onClick={() => setActiveTab('vault')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                activeTab === 'vault' 
                  ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/10 text-violet-300 border border-violet-500/30' 
                  : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
              }`}
            >
              <Video className="w-4 h-4" />
              <div className="flex-1 flex justify-between items-center">
                <span>Video Vault</span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                  {videos.length}
                </span>
              </div>
            </button>

            <button
              onClick={() => setActiveTab('ideas')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                activeTab === 'ideas' 
                  ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/10 text-violet-300 border border-violet-500/30' 
                  : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
              }`}
            >
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>Niche & Idea Lab</span>
            </button>

            <button
              onClick={() => setActiveTab('studio')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                activeTab === 'studio' 
                  ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/10 text-violet-300 border border-violet-500/30' 
                  : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
              }`}
            >
              <Sliders className="w-4 h-4 text-cyan-400" />
              <div className="flex-1 flex justify-between items-center">
                <span>Studio Generator</span>
                {isProducing && (
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                )}
              </div>
            </button>

            <button
              onClick={() => setActiveTab('dispatcher')}
              className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                activeTab === 'dispatcher' 
                  ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/10 text-violet-300 border border-violet-500/30' 
                  : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
              }`}
            >
              <Send className="w-4 h-4 text-emerald-400" />
              <span>YouTube Dispatcher</span>
            </button>
          </nav>

          {/* Accurate Daily Quotas & Credits Tracker */}
          <div className="p-3.5 rounded-2xl bg-gradient-to-b from-[#13131c] to-[#0d0d14] border border-slate-800/90 text-xs space-y-3 shadow-lg">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-200 flex items-center space-x-1.5 text-[11px] uppercase tracking-wider font-mono">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" />
                <span>Daily Quotas</span>
              </span>
              <span className="text-[10px] font-mono text-slate-400 flex items-center space-x-1" title="Google Cloud quota reset at Midnight Pacific Time">
                <Clock className="w-3 h-3 text-slate-500" />
                <span>{usage ? `${usage.reset_countdown} (PT)` : '...'}</span>
              </span>
            </div>

            {/* Gemini 3.5 Flash Lite Quota */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 flex items-center space-x-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${usage?.gemini?.has_key ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`}></span>
                  <span>Gemini 3.5 Flash Lite</span>
                </span>
                {usage && usage.gemini?.has_key === false ? (
                  <button 
                    onClick={() => setShowAiModal(true)}
                    className="text-[10px] font-mono font-bold text-slate-400 hover:text-cyan-300 underline"
                  >
                    No Key
                  </button>
                ) : (
                  <span className="font-mono font-bold text-cyan-300">
                    {usage ? `${usage.gemini.remaining.toLocaleString()} left` : '...'}
                  </span>
                )}
              </div>
              <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                <div 
                  style={{ width: `${usage?.gemini?.has_key === false ? 0 : Math.max(3, 100 - (usage?.gemini?.percent || 0))}%` }}
                  className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
                ></div>
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>Used: {usage ? usage.gemini.used.toLocaleString() : 0}</span>
                <span>Cap: {usage?.gemini?.limit ? `${usage.gemini.limit.toLocaleString()}/day` : '1,500/day'}</span>
              </div>
            </div>

            {/* YouTube Data API v3 Quota */}
            <div className="space-y-1 pt-2 border-t border-slate-800/60">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 flex items-center space-x-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${usage?.youtube?.connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
                  <span>YouTube API</span>
                </span>
                {usage && usage.youtube?.connected === false ? (
                  <button 
                    onClick={() => setShowChannelModal(true)}
                    className="text-[10px] font-mono font-bold text-amber-400 hover:text-amber-300 underline"
                  >
                    Not Linked
                  </button>
                ) : (
                  <span className="font-mono font-bold text-emerald-400">
                    {usage ? `${usage.youtube.uploads_remaining} uploads left` : '...'}
                  </span>
                )}
              </div>
              <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                <div 
                  style={{ width: `${usage?.youtube?.connected === false ? 0 : Math.max(3, 100 - (usage?.youtube?.percent || 0))}%` }}
                  className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full"
                ></div>
              </div>
              <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                <span>Used: {usage ? usage.youtube.units_used.toLocaleString() : 0} pts</span>
                <span>Cap: {usage?.youtube?.limit ? `${usage.youtube.limit.toLocaleString()} pts` : '10,000 pts'}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-500">
              <span className="flex items-center space-x-1 text-emerald-400/90 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>$0.00 Cost Stack</span>
              </span>
              <button 
                onClick={fetchUsage} 
                disabled={loadingUsage}
                className="hover:text-cyan-400 px-2 py-1 hover:bg-slate-800/80 rounded-lg transition flex items-center space-x-1 border border-transparent hover:border-slate-700/60" 
                title="Sync Daily API Quota & AI Status"
              >
                <RefreshCw className={`w-3 h-3 ${loadingUsage ? 'animate-spin text-cyan-400' : 'text-slate-400'}`} />
                <span className="text-[10px] font-mono text-slate-400">
                  {loadingUsage ? 'Syncing...' : 'Sync'}
                </span>
              </button>
            </div>
          </div>
        </aside>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-6">
          {/* ==================================================== */}
          {/* TAB 1: OVERVIEW & VIEWS TELEMETRY */}
          {/* ==================================================== */}
          {activeTab === 'overview' && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-black text-white">Channel Analytics & Telemetry</h1>
                  <p className="text-sm text-slate-400">Real-time performance audit for {stats?.channel_handle || "your channel"}</p>
                </div>
                <div className="text-xs px-3 py-1.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 flex items-center space-x-1.5 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span>FEED INDEXED</span>
                </div>
              </div>

              {/* Top Stats Metric Cards */}
              {loadingStats && !stats ? (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-3 animate-pulse">
                      <div className="flex justify-between items-center">
                        <div className="h-3 w-28 bg-slate-800 rounded"></div>
                        <div className="h-4 w-4 bg-slate-800 rounded"></div>
                      </div>
                      <div className="h-8 w-20 bg-slate-800 rounded"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-slate-700 transition">
                    <div className="flex items-center justify-between text-slate-400 text-xs">
                      <span>Total Channel Views</span>
                      <Eye className="w-4 h-4 text-violet-400" />
                    </div>
                    <div className="mt-2 flex items-baseline space-x-2">
                      <span className="text-3xl font-black text-white font-mono">{stats?.total_views || 0}</span>
                      <span className="text-xs text-emerald-400 font-bold">+100% Organic</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-slate-700 transition">
                    <div className="flex items-center justify-between text-slate-400 text-xs">
                      <span>Top Breakout Short</span>
                      <Flame className="w-4 h-4 text-amber-500" />
                    </div>
                    <div className="mt-2 flex items-baseline space-x-2">
                      <span className="text-3xl font-black text-amber-400 font-mono">
                        {topBreakoutViews.toLocaleString()}
                      </span>
                      <span className="text-xs text-slate-400">
                        views ({topBreakoutLabel})
                      </span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-slate-700 transition">
                    <div className="flex items-center justify-between text-slate-400 text-xs">
                      <span>Videos In Pipeline</span>
                      <Video className="w-4 h-4 text-cyan-400" />
                    </div>
                    <div className="mt-2 flex items-baseline space-x-2">
                      <span className="text-3xl font-black text-white font-mono">{videos.length}</span>
                      <span className="text-xs text-cyan-400 font-bold">1080x1920 HD</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-slate-700 transition">
                    <div className="flex items-center justify-between text-slate-400 text-xs">
                      <span>Target Geographic RPM</span>
                      <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                    </div>
                    <div className="mt-2 flex items-baseline space-x-2">
                      <span className="text-3xl font-black text-emerald-400 font-mono">$0.25</span>
                      <span className="text-xs text-slate-400">US/UK Tier 1</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Unified Tracked Shorts Index & Velocity Table with Sub-Tabs */}
              <div className="rounded-2xl bg-[#12121a] border border-slate-800/80 overflow-hidden shadow-xl">
                <div className="p-4 border-b border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div className="flex items-center space-x-2.5">
                    <div className="p-2 rounded-xl bg-violet-950/60 border border-violet-800/50">
                      <BarChart3 className="w-4 h-4 text-violet-400" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-bold text-sm text-white">Tracked Video Index & Velocity Telemetry</h3>
                        {loadingStats && (
                          <span className="flex items-center space-x-1 text-[10px] font-mono font-semibold text-cyan-400 bg-cyan-950/70 border border-cyan-800/50 px-2 py-0.5 rounded-full animate-pulse">
                            <RefreshCw className="w-2.5 h-2.5 animate-spin" />
                            <span>Syncing...</span>
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-slate-400">Live view counts, motion retention comparison, and channel dispatch pipeline</p>
                    </div>
                  </div>

                  {/* Sub-tabs: Live Tracked, Scheduled Pipeline, All */}
                  <div className="flex items-center space-x-1.5 p-1 bg-slate-900/90 rounded-xl border border-slate-800 self-start md:self-auto">
                    <button
                      onClick={() => { setTableTab('live'); setTablePage(1); }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                        tableTab === 'live'
                          ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                      <span>Live Tracked</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 text-emerald-200">
                        {allTableVideos.filter(v => v.status === 'LIVE' || v.status === 'PRIVATE' || v.views > 0).length}
                      </span>
                    </button>

                    <button
                      onClick={() => { setTableTab('scheduled'); setTablePage(1); }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                        tableTab === 'scheduled'
                          ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <Clock className="w-3 h-3 text-blue-300" />
                      <span>Scheduled Pipeline</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 text-blue-200">
                        {allTableVideos.filter(v => v.status === 'SCHEDULED').length}
                      </span>
                    </button>

                    <button
                      onClick={() => { setTableTab('all'); setTablePage(1); }}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                        tableTab === 'all'
                          ? 'bg-violet-600 text-white shadow-md shadow-violet-600/20'
                          : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <span>All ({allTableVideos.length})</span>
                    </button>
                  </div>
                </div>

                {loadingStats && (
                  <div className="h-0.5 w-full bg-slate-800/80 overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-violet-500 via-cyan-400 to-violet-500 animate-[pulse_1s_ease-in-out_infinite] w-full"></div>
                  </div>
                )}

                <div className={`overflow-x-auto transition-opacity ${loadingStats ? 'opacity-85' : 'opacity-100'}`}>
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-900/60 text-slate-400 uppercase font-mono border-b border-slate-800/80">
                      <tr>
                        <th className="py-3 px-4">Short ID</th>
                        <th className="py-3 px-4">Title / Topic</th>
                        <th className="py-3 px-4">Format</th>
                        <th className="py-3 px-4 min-w-[180px]">
                          {tableTab === 'scheduled' ? (
                            <span className="flex items-center space-x-1.5 text-blue-300">
                              <Calendar className="w-3.5 h-3.5 text-blue-400" />
                              <span>Scheduled Drop (Earliest First)</span>
                            </span>
                          ) : (
                            'Views & Velocity'
                          )}
                        </th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-sans">
                      {loadingStats && allTableVideos.length === 0 ? (
                        [...Array(tablePerPage > 5 ? 5 : tablePerPage)].map((_, i) => (
                          <tr key={`tbl-skel-${i}`} className="animate-pulse border-b border-slate-800/40">
                            <td className="py-3.5 px-4"><div className="h-3.5 w-16 bg-slate-800/80 rounded"></div></td>
                            <td className="py-3.5 px-4"><div className="h-3.5 w-48 bg-slate-800/80 rounded"></div></td>
                            <td className="py-3.5 px-4"><div className="h-4 w-20 bg-slate-800/80 rounded"></div></td>
                            <td className="py-3.5 px-4"><div className="h-3.5 w-32 bg-slate-800/80 rounded"></div></td>
                            <td className="py-3.5 px-4"><div className="h-4 w-16 bg-slate-800/80 rounded"></div></td>
                            <td className="py-3.5 px-4 text-right"><div className="h-3.5 w-12 bg-slate-800/80 rounded ml-auto"></div></td>
                          </tr>
                        ))
                      ) : paginatedTableVideos.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-slate-500 font-mono">
                            No videos found in this tab.
                          </td>
                        </tr>
                      ) : (
                        paginatedTableVideos.map((item) => {
                          const maxViews = 1100;
                          const pct = Math.min(100, Math.max(5, (item.views / maxViews) * 100));
                          const isMotion = item.motion_type === 'Real-Motion HD' || (!item.short_id?.startsWith('short_01') && !item.short_id?.startsWith('short_02') && !item.short_id?.startsWith('short_03'));
                          const isScheduled = item.status === 'SCHEDULED';

                          return (
                            <tr key={item.short_id} className="hover:bg-slate-900/40 transition">
                              <td className="py-3 px-4 font-mono font-bold text-violet-300">
                                {item.short_id.toUpperCase()}
                              </td>
                              <td className="py-3 px-4 text-slate-200 max-w-xs truncate" title={item.title}>
                                {item.title || "Scheduled Short"}
                              </td>
                              <td className="py-3 px-4">
                                {isMotion ? (
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/50">
                                    Real Motion HD
                                  </span>
                                ) : (
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800/50">
                                    Still Pilot
                                  </span>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                {isScheduled ? (
                                  <div className="flex items-center space-x-2 text-blue-300 font-mono text-xs">
                                    <Clock className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                                    <span className="font-semibold">{formatScheduleDate(item.publish_at)}</span>
                                  </div>
                                ) : (
                                  <div>
                                    <div className="flex items-center justify-between text-xs mb-1 font-mono">
                                      <span className="font-bold text-white">{item.views.toLocaleString()} views</span>
                                      <span className="text-[10px] text-slate-400">
                                        {item.short_id === 'short_04' ? '🚀 1.06k Breakout' : item.short_id === 'short_06' ? '🔥 339 Velocity' : isMotion ? 'Motion HD' : 'Static'}
                                      </span>
                                    </div>
                                    <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                                      <div 
                                        style={{ width: `${pct}%` }} 
                                        className={`h-full rounded-full transition-all duration-500 ${
                                          item.short_id === 'short_04'
                                            ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 shadow-sm shadow-emerald-500/50'
                                            : item.short_id === 'short_06' 
                                              ? 'bg-gradient-to-r from-amber-500 to-orange-500 shadow-sm shadow-orange-500/50' 
                                              : isMotion 
                                                ? 'bg-gradient-to-r from-cyan-500 to-blue-500' 
                                                : 'bg-gradient-to-r from-violet-600 to-purple-500'
                                        }`}
                                      ></div>
                                    </div>
                                  </div>
                                )}
                              </td>
                              <td className="py-3 px-4">
                                {item.status === 'LIVE' ? (
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/60 flex items-center space-x-1 w-fit">
                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                                    <span>LIVE</span>
                                  </span>
                                ) : item.status === 'SCHEDULED' ? (
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/60 flex items-center space-x-1 w-fit">
                                    <Clock className="w-2.5 h-2.5 text-blue-400" />
                                    <span>SCHEDULED</span>
                                  </span>
                                ) : (
                                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                                    PRIVATE
                                  </span>
                                )}
                              </td>
                              <td className="py-3 px-4 text-right">
                                {item.url ? (
                                  <a
                                    href={item.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="inline-flex items-center space-x-1 text-violet-400 hover:text-violet-300 font-medium"
                                  >
                                    <span>{isScheduled ? 'YouTube' : 'Watch'}</span>
                                    <ExternalLink className="w-3 h-3" />
                                  </a>
                                ) : (
                                  <span className="text-slate-600 text-[11px] font-mono">Ready</span>
                                )}
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>

                <Pagination
                  currentPage={tablePage}
                  totalItems={filteredTableVideos.length}
                  perPage={tablePerPage}
                  onPageChange={setTablePage}
                  onPerPageChange={setTablePerPage}
                  perPageOptions={[5, 10, 20, 50]}
                />
              </div>
            </div>
          )}

          {/* ==================================================== */}
          {/* TAB 2: VIDEO VAULT (ALL LOCAL SHORTS + PLAYER) */}
          {/* ==================================================== */}
          {activeTab === 'vault' && (
            <div className="space-y-6 max-w-6xl mx-auto">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-black text-white">Video Vault</h1>
                  <p className="text-sm text-slate-400">Inspect, preview, and dispatch local rendered shorts</p>
                </div>
                <span className="text-xs font-mono text-slate-400">{videos.length} videos stored locally</span>
              </div>

              {loadingVideos && videos.length === 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {[1, 2, 3, 4, 5, 6].map((n) => (
                    <div key={n} className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-4 animate-pulse">
                      <div className="flex items-center justify-between">
                        <div className="h-4 w-16 bg-slate-800 rounded"></div>
                        <div className="h-4 w-24 bg-slate-800 rounded"></div>
                      </div>
                      <div className="space-y-2">
                        <div className="h-4 w-full bg-slate-800 rounded"></div>
                        <div className="h-4 w-3/4 bg-slate-800 rounded"></div>
                      </div>
                      <div className="space-y-1.5 pt-2">
                        <div className="h-3 w-full bg-slate-800/60 rounded"></div>
                        <div className="h-3 w-5/6 bg-slate-800/60 rounded"></div>
                      </div>
                      <div className="pt-3 border-t border-slate-800/60 flex items-center space-x-2">
                        <div className="h-8 flex-1 bg-slate-800 rounded-xl"></div>
                        <div className="h-8 w-8 bg-slate-800 rounded-xl"></div>
                        <div className="h-8 w-8 bg-slate-800 rounded-xl"></div>
                        <div className="h-8 w-8 bg-slate-800 rounded-xl"></div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-5">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {paginatedVaultVideos.map((vid) => (
                      <div 
                        key={vid.id}
                        className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-violet-600/50 transition flex flex-col justify-between space-y-4 group"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-violet-400 uppercase">{vid.id}</span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                              vid.motion_type === 'Real-Motion HD' 
                                ? 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60' 
                                : 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                            }`}>
                              {vid.motion_type}
                            </span>
                          </div>

                          <h3 className="font-bold text-sm text-white line-clamp-2 leading-snug">
                            {vid.title}
                          </h3>

                          <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">
                            {vid.description || "No SEO description generated."}
                          </p>
                        </div>

                        <div className="space-y-3 pt-2 border-t border-slate-800/60">
                          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                            <span className="flex items-center space-x-1">
                              <Layers className="w-3.5 h-3.5 text-slate-500" />
                              <span>{vid.size_mb} MB</span>
                            </span>
                            <span className="flex items-center space-x-1">
                              <Clock className="w-3.5 h-3.5 text-slate-500" />
                              <span>{vid.modified.split(' ')[0]}</span>
                            </span>
                          </div>

                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => setPreviewVideo(vid)}
                              className="flex-1 py-2 px-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs flex items-center justify-center space-x-1.5 transition shadow-lg shadow-violet-600/20"
                            >
                              <Play className="w-3.5 h-3.5 fill-current" />
                              <span>Play</span>
                            </button>

                            <a
                              href={`/api/videos/${vid.id}/stream?token=${authToken}`}
                              download={`${vid.id}.mp4`}
                              title="Direct Download MP4"
                              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-emerald-400 transition"
                            >
                              <Download className="w-4 h-4" />
                            </a>

                            <button
                              onClick={() => copyMetadata(vid)}
                              title="Copy SEO metadata"
                              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                            >
                              {copiedId === vid.id ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                            </button>

                            <button
                              onClick={() => {
                                setDispatchVideoId(vid.id);
                                setActiveTab('dispatcher');
                              }}
                              title="Schedule or publish this video"
                              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 transition"
                            >
                              <Send className="w-4 h-4" />
                            </button>

                            <button
                              onClick={() => handleDeleteVideo(vid.id)}
                              title="Delete this short permanently"
                              className="p-2 rounded-xl bg-slate-800 hover:bg-red-950 text-slate-400 hover:text-red-400 transition"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-2xl bg-[#12121a] border border-slate-800/80 overflow-hidden">
                    <Pagination
                      currentPage={vaultPage}
                      totalItems={videos.length}
                      perPage={vaultPerPage}
                      onPageChange={setVaultPage}
                      onPerPageChange={setVaultPerPage}
                      perPageOptions={[6, 9, 12, 24, 48]}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ==================================================== */}
          {/* TAB 3: NICHE & IDEA LAB */}
          {/* ==================================================== */}
          {activeTab === 'ideas' && (
            <div className="space-y-6 max-w-5xl mx-auto">
              <div>
                <h1 className="text-2xl font-black text-white flex items-center space-x-2">
                  <Sparkles className="w-6 h-6 text-amber-400" />
                  <span>Viral Niche & Idea Lab</span>
                </h1>
                <p className="text-sm text-slate-400">Discover trending niches, psychological hooks, and 1-click script structures</p>
              </div>

              {/* Niche Selector Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {niches.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => setSelectedNiche(n.id)}
                    className={`p-4 rounded-2xl text-left border transition flex flex-col justify-between space-y-2 ${
                      selectedNiche === n.id
                        ? 'bg-violet-950/40 border-violet-500 shadow-lg shadow-violet-500/10'
                        : 'bg-[#12121a] border-slate-800/80 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-white text-sm">{n.name}</span>
                        <span className="text-emerald-400 font-mono font-bold">{n.rpm_range}</span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">{n.description}</p>
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/40">
                      <span>Retention: <strong className="text-slate-300">{n.retention_rate}</strong></span>
                      <span className="font-mono text-cyan-400">{n.voice_recommended.split('-')[2]}</span>
                    </div>
                  </button>
                ))}
              </div>

              {/* Concept Generator Card */}
              <div className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-4">
                <h3 className="font-bold text-sm text-white">Generate Viral Script Structure</h3>
                <div className="flex space-x-3">
                  <input
                    type="text"
                    value={ideaConcept}
                    onChange={(e) => setIdeaConcept(e.target.value)}
                    placeholder="Enter custom angle or keyword (e.g. 'Door in the face technique', 'Robot factories', 'Niacinamide')"
                    className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white"
                  />
                  <button
                    onClick={() => handleGenerateIdea()}
                    disabled={generatingIdea}
                    className="px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white font-bold text-sm flex items-center space-x-2 transition shadow-lg shadow-violet-600/20"
                  >
                    {generatingIdea ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    <span>Generate Concept</span>
                  </button>

                  <button
                    onClick={() => handleGenerateIdea('random')}
                    disabled={generatingIdea}
                    className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 disabled:opacity-50 text-black font-extrabold text-sm flex items-center space-x-2 transition shadow-lg shadow-amber-500/20"
                  >
                    <Sparkles className="w-4 h-4 fill-current" />
                    <span>🎲 Surprise Me</span>
                  </button>
                </div>

                {/* Skeleton Loader during Generation */}
                {generatingIdea && (
                  <div className="mt-4 p-5 rounded-xl bg-slate-900/60 border border-cyan-800/40 space-y-4 animate-pulse">
                    <div className="flex items-center justify-between">
                      <div className="h-4 w-44 bg-cyan-950/80 rounded"></div>
                      <div className="h-7 w-28 bg-slate-800 rounded-lg"></div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="h-3 w-16 bg-slate-800 rounded"></div>
                      <div className="h-5 w-4/5 bg-slate-800 rounded"></div>
                    </div>
                    <div className="space-y-2">
                      <div className="h-3 w-28 bg-slate-800 rounded"></div>
                      <div className="p-3.5 bg-black/40 rounded-lg space-y-2 border border-slate-800/40">
                        <div className="h-3 w-full bg-slate-800 rounded"></div>
                        <div className="h-3 w-11/12 bg-slate-800 rounded"></div>
                        <div className="h-3 w-4/5 bg-slate-800 rounded"></div>
                      </div>
                    </div>
                    <div className="flex space-x-2 pt-1">
                      <div className="h-5 w-20 bg-violet-950/60 rounded"></div>
                      <div className="h-5 w-20 bg-violet-950/60 rounded"></div>
                      <div className="h-5 w-20 bg-violet-950/60 rounded"></div>
                    </div>
                  </div>
                )}

                {generatedIdea && !generatingIdea && (
                  <div className="mt-4 p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-mono font-bold text-cyan-400 uppercase">Generated Concept</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                          generatedIdea.source && generatedIdea.source.startsWith('gemini')
                            ? 'bg-cyan-950 text-cyan-300 border-cyan-700'
                            : 'bg-violet-950 text-violet-300 border-violet-800'
                        }`}>
                          {generatedIdea.source && generatedIdea.source.startsWith('gemini') ? `⚡ ${generatedIdea.source.toUpperCase()}` : '🤖 Built-in Matrix'}
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => sendIdeaToStudio(generatedIdea)}
                          className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-bold text-xs flex items-center space-x-1.5 transition border border-slate-700/60"
                        >
                          <span>Send to Studio</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleQuickProduce(generatedIdea)}
                          disabled={isProducing}
                          className="py-1.5 px-3.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white font-bold text-xs flex items-center space-x-1.5 transition shadow-lg shadow-cyan-600/20"
                        >
                          <Zap className="w-3.5 h-3.5 fill-current text-cyan-200" />
                          <span>Quick Produce</span>
                        </button>
                      </div>
                    </div>

                    <div className="space-y-1">
                      <span className="text-xs text-slate-500 font-mono uppercase">Title</span>
                      <p className="text-sm font-bold text-white">{generatedIdea.title}</p>
                    </div>

                    <div className="space-y-1">
                      <span className="text-xs text-slate-500 font-mono uppercase">Script (45s retention hook)</span>
                      <p className="text-xs text-slate-300 leading-relaxed bg-black/40 p-3 rounded-lg border border-slate-800/60 font-sans">
                        {generatedIdea.script}
                      </p>
                    </div>

                    <div className="space-y-1">
                      <span className="text-xs text-slate-500 font-mono uppercase">Mixkit Footage Keywords</span>
                      <div className="flex flex-wrap gap-1.5">
                        {generatedIdea.keywords.map((k, i) => (
                          <span key={i} className="text-xs px-2 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-800/40 font-mono">
                            {k}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ==================================================== */}
          {/* TAB 4: STUDIO GENERATOR */}
          {/* ==================================================== */}
          {activeTab === 'studio' && (
            <div className="space-y-6 max-w-4xl mx-auto">
              <div>
                <h1 className="text-2xl font-black text-white flex items-center space-x-2">
                  <Sliders className="w-6 h-6 text-cyan-400" />
                  <span>Production Studio</span>
                </h1>
                <p className="text-sm text-slate-400">Synthesize audio, scrape stock clips, build ASS subtitles & render 1080x1920 MP4</p>
              </div>

              <div className="p-6 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-5">
                {/* 1-Click Zero Typing Auto-Roll Banner */}
                <div className="p-4 rounded-xl bg-gradient-to-r from-violet-950/70 via-purple-950/50 to-cyan-950/70 border border-violet-700/60 flex items-center justify-between shadow-lg">
                  <div>
                    <h3 className="font-extrabold text-sm text-white flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-amber-400" />
                      <span>100% Zero-Typing Mode</span>
                    </h3>
                    <p className="text-xs text-slate-400">1-click generates next short ID, viral script, stock tags, and voice</p>
                  </div>
                  <button
                    onClick={autoGenerateAndFillStudio}
                    disabled={generatingIdea || isProducing}
                    className="py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-extrabold text-xs flex items-center space-x-1.5 transition shadow-lg shadow-cyan-500/20"
                  >
                    {generatingIdea ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5 fill-current" />}
                    <span>Roll Fresh Short</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-mono uppercase text-slate-400">Short Folder ID</label>
                    <input
                      type="text"
                      value={studioVideoId}
                      onChange={(e) => setStudioVideoId(e.target.value)}
                      placeholder="e.g. short_08"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-mono uppercase text-slate-400">Voiceover Model (Edge-TTS)</label>
                    <select
                      value={studioVoice}
                      onChange={(e) => setStudioVoice(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white"
                    >
                      <option value="en-US-ChristopherNeural">Christopher (Deep Authoritative Male - Psychology)</option>
                      <option value="en-US-JennyNeural">Jenny (Warm Aesthetic Female - Skincare / Beauty)</option>
                      <option value="en-US-GuyNeural">Guy (Casual Storyteller - Tech / Gaming)</option>
                      <option value="en-US-AvaNeural">Ava (Modern Confident Female)</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-mono uppercase text-slate-400">Script Body</label>
                    <span className="text-xs text-slate-500 font-mono">
                      {studioScript.split(/\s+/).filter(Boolean).length} words (~{Math.round(studioScript.split(/\s+/).filter(Boolean).length / 2.7)}s)
                    </span>
                  </div>
                  <textarea
                    rows={5}
                    value={studioScript}
                    onChange={(e) => setStudioScript(e.target.value)}
                    placeholder="Paste the 40-50s script text with retention hook..."
                    className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white leading-relaxed font-sans"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-mono uppercase text-slate-400">Footage Search Keywords (Comma separated)</label>
                  <input
                    type="text"
                    value={studioKeywords}
                    onChange={(e) => setStudioKeywords(e.target.value)}
                    placeholder="e.g. dark city, robot, thinking, emergency, crowd"
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-mono uppercase text-slate-400">SEO Title (with #shorts)</label>
                    <input
                      type="text"
                      value={studioTitle}
                      onChange={(e) => setStudioTitle(e.target.value)}
                      placeholder="Title with #shorts and #tags"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-mono uppercase text-slate-400">Pinned Comment Question</label>
                    <input
                      type="text"
                      value={studioComment}
                      onChange={(e) => setStudioComment(e.target.value)}
                      placeholder="Question to drive comment debate..."
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white"
                    />
                  </div>
                </div>

                <button
                  onClick={handleStartProduction}
                  disabled={isProducing}
                  className="w-full py-3.5 rounded-xl bg-gradient-to-r from-violet-600 via-purple-600 to-cyan-500 hover:from-violet-500 hover:to-cyan-400 disabled:opacity-50 text-white font-bold text-base flex items-center justify-center space-x-2 transition shadow-xl shadow-violet-600/20"
                >
                  {isProducing ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5 fill-current" />}
                  <span>{isProducing ? 'Producing Real-Motion HD Short...' : 'Render 1080x1920 Short'}</span>
                </button>
              </div>

              {/* Progress & Log Card */}
              {taskStatus && (
                <div className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-sm text-white flex items-center space-x-2">
                      <Layers className="w-4 h-4 text-violet-400" />
                      <span>Production Pipeline Status</span>
                    </h3>
                    <span className={`text-xs font-mono uppercase font-bold px-2.5 py-1 rounded-full ${
                      taskStatus.status === 'completed'
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/60'
                        : taskStatus.status === 'failed'
                          ? 'bg-red-950 text-red-300 border border-red-800/60'
                          : taskStatus.status === 'queued'
                            ? 'bg-amber-950 text-amber-300 border border-amber-800/60 animate-pulse'
                            : 'bg-cyan-950 text-cyan-300 border border-cyan-800/60 animate-pulse'
                    }`}>
                      {taskStatus.status === 'queued' && taskStatus.queue_position
                        ? `Queued (#${taskStatus.queue_position})`
                        : taskStatus.status}
                    </span>
                  </div>

                  <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800/60">
                    <div 
                      style={{ width: `${taskStatus.progress || 0}%` }}
                      className="h-full bg-gradient-to-r from-violet-500 to-cyan-400 transition-all duration-300"
                    ></div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-black/60 border border-slate-800/80 font-mono text-xs text-slate-300 max-h-48 overflow-y-auto space-y-1">
                    {taskStatus.log?.map((l, i) => (
                      <div key={i} className={l.includes('[ERROR]') ? 'text-red-400 font-bold' : l.includes('[SUCCESS]') ? 'text-emerald-400 font-bold' : l.includes('[QUEUE]') ? 'text-amber-400 font-bold' : 'text-slate-400'}>
                        {l}
                      </div>
                    ))}
                  </div>

                  {taskStatus.status === 'completed' && (
                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
                      <span className="text-xs text-emerald-400 font-bold flex items-center space-x-1.5">
                        <Check className="w-4 h-4" />
                        <span>Render Complete</span>
                      </span>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            const v = videos.find(x => x.id === taskStatus.video_id);
                            if (v) setPreviewVideo(v);
                            else setActiveTab('vault');
                          }}
                          className="py-1.5 px-3 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-1.5 transition"
                        >
                          <Play className="w-3.5 h-3.5 fill-current" />
                          <span>Preview Video</span>
                        </button>
                        <button
                          onClick={() => handleDeleteVideo(taskStatus.video_id)}
                          className="py-1.5 px-3 rounded-lg bg-red-950/60 hover:bg-red-900/60 text-red-300 border border-red-800/60 font-bold text-xs flex items-center space-x-1.5 transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Discard / Delete</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ==================================================== */}
          {/* TAB 5: YOUTUBE DISPATCHER */}
          {/* ==================================================== */}
          {activeTab === 'dispatcher' && (
            <div className="space-y-6 max-w-3xl mx-auto">
              <div>
                <h1 className="text-2xl font-black text-white flex items-center space-x-2">
                  <Send className="w-6 h-6 text-emerald-400" />
                  <span>YouTube Direct Dispatcher</span>
                </h1>
                <p className="text-sm text-slate-400">Push verified shorts directly to channel with automated tags and scheduling</p>
              </div>

              <div className="p-6 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-5">
                <div className="space-y-1.5">
                  <label className="text-xs font-mono uppercase text-slate-400">Select Short from Vault</label>
                  <select
                    value={dispatchVideoId}
                    onChange={(e) => setDispatchVideoId(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono"
                  >
                    {videos.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.id.toUpperCase()} — {v.title} ({v.size_mb} MB)
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-xs font-mono uppercase text-slate-400">Publishing Mode</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setDispatchMode('public')}
                      className={`p-3 rounded-xl border text-left transition ${
                        dispatchMode === 'public'
                          ? 'bg-emerald-950/40 border-emerald-500 text-white shadow-lg shadow-emerald-500/10'
                          : 'bg-slate-900 border-slate-800 text-slate-400'
                      }`}
                    >
                      <div className="font-bold text-sm">Instant Public</div>
                      <div className="text-xs text-slate-400 mt-1">Hits the YouTube feed immediately (Like Short 6)</div>
                    </button>

                    <button
                      type="button"
                      onClick={() => setDispatchMode('scheduled')}
                      className={`p-3 rounded-xl border text-left transition ${
                        dispatchMode === 'scheduled'
                          ? 'bg-blue-950/40 border-blue-500 text-white shadow-lg shadow-blue-500/10'
                          : 'bg-slate-900 border-slate-800 text-slate-400'
                      }`}
                    >
                      <div className="font-bold text-sm">Automated Schedule</div>
                      <div className="text-xs text-slate-400 mt-1">Locks release time via YouTube publishAt</div>
                    </button>
                  </div>
                </div>

                {dispatchMode === 'scheduled' && (
                  <div className="space-y-1.5">
                    <label className="text-xs font-mono uppercase text-slate-400">Release Date & Time (UTC)</label>
                    <input
                      type="datetime-local"
                      value={dispatchTime}
                      onChange={(e) => setDispatchTime(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono"
                    />
                  </div>
                )}

                {!channelData?.has_youtube_token && (
                  <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-800/60 flex items-center justify-between text-xs text-amber-300">
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>YouTube OAuth token missing. Connect channel to dispatch.</span>
                    </div>
                    <button
                      onClick={() => setShowChannelModal(true)}
                      className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs transition shrink-0"
                    >
                      Connect Channel
                    </button>
                  </div>
                )}

                <button
                  onClick={channelData?.has_youtube_token ? handleUpload : () => setShowChannelModal(true)}
                  disabled={uploading}
                  className={`w-full py-3.5 rounded-xl text-white font-bold text-sm flex items-center justify-center space-x-2 transition shadow-xl ${
                    channelData?.has_youtube_token 
                      ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20' 
                      : 'bg-amber-600 hover:bg-amber-500 shadow-amber-600/20'
                  }`}
                >
                  {uploading ? (
                    <RefreshCw className="w-5 h-5 animate-spin" />
                  ) : channelData?.has_youtube_token ? (
                    <Send className="w-5 h-5" />
                  ) : (
                    <ShieldCheck className="w-5 h-5" />
                  )}
                  <span>
                    {uploading 
                      ? 'Uploading to YouTube Data API...' 
                      : channelData?.has_youtube_token 
                        ? `Dispatch ${dispatchVideoId.toUpperCase()} to Channel` 
                        : 'Connect YouTube Channel to Dispatch'}
                  </span>
                </button>
              </div>

              {/* Upload Result Alert */}
              {uploadResult && (
                <div className={`p-4 rounded-xl border text-sm ${
                  uploadResult.success 
                    ? 'bg-emerald-950/60 border-emerald-700 text-emerald-200' 
                    : 'bg-red-950/60 border-red-700 text-red-200'
                }`}>
                  {uploadResult.success ? (
                    <div className="space-y-1">
                      <div className="font-bold text-white flex items-center space-x-1.5">
                        <Check className="w-4 h-4 text-emerald-400" />
                        <span>Successfully Uploaded to YouTube!</span>
                      </div>
                      <p className="text-xs text-slate-300">
                        Watch or inspect: <a href={uploadResult.url} target="_blank" rel="noreferrer" className="underline font-mono text-cyan-300">{uploadResult.url}</a>
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <div className="font-bold text-white flex items-center space-x-1.5">
                        <AlertCircle className="w-4 h-4 text-red-400" />
                        <span>Upload Failed:</span>
                      </div>
                      <p className="text-xs font-mono">{uploadResult.error}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* ==================================================== */}
      {/* MODAL: VIDEO PREVIEW PLAYER (9:16 VERTICAL HD) */}
      {/* ==================================================== */}
      {previewVideo && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#12121a] border border-slate-800 rounded-3xl overflow-hidden max-w-md w-full shadow-2xl relative flex flex-col">
            <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-xs font-bold text-violet-400 uppercase">{previewVideo.id}</span>
                <span className="text-xs text-slate-300 truncate max-w-xs">{previewVideo.title}</span>
              </div>
              <button 
                onClick={() => setPreviewVideo(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Video Player */}
            <div className="relative bg-black flex items-center justify-center aspect-[9/16] max-h-[600px]">
              <video
                src={`/api/videos/${previewVideo.id}/stream?token=${authToken}`}
                controls
                autoPlay
                className="w-full h-full object-contain"
              />
            </div>

            <div className="p-4 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono text-slate-400">
              <span>Size: {previewVideo.size_mb} MB</span>
              <span>Format: {previewVideo.motion_type}</span>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* MODAL: GEMINI 2.5 FLASH AI SETUP (100% FREE TIER) */}
      {/* ==================================================== */}
      {showAiModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#12121a] border border-slate-800 rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl relative">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-cyan-950/60 border border-cyan-800/50">
                  <Cpu className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-extrabold text-white text-base">Gemini 3.5 Flash Lite Setup</h3>
                  <p className="text-[11px] text-cyan-400 font-mono">Ultra-Low Billing • 0.9s Speed • Zero Credit Waste</p>
                </div>
              </div>
              <button 
                onClick={() => { setShowAiModal(false); setAiKeyError(''); }} 
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Gemini 3.5 Flash Lite is <strong className="text-emerald-300">pre-configured and ready to use</strong> (zero setup required). You do not need to type anything! You can optionally paste your own private Google AI Studio key below if you wish to use your own quota:
            </p>

            {/* Error Banner */}
            {aiKeyError && (
              <div className="p-3 rounded-xl bg-red-950/50 border border-red-800/60 text-xs text-red-300 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <span className="break-all">{aiKeyError}</span>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-mono uppercase text-slate-400 flex items-center justify-between">
                <span>Google AI Studio API Key (Optional)</span>
                {aiSettings?.has_key && (
                  <span className="text-emerald-400 font-bold">
                    {aiSettings.is_custom_key ? "Custom Key Active" : "Pre-Configured System Key"}
                  </span>
                )}
              </label>
              <input
                type="password"
                value={inputApiKey}
                onChange={(e) => { setInputApiKey(e.target.value); setAiKeyError(''); }}
                placeholder={aiSettings?.has_key ? `Current: ${aiSettings.masked_key}` : "AIzaSy..."}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 outline-none text-sm text-white font-mono"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <a 
                href="https://aistudio.google.com/app/apikey" 
                target="_blank" 
                rel="noreferrer"
                className="text-xs text-cyan-400 hover:text-cyan-300 underline flex items-center space-x-1"
              >
                <span>Get Free Key (Google AI Studio)</span>
                <ExternalLink className="w-3 h-3" />
              </a>

              <div className="flex items-center space-x-2">
                {aiSettings?.is_custom_key && (
                  <button
                    onClick={handleResetAiKey}
                    disabled={savingKey}
                    className="py-2.5 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition"
                  >
                    Revert to Default
                  </button>
                )}
                <button
                  onClick={handleSaveAiKey}
                  disabled={savingKey || !inputApiKey.trim()}
                  className="py-2.5 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 font-bold text-xs text-white transition flex items-center space-x-1.5 shadow-lg shadow-cyan-600/20"
                >
                  {savingKey ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                  <span>{savingKey ? "Verifying with Google..." : "Save Key"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* MODAL: YOUTUBE CHANNEL & OAUTH CONNECTION */}
      {/* ==================================================== */}
      {showChannelModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#12121a] border border-slate-800 rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <div className="p-2 rounded-xl bg-violet-950/60 border border-violet-800/50">
                  <Film className="w-5 h-5 text-violet-400" />
                </div>
                <div>
                  <h3 className="font-extrabold text-white text-base">Channel & YouTube Connection</h3>
                  <p className="text-[11px] text-violet-400 font-mono">Isolated Per User • Private Upload Token & Stats</p>
                </div>
              </div>
              <button 
                onClick={() => { setShowChannelModal(false); setOauthStep('initial'); setTokenUploadError(''); }} 
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Connect your YouTube Channel via credentials file or OAuth token. Every account has its own isolated upload target and quota.
            </p>

            {/* CHANNEL HANDLE INPUT */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono uppercase text-slate-400 flex items-center justify-between">
                <span>YouTube Channel Handle</span>
                <span className="text-slate-500 font-mono text-[10px]">e.g. @MyChannel</span>
              </label>
              <input
                type="text"
                value={inputChannelHandle}
                onChange={(e) => setInputChannelHandle(e.target.value)}
                placeholder="@MyYouTubeChannel"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono"
              />
            </div>

            {/* ERROR DISPLAY */}
            {tokenUploadError && (
              <div className="p-3 rounded-xl bg-red-950/50 border border-red-800/60 text-xs text-red-300 flex items-start space-x-2">
                <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                <span className="break-all">{tokenUploadError}</span>
              </div>
            )}

            {/* OAUTH CREDENTIALS SECTION */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-mono uppercase text-slate-400">
                  <span>YouTube OAuth Status</span>
                </label>
                {channelData?.has_youtube_token ? (
                  <span className="text-emerald-400 font-bold text-xs flex items-center space-x-1">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                    <span>Connected</span>
                  </span>
                ) : (
                  <span className="text-amber-400 font-bold text-xs">Not Connected</span>
                )}
              </div>

              {channelData?.has_youtube_token && !showChangeCredentials ? (
                <div className="p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-xs text-emerald-300 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>OAuth token active and verified for uploads.</span>
                  </div>
                  <div className="flex items-center space-x-1.5">
                    <button
                      onClick={() => setShowChangeCredentials(true)}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
                    >
                      Update
                    </button>
                    <button
                      onClick={handleDisconnectYoutube}
                      className="px-2.5 py-1 rounded-lg bg-red-950/60 border border-red-800/60 hover:bg-red-900 text-red-300 text-xs transition"
                    >
                      Disconnect
                    </button>
                  </div>
                </div>
              ) : oauthStep === 'awaiting_code' ? (
                /* STEP 2: AUTHORIZE ON GOOGLE AND PASTE CODE */
                <div className="p-4 rounded-2xl bg-violet-950/20 border border-violet-800/40 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-violet-300 uppercase tracking-wider">Step 2 · Google Authorization</span>
                    <button 
                      onClick={() => setOauthStep('initial')}
                      className="text-[11px] text-slate-400 hover:text-white underline"
                    >
                      Back
                    </button>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed">
                    1. Click the button below to authorize YouTube access with your Google account in a new tab:
                  </p>

                  <a
                    href={oauthAuthUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-violet-600 hover:bg-violet-500 font-bold text-xs text-white shadow-lg shadow-violet-600/30 transition text-center"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>Authorize Channel on Google</span>
                  </a>

                  <div className="pt-2 border-t border-slate-800/80 space-y-2">
                    <p className="text-[11px] text-slate-400 leading-relaxed">
                      2. After approving, Google redirects to <code className="text-violet-300 font-mono">http://localhost/?code=...</code>. Even if browser shows &quot;Site can&apos;t be reached&quot;, copy the entire URL or code from the address bar and paste here:
                    </p>
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={inputOauthCode}
                        onChange={(e) => setInputOauthCode(e.target.value)}
                        placeholder="Paste code=... or full http://localhost/?code=..."
                        className="flex-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-xs text-white font-mono"
                      />
                      <button
                        onClick={handleCompleteOauthCode}
                        disabled={exchangingOauth || !inputOauthCode.trim()}
                        className="py-2 px-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 font-bold text-xs text-white transition flex items-center space-x-1.5 shrink-0 shadow-lg"
                      >
                        {exchangingOauth ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                        <span>Finish</span>
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                /* INITIAL STEP: UPLOAD TOKEN OR CLIENT SECRET FILE */
                <div className="space-y-3">
                  {/* DRAG & DROP / FILE UPLOADER */}
                  <label className="relative border-2 border-dashed border-violet-800/40 hover:border-violet-500/70 bg-violet-950/10 hover:bg-violet-950/20 rounded-2xl p-5 flex flex-col items-center justify-center text-center cursor-pointer transition group">
                    <input
                      type="file"
                      accept=".json"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files?.[0]) {
                          handleTokenFileUpload(e.target.files[0]);
                        }
                      }}
                    />
                    <div className="p-3 rounded-full bg-violet-900/30 text-violet-400 group-hover:scale-110 transition duration-200 mb-2">
                      {uploadingTokenFile ? (
                        <RefreshCw className="w-5 h-5 animate-spin text-violet-300" />
                      ) : (
                        <Upload className="w-5 h-5" />
                      )}
                    </div>
                    <span className="text-xs font-bold text-white group-hover:text-violet-300 transition">
                      {uploadingTokenFile ? "Reading & processing file..." : "Click or drop credential JSON file here"}
                    </span>
                    <span className="text-[11px] text-slate-400 mt-1">
                      Upload <code className="text-violet-400">token.json</code> or Google Cloud <code className="text-violet-400">client_secret_XXXX.json</code>
                    </span>
                  </label>

                  {/* QUICK 1-CLICK AUTH BUTTON IF SERVER CLIENT_SECRET EXISTS */}
                  {channelData?.has_client_secret && (
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                      <div className="flex items-center space-x-2 text-slate-300">
                        <Key className="w-4 h-4 text-violet-400" />
                        <span>Google Client Credentials detected</span>
                      </div>
                      <button
                        onClick={handleStartGoogleAuth}
                        disabled={uploadingTokenFile}
                        className="py-1.5 px-3 rounded-lg bg-violet-600 hover:bg-violet-500 font-bold text-xs text-white transition flex items-center space-x-1"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        <span>Connect Google Account</span>
                      </button>
                    </div>
                  )}

                  {/* TOGGLE MANUAL TEXTAREA */}
                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={() => setShowManualJson(!showManualJson)}
                      className="text-[11px] text-slate-400 hover:text-slate-200 underline font-mono"
                    >
                      {showManualJson ? "Hide manual JSON input" : "Or paste JSON credentials manually"}
                    </button>
                    {showManualJson && (
                      <textarea
                        rows={3}
                        value={inputYoutubeToken}
                        onChange={(e) => setInputYoutubeToken(e.target.value)}
                        placeholder='Paste contents of token.json or client_secret.json here'
                        className="mt-2 w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-xs text-white font-mono"
                      />
                    )}
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                onClick={() => { setShowChannelModal(false); setOauthStep('initial'); setTokenUploadError(''); }}
                className="py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 font-bold text-xs text-slate-300 transition"
              >
                Close
              </button>
              <button
                onClick={handleSaveChannel}
                disabled={savingChannel || uploadingTokenFile || exchangingOauth}
                className="py-2.5 px-5 rounded-xl bg-violet-600 hover:bg-violet-500 font-bold text-xs text-white transition flex items-center space-x-1.5 shadow-lg shadow-violet-600/20"
              >
                {savingChannel ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                <span>Save Channel</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* FLOATING MINI RENDER STATUS BAR */}
      {/* ==================================================== */}
      {isProducing && activeTab !== 'studio' && (
        <div 
          onClick={() => setActiveTab('studio')}
          className="fixed bottom-6 left-6 z-50 bg-[#12121a]/95 border border-cyan-500/60 shadow-2xl shadow-cyan-950/70 rounded-2xl p-3.5 flex items-center space-x-3.5 cursor-pointer hover:border-cyan-400 transition group backdrop-blur-md max-w-sm"
        >
          <div className="relative flex items-center justify-center p-2 rounded-xl bg-cyan-950/70 border border-cyan-800/60 text-cyan-400">
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="font-bold text-white uppercase">{studioVideoId}</span>
              <span className="text-cyan-400 font-bold">{taskStatus?.progress || 0}%</span>
            </div>
            <p className="text-[11px] text-slate-400 truncate mt-0.5">
              {taskStatus?.log?.[taskStatus.log.length - 1] || 'Rendering video in studio...'}
            </p>
          </div>
          <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-0.5 transition" />
        </div>
      )}

      {/* ==================================================== */}
      {/* FLOATING TOAST NOTIFICATIONS */}
      {/* ==================================================== */}
      <div className="fixed bottom-6 right-6 z-[100] flex flex-col space-y-2 pointer-events-none max-w-sm w-full">
        {toasts.map(t => (
          <div
            key={t.id}
            className={`pointer-events-auto p-3.5 rounded-2xl border shadow-2xl flex items-center space-x-3 backdrop-blur-md transition-all duration-300 transform translate-y-0 ${
              t.type === 'success'
                ? 'bg-emerald-950/90 border-emerald-500/50 text-emerald-200 shadow-emerald-950/50'
                : t.type === 'error'
                ? 'bg-rose-950/90 border-rose-500/50 text-rose-200 shadow-rose-950/50'
                : 'bg-slate-900/90 border-slate-700/60 text-slate-200 shadow-black/60'
            }`}
          >
            {t.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
            {t.type === 'error' && <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />}
            {t.type === 'info' && <Info className="w-4 h-4 text-cyan-400 shrink-0" />}
            <span className="text-xs font-medium leading-snug flex-1">{t.message}</span>
            <button
              onClick={() => setToasts(prev => prev.filter(x => x.id !== t.id))}
              className="text-slate-400 hover:text-white p-0.5"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
