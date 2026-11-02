import React, { useEffect } from 'react';
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { 
  Film, Eye, Cpu, RefreshCw, BarChart3, Video, Sparkles, Sliders, Send, 
  Clock, ShieldCheck, ExternalLink, ChevronRight 
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import AiModal from './AiModal';
import ChannelModal from './ChannelModal';
import VideoPreviewModal from './VideoPreviewModal';
import ToastContainer from './ToastContainer';

export default function Layout() {
  const {
    currentUser, handleLogout,
    stats, loadingStats, fetchStats,
    videos, fetchVideos,
    usage, loadingUsage, fetchUsage,
    channelData,
    aiSettings, showAiModal, setShowAiModal,
    inputApiKey, setInputApiKey, savingKey, aiKeyError, setAiKeyError,
    handleSaveAiKey, handleResetAiKey,
    showChannelModal, setShowChannelModal,
    inputChannelHandle, setInputChannelHandle,
    tokenUploadError, setTokenUploadError,
    showChangeCredentials, setShowChangeCredentials,
    oauthStep, setOauthStep,
    oauthAuthUrl, inputOauthCode, setInputOauthCode,
    exchangingOauth, uploadingTokenFile,
    showManualJson, setShowManualJson,
    inputYoutubeToken, setInputYoutubeToken,
    savingChannel, handleTokenFileUpload, handleStartGoogleAuth,
    handleCompleteOauthCode, handleSaveChannel, handleDisconnectYoutube,
    previewVideo, setPreviewVideo, authToken,
    toasts, closeToast,
    isProducing, studioVideoId, taskStatus
  } = useApp();

  const navigate = useNavigate();
  const location = useLocation();

  // Keyboard navigation & modal shortcuts
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
        navigate('/overview');
      } else if (e.key === '2') {
        navigate('/vault');
      } else if (e.key === '3') {
        navigate('/ideas');
      } else if (e.key === '4') {
        navigate('/studio');
      } else if (e.key === '5') {
        navigate('/dispatcher');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate, setPreviewVideo, setShowAiModal, setShowChannelModal]);

  const getNavClass = ({ isActive }) =>
    `w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
      isActive
        ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/10 text-violet-300 border border-violet-500/30'
        : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
    }`;

  return (
    <div className="min-h-screen bg-[#09090e] text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="h-16 border-b border-slate-800/80 bg-[#0d0d14]/90 backdrop-blur sticky top-0 z-40 px-6 flex items-center justify-between">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => navigate('/overview')}>
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
                onClick={handleLogout}
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
            <NavLink to="/overview" className={getNavClass}>
              <BarChart3 className="w-4 h-4" />
              <span>Overview & Views</span>
            </NavLink>

            <NavLink to="/vault" className={getNavClass}>
              <Video className="w-4 h-4" />
              <div className="flex-1 flex justify-between items-center">
                <span>Video Vault</span>
                <span className="text-[11px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                  {videos.length}
                </span>
              </div>
            </NavLink>

            <NavLink to="/ideas" className={getNavClass}>
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>Niche & Idea Lab</span>
            </NavLink>

            <NavLink to="/studio" className={getNavClass}>
              <Sliders className="w-4 h-4 text-cyan-400" />
              <div className="flex-1 flex justify-between items-center">
                <span>Studio Generator</span>
                {isProducing && (
                  <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
                )}
              </div>
            </NavLink>

            <NavLink to="/dispatcher" className={getNavClass}>
              <Send className="w-4 h-4 text-emerald-400" />
              <span>YouTube Dispatcher</span>
            </NavLink>
          </nav>

          {/* Daily Quotas & Credits Tracker */}
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

            {/* Gemini Flash Quota */}
            <div className="space-y-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400 flex items-center space-x-1">
                  <span className={`w-1.5 h-1.5 rounded-full ${usage?.gemini?.has_key ? 'bg-cyan-400 animate-pulse' : 'bg-slate-600'}`}></span>
                  <span>Gemini 3.1 Flash Lite</span>
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
                <span>Cap: {usage?.gemini?.limit ? `${usage.gemini.limit.toLocaleString()}/day` : '500/day'}</span>
              </div>
            </div>

            {/* YouTube Data API v3 Quota */}
            <div className="space-y-1 pt-2 border-t border-slate-800/60">
              <div className="flex items-center justify-between text-[11px] gap-1 flex-wrap">
                <span className="text-slate-400 flex items-center space-x-1.5 min-w-0 shrink">
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${usage?.youtube?.connected ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
                  <span className="truncate">YouTube API</span>
                  {usage?.youtube?.is_live && (
                    <span 
                      className="text-[9px] font-mono px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 whitespace-nowrap shrink-0 flex items-center space-x-1 shadow-sm"
                      title="Genuine source of truth synced with Google Cloud Monitoring API"
                    >
                      <span className="w-1 h-1 rounded-full bg-emerald-400"></span>
                      <span><strong className="font-bold hidden sm:inline">GCP </strong>LIVE</span>
                    </span>
                  )}
                </span>
                {usage && usage.youtube?.connected === false ? (
                  <button 
                    onClick={() => setShowChannelModal(true)}
                    className="text-[10px] font-mono font-bold text-amber-400 hover:text-amber-300 underline shrink-0"
                  >
                    Not Linked
                  </button>
                ) : (
                  <span className="font-mono font-bold text-emerald-400 whitespace-nowrap shrink-0">
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
          <Outlet />
        </main>
      </div>

      {/* Floating Mini Render Status Bar */}
      {isProducing && location.pathname !== '/studio' && (
        <div 
          onClick={() => navigate('/studio')}
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

      {/* All Modals */}
      <AiModal
        isOpen={showAiModal}
        onClose={() => setShowAiModal(false)}
        aiSettings={aiSettings}
        inputApiKey={inputApiKey}
        setInputApiKey={setInputApiKey}
        savingKey={savingKey}
        aiKeyError={aiKeyError}
        setAiKeyError={setAiKeyError}
        onSave={handleSaveAiKey}
        onReset={handleResetAiKey}
      />

      <ChannelModal
        isOpen={showChannelModal}
        onClose={() => setShowChannelModal(false)}
        channelData={channelData}
        inputChannelHandle={inputChannelHandle}
        setInputChannelHandle={setInputChannelHandle}
        tokenUploadError={tokenUploadError}
        setTokenUploadError={setTokenUploadError}
        showChangeCredentials={showChangeCredentials}
        setShowChangeCredentials={setShowChangeCredentials}
        oauthStep={oauthStep}
        setOauthStep={setOauthStep}
        oauthAuthUrl={oauthAuthUrl}
        inputOauthCode={inputOauthCode}
        setInputOauthCode={setInputOauthCode}
        exchangingOauth={exchangingOauth}
        uploadingTokenFile={uploadingTokenFile}
        showManualJson={showManualJson}
        setShowManualJson={setShowManualJson}
        inputYoutubeToken={inputYoutubeToken}
        setInputYoutubeToken={setInputYoutubeToken}
        savingChannel={savingChannel}
        handleTokenFileUpload={handleTokenFileUpload}
        handleStartGoogleAuth={handleStartGoogleAuth}
        handleCompleteOauthCode={handleCompleteOauthCode}
        handleSaveChannel={handleSaveChannel}
        handleDisconnectYoutube={handleDisconnectYoutube}
      />

      <VideoPreviewModal
        previewVideo={previewVideo}
        authToken={authToken}
        onClose={() => setPreviewVideo(null)}
      />

      <ToastContainer toasts={toasts} onClose={closeToast} />
    </div>
  );
}

