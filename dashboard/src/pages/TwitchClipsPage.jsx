import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tv, RefreshCw, Scissors, Play, ExternalLink, Clock, Eye, Flame, Link as LinkIcon } from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function TwitchClipsPage() {
  const { authFetch, showToast, fetchVideos, videos, setPreviewVideo } = useApp();
  const navigate = useNavigate();

  const [game, setGame] = useState('all');
  const [hours, setHours] = useState(24);
  const [lang, setLang] = useState('en');
  const [clips, setClips] = useState([]);
  const [loading, setLoading] = useState(false);
  const [customUrl, setCustomUrl] = useState('');

  const [activeTask, setActiveTask] = useState(null);
  const [producingUrl, setProducingUrl] = useState(null);

  const loadClips = async () => {
    setLoading(true);
    try {
      const res = await authFetch(`/api/twitch/clips?game=${game}&hours=${hours}&lang=${lang}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setClips(data.clips || []);
    } catch (e) {
      showToast(`Twitch fetch error: ${e.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClips();
  }, []);

  useEffect(() => {
    if (!activeTask?.task_id || activeTask.status === 'completed' || activeTask.status === 'failed') return;
    const timer = setInterval(async () => {
      try {
        const res = await authFetch(`/api/produce/status/${activeTask.task_id}`);
        if (res.ok) {
          const data = await res.json();
          setActiveTask(data);
          if (data.status === 'completed' || data.status === 'failed') {
            setProducingUrl(null);
            fetchVideos();
          }
        } else if (res.status === 404) {
          setProducingUrl(null);
          setActiveTask((prev) => prev ? { ...prev, status: 'failed', log: [...(prev.log || []), '[ERROR] Task lost (server restarted). Click Cut 40/60 Short again.'] } : null);
        }
      } catch (e) {
        console.error(e);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [activeTask?.task_id, activeTask?.status]);

  const startClipProduce = async (clip) => {
    setProducingUrl(clip.url);
    try {
      const res = await authFetch('/api/twitch/produce', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clip_url: clip.url,
          clip_title: clip.title || 'Insane GTA Moment',
          broadcaster_name: clip.broadcaster_name || 'Streamer',
          game_name: clip.game_name || 'Grand Theft Auto',
          thumbnail_url: clip.thumbnail_url || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setActiveTask({ task_id: data.task_id, video_id: data.video_id, status: 'queued', progress: 5, log: ['Queued Twitch 40/60 render...'] });
      showToast(`Queued ${data.video_id.toUpperCase()} for 40/60 render!`, 'success');
    } catch (e) {
      setProducingUrl(null);
      showToast(`Produce error: ${e.message}`, 'error');
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center space-x-2">
            <Tv className="w-6 h-6 text-purple-400" />
            <span>Twitch Viral Clip Harvester</span>
          </h1>
          <p className="text-sm text-slate-400">Pull top GTA VI / GTA V clips ranked by velocity, auto-crop 40/60 facecam + gameplay, and burn Whisper seam captions</p>
        </div>

        <button
          type="button"
          onClick={loadClips}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center space-x-2 transition self-start"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Scanning Twitch...' : 'Refresh Viral Clips'}</span>
        </button>
      </div>

      {/* Filters + Manual Clip URL */}
      <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 grid grid-cols-1 md:grid-cols-12 gap-3 items-end">
        <div className="md:col-span-2 space-y-1">
          <label className="text-[11px] font-mono uppercase text-slate-400">Game</label>
          <select
            value={game}
            onChange={(e) => setGame(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white font-mono outline-none"
          >
            <option value="all">GTA VI + GTA V</option>
            <option value="gta6">GTA VI Only</option>
            <option value="gta5">GTA V Only</option>
          </select>
        </div>

        <div className="md:col-span-2 space-y-1">
          <label className="text-[11px] font-mono uppercase text-slate-400">Window</label>
          <select
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white font-mono outline-none"
          >
            <option value={24}>Last 24h</option>
            <option value={72}>Last 72h</option>
            <option value={168}>Last 7d</option>
          </select>
        </div>

        <div className="md:col-span-2 space-y-1">
          <label className="text-[11px] font-mono uppercase text-slate-400">Language</label>
          <select
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white font-mono outline-none"
          >
            <option value="en">English</option>
            <option value="all">All Languages</option>
          </select>
        </div>

        <div className="md:col-span-6 flex items-end gap-2">
          <div className="flex-1 space-y-1">
            <label className="text-[11px] font-mono uppercase text-slate-400 flex items-center space-x-1">
              <LinkIcon className="w-3 h-3 text-purple-400" />
              <span>Or Paste Any Twitch Clip URL</span>
            </label>
            <input
              type="text"
              value={customUrl}
              onChange={(e) => setCustomUrl(e.target.value)}
              placeholder="https://www.twitch.tv/streamer/clip/..."
              className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white font-mono outline-none focus:border-purple-500"
            />
          </div>
          <button
            type="button"
            disabled={!customUrl.trim() || Boolean(producingUrl)}
            onClick={() => startClipProduce({ url: customUrl.trim(), title: 'Viral GTA Moment', broadcaster_name: 'Streamer', game_name: 'Grand Theft Auto VI' })}
            className="px-3.5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white font-bold text-xs shrink-0"
          >
            Cut URL
          </button>
        </div>
      </div>

      {/* Live Render Status */}
      {activeTask && (
        <div className="p-4 rounded-2xl bg-[#12121a] border border-purple-700/50 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-white">
              TWITCH 40/60 PIPELINE — {(activeTask.video_id || '').toUpperCase()}
            </span>
            <span className={`text-[11px] font-mono uppercase font-bold px-2.5 py-0.5 rounded-full ${
              activeTask.status === 'completed'
                ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                : activeTask.status === 'failed'
                  ? 'bg-red-950 text-red-300 border border-red-800'
                  : 'bg-purple-950 text-purple-300 border border-purple-700 animate-pulse'
            }`}>
              {activeTask.status}
            </span>
          </div>

          <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
            <div style={{ width: `${activeTask.progress || 0}%` }} className="h-full bg-gradient-to-r from-purple-500 to-cyan-400 transition-all" />
          </div>

          <div className="p-2.5 rounded-xl bg-black/60 font-mono text-[11px] text-slate-300 max-h-32 overflow-y-auto space-y-1">
            {(activeTask.log || []).map((l, i) => (
              <div key={i} className={l.includes('[ERROR]') ? 'text-red-400' : l.includes('[SUCCESS]') ? 'text-emerald-400 font-bold' : 'text-slate-400'}>
                {l}
              </div>
            ))}
          </div>

          {activeTask.status === 'completed' && (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => {
                  const v = videos.find((x) => x.id === activeTask.video_id);
                  if (v) setPreviewVideo(v);
                  else navigate('/vault');
                }}
                className="px-3.5 py-1.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-1.5"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Preview Rendered Short</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Clips Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {clips.map((c) => (
          <div key={c.id} className="rounded-2xl bg-[#12121a] border border-slate-800/80 overflow-hidden flex flex-col justify-between">
            <div>
              <div className="relative aspect-video bg-black">
                {c.thumbnail_url && <img src={c.thumbnail_url} alt={c.title} className="w-full h-full object-cover" />}
                <span className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono font-bold text-purple-300">
                  {c.game_name}
                </span>
                <span className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono text-white flex items-center space-x-1">
                  <Clock className="w-3 h-3" />
                  <span>{c.duration}s</span>
                </span>
              </div>

              <div className="p-4 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-mono">
                  <span className="text-cyan-400 font-bold">@{c.broadcaster_name}</span>
                  <span className="text-amber-400 flex items-center space-x-1">
                    <Flame className="w-3 h-3" />
                    <span>{c.velocity}/hr</span>
                  </span>
                </div>
                <h3 className="text-xs font-bold text-white line-clamp-2 min-h-[2rem]">{c.title}</h3>
                <div className="text-[11px] text-slate-500 font-mono flex items-center space-x-1">
                  <Eye className="w-3 h-3" />
                  <span>{c.view_count.toLocaleString()} views</span>
                </div>
              </div>
            </div>

            <div className="px-4 pb-4 flex items-center gap-2">
              <button
                type="button"
                disabled={Boolean(producingUrl)}
                onClick={() => startClipProduce(c)}
                className="flex-1 py-2 px-3 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 disabled:opacity-40 text-white font-bold text-xs flex items-center justify-center space-x-1.5 transition"
              >
                <Scissors className="w-3.5 h-3.5" />
                <span>{producingUrl === c.url ? 'Rendering...' : 'Cut 40/60 Short'}</span>
              </button>
              <a
                href={c.url}
                target="_blank"
                rel="noreferrer"
                className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition"
                title="Open on Twitch"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
