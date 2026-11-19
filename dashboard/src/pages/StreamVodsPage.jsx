import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Radio, Scissors, RefreshCw, Play, Sparkles, Clock } from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function StreamVodsPage() {
  const { authFetch, showToast, fetchVideos } = useApp();
  const navigate = useNavigate();

  const [channelInput, setChannelInput] = useState(() => localStorage.getItem('gta_twitch_channel') || '');
  const [loadingVods, setLoadingVods] = useState(false);
  const [scanningHighlights, setScanningHighlights] = useState(false);
  const [vods, setVods] = useState([]);
  const [highlights, setHighlights] = useState([]);
  const [selectedVod, setSelectedVod] = useState(null);

  const [startTime, setStartTime] = useState('00:00');
  const [endTime, setEndTime] = useState('00:30');
  const [hookBanner, setHookBanner] = useState('WAIT FOR THE ENDING');
  const [title, setTitle] = useState('');
  const [ttsHook, setTtsHook] = useState('');
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
      if (found.length > 0) {
        setStartTime(found[0].start);
        setEndTime(found[0].end);
        showToast(`Found ${found.length} best moments!`, 'success');
      } else {
        showToast('No strong spikes detected in this VOD.', 'info');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setScanningHighlights(false);
    }
  };

  const handleProduceVod = async (customStart, customEnd) => {
    const vodUrl = selectedVod?.url || (channelInput.includes('twitch.tv/videos/') ? channelInput.trim() : '');
    if (!vodUrl) return showToast('Select a VOD or paste a Twitch VOD URL first.', 'error');
    const st = typeof customStart === 'string' ? customStart : startTime;
    const et = typeof customEnd === 'string' ? customEnd : endTime;
    setActiveTask({ task_id: null, status: 'queued', progress: 5, log: ['Queueing VOD slice...'] });
    try {
      const res = await authFetch('/api/vod/produce', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vod_url: vodUrl,
          start_time: st,
          end_time: et,
          hook_banner: hookBanner,
          title: title || undefined,
          tts_hook: ttsHook || undefined,
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

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-white flex items-center space-x-2">
          <Radio className="w-6 h-6 text-purple-400" />
          <span>Xbox Stream VOD Clipper</span>
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Slice moments from your casual Twitch Series X broadcasts into 1080×1920 Cinema Frame Shorts (zero Reused Content risk).
        </p>
      </div>

      <form onSubmit={handleLoadVods} className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 flex flex-col sm:flex-row gap-3">
        <input
          type="text"
          value={channelInput}
          onChange={(e) => setChannelInput(e.target.value)}
          placeholder="Your Twitch username (e.g. pixelbreach) or https://www.twitch.tv/videos/..."
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
                <div className="flex items-center space-x-1.5 shrink-0">
                  <button
                    type="button"
                    onClick={() => { setStartTime(h.start); setEndTime(h.end); }}
                    className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200"
                  >
                    Fill
                  </button>
                  <button
                    type="button"
                    onClick={() => { setStartTime(h.start); setEndTime(h.end); handleProduceVod(h.start, h.end); }}
                    className="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-bold text-white"
                  >
                    Cut
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-6 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="space-y-1">
            <label className="text-[11px] font-mono uppercase text-slate-400 flex items-center space-x-1">
              <Clock className="w-3 h-3" /><span>Start (MM:SS)</span>
            </label>
            <input
              type="text"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 focus:border-purple-500 outline-none text-sm text-white font-mono"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[11px] font-mono uppercase text-slate-400 flex items-center space-x-1">
              <Clock className="w-3 h-3" /><span>End (max +58s)</span>
            </label>
            <input
              type="text"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 focus:border-purple-500 outline-none text-sm text-white font-mono"
            />
          </div>
          <div className="col-span-2 space-y-1">
            <label className="text-[11px] font-mono uppercase text-slate-400">Top Hook Banner (0–3.5s)</label>
            <input
              type="text"
              value={hookBanner}
              onChange={(e) => setHookBanner(e.target.value)}
              placeholder="e.g. GTA 6 POLICE AI IS INSANE"
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 focus:border-purple-500 outline-none text-sm text-white font-mono"
            />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-[11px] font-mono uppercase text-slate-400">YouTube Title (Optional)</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Auto-uses hook banner + #shorts #gta6"
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 focus:border-purple-500 outline-none text-sm text-white font-mono"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[11px] font-mono uppercase text-slate-400">Optional Voiceover Hook (Blank = Pure Game Audio)</label>
            <input
              type="text"
              value={ttsHook}
              onChange={(e) => setTtsHook(e.target.value)}
              placeholder="e.g. Watch what this NPC just did in Vice City."
              className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 focus:border-purple-500 outline-none text-sm text-white font-mono"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={handleProduceVod}
          disabled={activeTask?.status === 'queued' || activeTask?.status === 'processing'}
          className="w-full py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm flex items-center justify-center space-x-2 transition disabled:opacity-50"
        >
          <Scissors className="w-4 h-4" />
          <span>Cut Slice & Render Cinema Short</span>
        </button>

        {activeTask && (
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs font-mono">
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
            {activeTask.status === 'completed' && (
              <button
                type="button"
                onClick={() => navigate('/vault')}
                className="mt-2 px-3 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-bold inline-flex items-center space-x-1"
              >
                <Play className="w-3.5 h-3.5" /><span>Open in Vault</span>
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
