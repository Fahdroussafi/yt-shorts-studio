import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Radio, Scissors, RefreshCw, Play, Sparkles } from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function StreamVodsPage() {
  const { authFetch, authToken, showToast, fetchVideos, setPreviewVideo } = useApp();
  const navigate = useNavigate();

  const [channelInput, setChannelInput] = useState(() => localStorage.getItem('gta_twitch_channel') || '');
  const [loadingVods, setLoadingVods] = useState(false);
  const [scanningHighlights, setScanningHighlights] = useState(false);
  const [vods, setVods] = useState([]);
  const [clips, setClips] = useState([]);
  const [highlights, setHighlights] = useState([]);
  const [selectedVod, setSelectedVod] = useState(null);
  const [activeTask, setActiveTask] = useState(null);

  useEffect(() => {
    if (!activeTask?.task_id || activeTask.status === 'completed' || activeTask.status === 'failed') return;
    const iv = setInterval(async () => {
      try {
        const res = await authFetch(`/api/produce/status/${activeTask.task_id}`);
        if (res.ok) {
          const data = await res.json();
          setActiveTask(data);
          if (data.status === 'completed') {
            showToast(`Stream Short ${data.video_id?.toUpperCase()} ready in Vault!`, 'success');
            fetchVideos();
          } else if (data.status === 'failed') {
            showToast(data.error || 'VOD render failed', 'error');
          }
        }
      } catch {}
    }, 1500);
    return () => clearInterval(iv);
  }, [activeTask, authFetch, fetchVideos, showToast]);

  const handleLoadVods = async (e) => {
    e?.preventDefault();
    if (!channelInput.trim()) return showToast('Enter your Twitch username or VOD URL.', 'error');
    localStorage.setItem('gta_twitch_channel', channelInput.trim());
    setLoadingVods(true);
    try {
      const res = await authFetch('/api/vod/inspect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_or_url: channelInput.trim() }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setVods(data.vods || []);
      setClips(data.clips || []);
      setHighlights([]);
      if (data.vods?.length > 0) setSelectedVod(data.vods[0]);
      else showToast('No past broadcasts found. Enable "Store past broadcasts" in Twitch settings.', 'info');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoadingVods(false);
    }
  };

  const handleFindHighlights = async (vodObj) => {
    const target = vodObj || selectedVod;
    if (!target?.url) return showToast('Select a VOD first.', 'error');
    setSelectedVod(target);
    setScanningHighlights(true);
    try {
      const res = await authFetch('/api/vod/highlights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vod_url: target.url }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      const found = data.highlights || [];
      setHighlights(found);
      if (found.length > 0) showToast(`Found ${found.length} best moments!`, 'success');
      else showToast('No strong spikes detected in this VOD.', 'info');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setScanningHighlights(false);
    }
  };

  const handleCutHighlight = async (h) => {
    const vodUrl = h.url || selectedVod?.url || (channelInput.includes('twitch.tv/videos/') ? channelInput.trim() : '');
    if (!vodUrl) return showToast('Select a VOD first.', 'error');
    setActiveTask({ task_id: null, status: 'queued', progress: 5, log: [`Queueing ${h.start}–${h.end}...`] });
    try {
      const res = await authFetch('/api/vod/produce', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vod_url: vodUrl,
          vod_title: h.title || selectedVod?.title || undefined,
          game_name: h.game_name || undefined,
          start_time: h.start,
          end_time: h.end,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setActiveTask({ task_id: data.task_id, video_id: data.video_id, status: 'queued', progress: 10, log: ['Queued VOD slice render...'] });
    } catch (err) {
      setActiveTask(null);
      showToast(err.message, 'error');
    }
  };

  const busy = activeTask?.status === 'queued' || activeTask?.status === 'processing';

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-white flex items-center space-x-2">
          <Radio className="w-6 h-6 text-purple-400" />
          <span>Xbox Stream VOD Clipper</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Auto-detects top moments from your Twitch Series X streams and renders 1080×1920 Cinema Frame Shorts.
        </p>
      </div>

      <form onSubmit={handleLoadVods} className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          value={channelInput}
          onChange={(e) => setChannelInput(e.target.value)}
          placeholder="Your Twitch username (e.g. Cryjin01) or VOD URL"
          className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-purple-500 outline-none text-sm text-white font-mono"
        />
        <button
          type="submit"
          disabled={loadingVods}
          className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-sm flex items-center justify-center space-x-2 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loadingVods ? 'animate-spin' : ''}`} />
          <span>{loadingVods ? 'Scanning...' : 'Load Stream VODs'}</span>
        </button>
      </form>

      {vods.length > 0 && (
        <div className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {vods.map((v) => {
              const active = selectedVod?.id === v.id;
              return (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => setSelectedVod(v)}
                  className={`p-3.5 rounded-xl border text-left transition ${
                    active ? 'bg-purple-950/40 border-purple-500 text-white' : 'bg-[#12121a] border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold text-sm truncate">{v.title}</div>
                  <div className="text-xs font-mono text-slate-400 mt-1 flex items-center justify-between">
                    <span>VOD #{v.id}</span>
                    <span>{v.duration_str}</span>
                  </div>
                </button>
              );
            })}
          </div>
          {selectedVod && (
            <button
              type="button"
              onClick={() => handleFindHighlights(selectedVod)}
              disabled={scanningHighlights}
              className="w-full py-3 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-sm flex items-center justify-center space-x-2 transition disabled:opacity-50"
            >
              <Sparkles className={`w-4 h-4 ${scanningHighlights ? 'animate-spin' : ''}`} />
              <span>{scanningHighlights ? 'Scanning Visual + Audio Peaks...' : `Auto-Find Best Moments in VOD #${selectedVod.id}`}</span>
            </button>
          )}
        </div>
      )}

      {clips.length > 0 && (
        <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-3">
          <div className="text-xs font-mono uppercase text-purple-400">Your Channel Clips</div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {clips.map((c) => (
              <div key={c.id} className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-sm font-bold text-white truncate">{c.title}</div>
                  <div className="text-[11px] font-mono text-slate-400">
                    {c.game_name || 'Stream Clip'} · {c.duration_str} · {c.view_count} views
                  </div>
                </div>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => handleCutHighlight({ start: '00:00', end: c.duration_str, url: c.url, title: c.title, game_name: c.game_name })}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white inline-flex items-center space-x-1 shrink-0 disabled:opacity-50"
                >
                  <Scissors className="w-3.5 h-3.5" /><span>Cut & Render</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {highlights.length > 0 && (
        <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-3">
          <div className="text-xs font-mono uppercase text-amber-400 flex items-center space-x-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Auto-Detected Best Moments (Visual + Game Audio Peaks)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {highlights.map((h, i) => (
              <div key={i} className="p-3 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-sm font-mono font-bold text-white">{h.start} – {h.end}</div>
                  <div className="text-[11px] font-mono text-slate-400">
                    Score {h.score} · Visual {h.visual_z} · Audio {h.audio_spike}x
                  </div>
                </div>
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => handleCutHighlight(h)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white inline-flex items-center space-x-1 shrink-0 disabled:opacity-50"
                >
                  <Scissors className="w-3.5 h-3.5" /><span>Cut & Render</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTask && (
        <div className="p-4 rounded-xl bg-[#12121a] border border-slate-800 space-y-2 text-xs font-mono">
          <div className="flex justify-between text-slate-300">
            <span>{activeTask.video_id?.toUpperCase() || 'VOD'} — {activeTask.status?.toUpperCase()}</span>
            <span>{activeTask.progress || 0}%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 transition-all" style={{ width: `${activeTask.progress || 0}%` }} />
          </div>
          {(activeTask.log || []).slice(-3).map((l, idx) => (
            <div key={idx} className="text-slate-400">{l}</div>
          ))}
          {activeTask.status === 'completed' && activeTask.video_id && (
            <div className="pt-3 space-y-3">
              <video
                src={`/api/videos/${activeTask.video_id}/stream?token=${authToken}`}
                controls
                playsInline
                className="w-full max-w-[260px] rounded-xl border border-slate-800 bg-black aspect-[9/16]"
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setPreviewVideo({ id: activeTask.video_id, title: activeTask.output_file || activeTask.video_id })}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold inline-flex items-center space-x-1"
                >
                  <Play className="w-3.5 h-3.5" /><span>Full Preview</span>
                </button>
                <button
                  type="button"
                  onClick={() => navigate('/vault')}
                  className="px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-bold inline-flex items-center space-x-1"
                >
                  <span>Open in Vault</span>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
