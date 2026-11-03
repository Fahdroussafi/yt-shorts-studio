import React, { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext(null);

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}

export function AppProvider({ children }) {
  // Authentication State
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('yt_studio_jwt') || '');
  const [currentUser, setCurrentUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);

  // Toast Notification System
  const [toasts, setToasts] = useState([]);
  const showToast = (message, type = 'info') => {
    const id = Date.now() + Math.random().toString(36).substring(2, 6);
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3800);
  };
  const closeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const handleLogout = () => {
    localStorage.removeItem('yt_studio_jwt');
    setAuthToken('');
    setCurrentUser(null);
    setStats(null);
    setVideos([]);
    setUsage(null);
    setAiSettings(null);
    setChannelData({ channel_handle: '', channel_url: '', has_youtube_token: false, has_client_secret: false });
    setInputChannelHandle('');
    setInputYoutubeToken('');
    setGeneratedIdea(null);
    setStudioVideoId('short_01');
    setStudioScript('');
    setStudioTitle('');
    setStudioDesc('');
    setDispatchVideoId('');
    setUploadResult(null);
    setActiveTaskId(null);
    setTaskStatus(null);
    setIsProducing(false);
    setPreviewVideo(null);
  };

  // Authenticated fetch wrapper
  const authFetch = (url, options = {}) => {
    const headers = { ...(options.headers || {}) };
    if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }
    return fetch(url, { ...options, headers }).then(res => {
      if (res.status === 401) {
        handleLogout();
        throw new Error('Unauthorized');
      }
      return res;
    });
  };

  // Global Data State
  const [stats, setStats] = useState(null);
  const [videos, setVideos] = useState([]);
  const [niches, setNiches] = useState([]);
  const [loadingStats, setLoadingStats] = useState(false);
  const [loadingVideos, setLoadingVideos] = useState(false);
  const [usage, setUsage] = useState(null);
  const [loadingUsage, setLoadingUsage] = useState(false);
  const [syncingChannel, setSyncingChannel] = useState(false);

  // Modals & Popups
  const [previewVideo, setPreviewVideo] = useState(null);
  const [copiedId, setCopiedId] = useState(null);
  const [showAiModal, setShowAiModal] = useState(false);
  const [showChannelModal, setShowChannelModal] = useState(false);

  // AI Flash Model State
  const [aiSettings, setAiSettings] = useState(null);
  const [inputApiKey, setInputApiKey] = useState('');
  const [savingKey, setSavingKey] = useState(false);
  const [aiKeyError, setAiKeyError] = useState('');

  // Channel Connection State
  const [channelData, setChannelData] = useState({ channel_handle: '', channel_url: '', has_youtube_token: false, has_client_secret: false });
  const [inputChannelHandle, setInputChannelHandle] = useState('');
  const [inputYoutubeToken, setInputYoutubeToken] = useState('');
  const [savingChannel, setSavingChannel] = useState(false);
  const [oauthStep, setOauthStep] = useState('initial');
  const [oauthAuthUrl, setOauthAuthUrl] = useState('');
  const [inputOauthCode, setInputOauthCode] = useState('');
  const [exchangingOauth, setExchangingOauth] = useState(false);
  const [uploadingTokenFile, setUploadingTokenFile] = useState(false);
  const [tokenUploadError, setTokenUploadError] = useState('');
  const [showManualJson, setShowManualJson] = useState(false);
  const [showChangeCredentials, setShowChangeCredentials] = useState(false);

  // Idea Lab State
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
  const [scheduleRec, setScheduleRec] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  // FIX: Prevent background scrolling whenever ANY modal is active
  useEffect(() => {
    const isAnyModalOpen = Boolean(showAiModal || showChannelModal || previewVideo);
    if (isAnyModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [showAiModal, showChannelModal, previewVideo]);

  // Auth Verification on mount
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
        handleLogout();
        setAuthChecking(false);
      });
  }, []);

  // Fetch initial data when authenticated
  useEffect(() => {
    if (!authToken) return;
    fetchStats();
    fetchVideos();
    fetchNiches();
    fetchAiSettings();
    fetchChannelSettings();
    fetchUsage();
    fetchScheduleRec();
  }, [authToken]);

  // Background Telemetry Sync every 45s
  useEffect(() => {
    if (!authToken) return;
    const interval = setInterval(() => {
      fetchStats();
    }, 45000);
    return () => clearInterval(interval);
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

  // API Call Handlers
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

  const fetchScheduleRec = async () => {
    try {
      const res = await authFetch('/api/schedule/recommendation');
      if (res.ok) {
        const data = await res.json();
        setScheduleRec(data);
        if (data.recommended_slot && !dispatchTime) {
          setDispatchTime(data.recommended_slot.input_val);
        }
      }
    } catch (e) {
      console.error("Schedule recommendation fetch error:", e);
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
    const handleTrimmed = inputChannelHandle.trim();
    const tokenTrimmed = inputYoutubeToken.trim();

    if (!handleTrimmed && !tokenTrimmed) {
      showToast("Please enter a YouTube handle or upload credentials.", "warning");
      return;
    }

    setSavingChannel(true);
    setTokenUploadError('');
    try {
      if (handleTrimmed) {
        const hRes = await authFetch('/api/settings/channel', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ channel_handle: handleTrimmed })
        });
        const hData = await hRes.json();
        if (!hRes.ok) {
          throw new Error(hData.detail || hData.message || "Failed to save channel handle.");
        }
      }
      if (tokenTrimmed) {
        const res = await authFetch('/api/settings/youtube-token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token_json: tokenTrimmed })
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

  const handleSyncChannel = async () => {
    setSyncingChannel(true);
    showToast("Scanning YouTube channel for published shorts...", "info");
    try {
      const res = await authFetch('/api/channel/sync', { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || `Channel sync complete! Restored ${data.restored_count || 0} videos.`, "success");
        await fetchStats();
      } else {
        showToast(`Sync failed: ${data.detail || 'Could not query channel.'}`, "error");
      }
    } catch (e) {
      showToast(`Network error syncing channel: ${e.message}`, "error");
    } finally {
      setSyncingChannel(false);
    }
  };

  const copyMetadata = (v) => {
    const text = `TITLE:\n${v.title}\n\nDESCRIPTION:\n${v.description}\n\nPINNED COMMENT:\n${v.pinned_comment}`;
    navigator.clipboard.writeText(text);
    setCopiedId(v.id);
    showToast(`Copied SEO metadata for ${v.id}!`, "success");
    setTimeout(() => setCopiedId(null), 2000);
  };

  // FIX: Immediate optimistic update on delete so Overview & Vault update instantly without manual F5
  const handleDeleteVideo = async (videoId) => {
    if (!window.confirm(`Delete local media files for '${videoId}' from server disk?\n\nNote: If this video is already published or scheduled on YouTube, its view tracking, channel stats, and telemetry history will be safely preserved in your dashboard.`)) {
      return;
    }
    try {
      const res = await authFetch(`/api/videos/${videoId}`, { method: 'DELETE' });
      const data = await res.json();
      if (res.ok) {
        showToast(data.message || `Local files for ${videoId} purged from disk.`, "success");
        if (previewVideo?.id === videoId) {
          setPreviewVideo(null);
        }

        // Optimistic cache eviction
        setVideos(prev => prev.filter(v => v.id !== videoId));
        setStats(prev => prev ? {
          ...prev,
          videos: (prev.videos || []).filter(v => v.short_id !== videoId && v.id !== videoId)
        } : prev);

        fetchVideos();
        fetchStats();
      } else {
        showToast(`Failed to delete: ${data.detail}`, "error");
      }
    } catch (e) {
      showToast(`Error deleting: ${e.message}`, "error");
    }
  };

  const handleGenerateIdea = async (overrideNiche = null, isSurprise = false) => {
    setGeneratingIdea(true);
    try {
      const targetNiche = overrideNiche || selectedNiche;
      const res = await authFetch('/api/ideas/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          niche: targetNiche,
          concept: isSurprise ? '' : ideaConcept,
          surprise: isSurprise
        })
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

  const sendIdeaToStudio = (idea, navigate) => {
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
    if (navigate) {
      navigate('/studio');
    }
  };

  const handleQuickProduce = async (idea, navigate) => {
    sendIdeaToStudio(idea, navigate);
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
          voice: idea.voice || studioVoice,
          niche: idea.niche || selectedNiche
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
          voice: studioVoice,
          niche: selectedNiche
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
      const formatPublishAt = (t) => {
        if (!t) return null;
        if (t.includes('Z')) return t;
        return `${t.replace(' ', 'T')}${t.length === 16 ? ':00.000Z' : 'Z'}`;
      };

      const payload = {
        video_id: dispatchVideoId,
        privacy_status: dispatchMode,
        publish_at: dispatchMode === 'scheduled' && dispatchTime ? formatPublishAt(dispatchTime) : null
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

  const value = {
    authToken, setAuthToken,
    currentUser, setCurrentUser,
    authChecking, setAuthChecking,
    handleLogout,
    authFetch,
    toasts, showToast, closeToast,
    stats, setStats, loadingStats, fetchStats,
    videos, setVideos, loadingVideos, fetchVideos,
    usage, loadingUsage, fetchUsage,
    niches, fetchNiches,
    scheduleRec, fetchScheduleRec,
    previewVideo, setPreviewVideo,
    copiedId, copyMetadata,
    handleDeleteVideo,
    syncingChannel, handleSyncChannel,
    aiSettings, setAiSettings, showAiModal, setShowAiModal,
    inputApiKey, setInputApiKey, savingKey, aiKeyError, setAiKeyError,
    handleSaveAiKey, handleResetAiKey,
    channelData, setChannelData, showChannelModal, setShowChannelModal,
    inputChannelHandle, setInputChannelHandle,
    inputYoutubeToken, setInputYoutubeToken,
    savingChannel, oauthStep, setOauthStep,
    oauthAuthUrl, inputOauthCode, setInputOauthCode,
    exchangingOauth, uploadingTokenFile, tokenUploadError, setTokenUploadError,
    showManualJson, setShowManualJson,
    showChangeCredentials, setShowChangeCredentials,
    handleTokenFileUpload, handleStartGoogleAuth, handleCompleteOauthCode,
    handleSaveChannel, handleDisconnectYoutube,
    selectedNiche, setSelectedNiche,
    ideaConcept, setIdeaConcept,
    generatingIdea, generatedIdea,
    handleGenerateIdea, autoGenerateAndFillStudio,
    sendIdeaToStudio, handleQuickProduce,
    studioVideoId, setStudioVideoId,
    studioVoice, setStudioVoice,
    studioScript, setStudioScript,
    studioKeywords, setStudioKeywords,
    studioTitle, setStudioTitle,
    studioDesc, setStudioDesc,
    studioComment, setStudioComment,
    activeTaskId, taskStatus, isProducing, handleStartProduction,
    dispatchVideoId, setDispatchVideoId,
    dispatchMode, setDispatchMode,
    dispatchTime, setDispatchTime,
    uploading, uploadResult, handleUpload
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

