import React, { useState, useMemo, useEffect } from 'react';
import { Send, Clock, AlertCircle, RefreshCw, ShieldCheck, Check, Layers, Calendar } from 'lucide-react';
import { useApp } from '../context/AppContext';

function getNextAvailableDateStr(statsVideos) {
  const tomorrow = new Date();
  tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
  let base = Date.UTC(tomorrow.getUTCFullYear(), tomorrow.getUTCMonth(), tomorrow.getUTCDate());

  const list = statsVideos || [];
  for (const v of list) {
    if (v.publish_at) {
      const t = new Date(v.publish_at).getTime();
      if (!Number.isNaN(t) && t >= base) {
        const d = new Date(t);
        const nextDay = Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + 1);
        if (nextDay > base) base = nextDay;
      }
    }
  }
  return new Date(base).toISOString().slice(0, 10);
}

function addDaysToDate(dateStr, offsetDays, timeStr) {
  const [y, m, d] = (dateStr || '').split('-').map(Number);
  if (!y || !m || !d) return '';
  const dt = new Date(Date.UTC(y, m - 1, d + offsetDays));
  const cleanTime = (timeStr || '19:00').slice(0, 5);
  return `${dt.toISOString().slice(0, 10)}T${cleanTime}`;
}

export default function DispatcherPage() {
  const {
    videos, stats, usage,
    dispatchVideoId, setDispatchVideoId,
    dispatchMode, setDispatchMode,
    dispatchTime, setDispatchTime,
    channelData, setShowChannelModal,
    uploading, uploadResult, handleUpload,
    batchProgress, handleBatchUpload
  } = useApp();

  const [tab, setTab] = useState('single'); // 'single' | 'batch'
  const [startDate, setStartDate] = useState(() => getNextAvailableDateStr(stats?.videos));
  const [dailyTime, setDailyTime] = useState('19:00');
  const [postsPerDay, setPostsPerDay] = useState(1); // 1 | 2
  const [selectedIds, setSelectedIds] = useState([]);

  const quotaRemaining = usage?.youtube?.uploads_remaining ?? 6;
  const maxBatch = Math.max(0, Math.min(6, quotaRemaining));
  const minDateUtc = new Date().toISOString().slice(0, 10);
  const minDateTimeUtc = `${minDateUtc}T00:00`;

  const readyVideos = useMemo(
    () => (videos || []).filter((v) => !v.yt_id && v.status === 'LOCAL_READY'),
    [videos]
  );

  // Sync default startDate when stats load (only if user hasn't started batch yet)
  useEffect(() => {
    setStartDate((prev) => prev || getNextAvailableDateStr(stats?.videos));
  }, [stats]);

  // Sync single-dispatch selection to a valid unscheduled/ready short
  useEffect(() => {
    if (readyVideos.length === 0) {
      if (dispatchVideoId) setDispatchVideoId('');
      return;
    }
    if (!readyVideos.some((v) => v.id === dispatchVideoId)) {
      setDispatchVideoId(readyVideos[readyVideos.length - 1].id);
    }
  }, [readyVideos, dispatchVideoId, setDispatchVideoId]);

  // Auto-select up to remaining quota (max 6) ready shorts when entering batch or when readyVideos change
  useEffect(() => {
    const validReady = new Set(readyVideos.map((v) => v.id));
    setSelectedIds((prev) => {
      const kept = prev.filter((id) => validReady.has(id));
      if (kept.length > 0) return kept.slice(0, maxBatch || 6);
      return readyVideos.slice(0, maxBatch).map((v) => v.id);
    });
  }, [readyVideos, maxBatch]);

  const fillDefaultSingleTime = () => {
    if (!dispatchTime) {
      const nextDate = getNextAvailableDateStr(stats?.videos);
      setDispatchTime(`${nextDate}T${dailyTime}`);
    }
  };

  const toggleBatchVideo = (id) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= maxBatch) return prev;
      return [...prev, id];
    });
  };

  const batchPlan = useMemo(() => {
    const occupied = new Set(
      (stats?.videos || [])
        .map((v) => (v.publish_at ? new Date(v.publish_at).toISOString().slice(0, 16) : null))
        .filter(Boolean)
    );
    const slotTimes = postsPerDay === 2 ? ['15:00', dailyTime || '19:00'] : [dailyTime || '19:00'];
    let slotCursor = 0;

    return readyVideos
      .filter((v) => selectedIds.includes(v.id))
      .map((v) => {
        let publishAt = '';
        while (slotCursor < 365) {
          const dayOffset = Math.floor(slotCursor / slotTimes.length);
          const timeSlot = slotTimes[slotCursor % slotTimes.length];
          slotCursor += 1;
          const candidate = addDaysToDate(startDate, dayOffset, timeSlot);
          if (!occupied.has(candidate)) {
            occupied.add(candidate);
            publishAt = candidate;
            break;
          }
        }
        return { videoId: v.id, title: v.title, size_mb: v.size_mb, publishAt };
      });
  }, [readyVideos, selectedIds, startDate, dailyTime, postsPerDay, stats]);

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-black text-white flex items-center space-x-2">
            <Send className="w-6 h-6 text-emerald-400" />
            <span>YouTube Direct Dispatcher</span>
          </h1>
          <p className="text-sm text-slate-400">Push verified shorts directly to channel with automated tags and scheduling</p>
        </div>

        <div className="inline-flex p-1 rounded-xl bg-slate-900 border border-slate-800 self-start">
          <button
            type="button"
            onClick={() => setTab('single')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
              tab === 'single' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Single Short
          </button>
          <button
            type="button"
            onClick={() => setTab('batch')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center space-x-1.5 transition ${
              tab === 'batch' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Batch ({readyVideos.length})</span>
          </button>
        </div>
      </div>

      {tab === 'single' ? (
        <div className="p-6 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-5">
          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase text-slate-400">Select Short from Vault</label>
            <select
              value={dispatchVideoId}
              onChange={(e) => setDispatchVideoId(e.target.value)}
              disabled={readyVideos.length === 0}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono disabled:opacity-50"
            >
              {readyVideos.length === 0 ? (
                <option value="">No unscheduled shorts in vault</option>
              ) : (
                readyVideos.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.id.toUpperCase()} — {v.title} ({v.size_mb} MB)
                  </option>
                ))
              )}
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
                onClick={() => {
                  setDispatchMode('scheduled');
                  fillDefaultSingleTime();
                }}
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
            <div className="space-y-2.5 p-4 bg-slate-900/60 rounded-xl border border-slate-800">
              <label className="text-xs font-mono uppercase text-slate-300 font-semibold flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-400" />
                <span>Exact Release Date & Time (UTC)</span>
              </label>
              <input
                type="datetime-local"
                min={minDateTimeUtc}
                value={dispatchTime}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v && v.slice(0, 10) < minDateUtc) return;
                  setDispatchTime(v);
                }}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-blue-500 outline-none text-sm text-white font-mono"
              />
              <p className="text-[11px] text-slate-500 font-mono">
                Short will remain private until this exact UTC timestamp, then automatically switch to public.
              </p>
            </div>
          )}

          {!channelData?.has_youtube_token && (
            <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-800/60 flex items-center justify-between text-xs text-amber-300">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                <span>YouTube OAuth token missing. Connect channel to dispatch.</span>
              </div>
              <button
                type="button"
                onClick={() => setShowChannelModal(true)}
                className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs transition shrink-0"
              >
                Connect Channel
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={channelData?.has_youtube_token ? handleUpload : () => setShowChannelModal(true)}
            disabled={uploading || (channelData?.has_youtube_token && !dispatchVideoId)}
            className={`w-full py-3.5 rounded-xl text-white font-bold text-sm flex items-center justify-center space-x-2 transition shadow-xl disabled:opacity-50 disabled:cursor-not-allowed ${
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
                  ? `Dispatch ${(dispatchVideoId || '').toUpperCase()} to Channel`
                  : 'Connect YouTube Channel to Dispatch'}
            </span>
          </button>
        </div>
      ) : (
        <div className="p-6 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-5">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400">
              READY UN-UPLOADED SHORTS: <strong className="text-white">{readyVideos.length}</strong>
            </span>
            <span className="text-blue-400">
              QUOTA LEFT TODAY: <strong>{quotaRemaining} / 6</strong>
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-4 bg-slate-900/60 rounded-xl border border-slate-800">
            <div className="space-y-1">
              <label className="text-[11px] font-mono uppercase text-slate-400 flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5 text-blue-400" />
                <span>First Short Date (UTC)</span>
              </label>
              <input
                type="date"
                min={minDateUtc}
                value={startDate}
                onChange={(e) => {
                  const v = e.target.value;
                  if (v && v < minDateUtc) return;
                  setStartDate(v);
                }}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 focus:border-blue-500 outline-none text-sm text-white font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono uppercase text-slate-400 flex items-center space-x-1">
                <Clock className="w-3.5 h-3.5 text-blue-400" />
                <span>Primary Time (UTC)</span>
              </label>
              <input
                type="time"
                value={dailyTime}
                onChange={(e) => setDailyTime(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 focus:border-blue-500 outline-none text-sm text-white font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-mono uppercase text-slate-400 flex items-center space-x-1">
                <Layers className="w-3.5 h-3.5 text-blue-400" />
                <span>Cadence</span>
              </label>
              <select
                value={postsPerDay}
                onChange={(e) => setPostsPerDay(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 focus:border-blue-500 outline-none text-sm text-white font-mono"
              >
                <option value={1}>1 / Day ({dailyTime})</option>
                <option value={2}>2 / Day (15:00 & {dailyTime})</option>
              </select>
            </div>
          </div>

          {readyVideos.length === 0 ? (
            <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-400 text-center">
              No un-uploaded local shorts in vault. Produce new shorts first.
            </div>
          ) : (
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {readyVideos.map((v) => {
                const checked = selectedIds.includes(v.id);
                const planEntry = batchPlan.find((p) => p.videoId === v.id);
                return (
                  <label
                    key={v.id}
                    className={`flex items-center justify-between p-3 rounded-xl border cursor-pointer transition ${
                      checked
                        ? 'bg-blue-950/30 border-blue-500/60 text-white'
                        : 'bg-slate-900/50 border-slate-800 text-slate-400'
                    }`}
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled={!checked && selectedIds.length >= maxBatch}
                        onChange={() => toggleBatchVideo(v.id)}
                        className="rounded border-slate-700 bg-slate-950 text-blue-500"
                      />
                      <div className="min-w-0">
                        <div className="text-xs font-mono font-bold truncate">
                          {v.id.toUpperCase()} — {v.title}
                        </div>
                        <div className="text-[11px] text-slate-500 font-mono">{v.size_mb} MB</div>
                      </div>
                    </div>
                    {planEntry && (
                      <span className="text-[11px] font-mono text-blue-300 shrink-0 ml-2">
                        {planEntry.publishAt.replace('T', ' ')} UTC
                      </span>
                    )}
                  </label>
                );
              })}
            </div>
          )}

          {!channelData?.has_youtube_token && (
            <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-800/60 flex items-center justify-between text-xs text-amber-300">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-amber-400 shrink-0" />
                <span>YouTube OAuth token missing. Connect channel to dispatch.</span>
              </div>
              <button
                type="button"
                onClick={() => setShowChannelModal(true)}
                className="px-3 py-1 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs transition shrink-0"
              >
                Connect Channel
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={channelData?.has_youtube_token ? () => handleBatchUpload(batchPlan) : () => setShowChannelModal(true)}
            disabled={uploading || (channelData?.has_youtube_token && (batchPlan.length === 0 || maxBatch === 0))}
            className={`w-full py-3.5 rounded-xl text-white font-bold text-sm flex items-center justify-center space-x-2 transition shadow-xl disabled:opacity-50 ${
              channelData?.has_youtube_token
                ? 'bg-blue-600 hover:bg-blue-500 shadow-blue-600/20'
                : 'bg-amber-600 hover:bg-amber-500 shadow-amber-600/20'
            }`}
          >
            {uploading ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : channelData?.has_youtube_token ? (
              <Layers className="w-5 h-5" />
            ) : (
              <ShieldCheck className="w-5 h-5" />
            )}
            <span>
              {uploading && batchProgress?.active
                ? `Scheduling ${batchProgress.current}/${batchProgress.total}: ${(batchProgress.currentId || '').toUpperCase()}...`
                : channelData?.has_youtube_token
                  ? maxBatch === 0
                    ? 'Daily YouTube Upload Quota Reached (0 Left)'
                    : `Auto-Schedule ${batchPlan.length} Short${batchPlan.length === 1 ? '' : 's'} (1/Day @ ${dailyTime} UTC)`
                  : 'Connect YouTube Channel to Dispatch'}
            </span>
          </button>
        </div>
      )}

      {/* Batch Upload Results */}
      {batchProgress && batchProgress.results.length > 0 && (
        <div className="p-4 rounded-xl border border-slate-800 bg-[#12121a] space-y-2 text-xs font-mono">
          <div className="font-bold text-white">
            Batch Progress ({batchProgress.results.length}/{batchProgress.total})
          </div>
          {batchProgress.results.map((r) => (
            <div
              key={r.video_id}
              className={`flex items-center justify-between p-2 rounded-lg ${
                r.success ? 'bg-emerald-950/40 text-emerald-300' : 'bg-red-950/40 text-red-300'
              }`}
            >
              <span>
                {(r.video_id || '').toUpperCase()} {r.scheduledAt ? `(${r.scheduledAt.replace('T', ' ')} UTC)` : ''}
              </span>
              {r.success ? (
                <a href={r.url} target="_blank" rel="noreferrer" className="underline text-cyan-300">
                  {r.yt_id}
                </a>
              ) : (
                <span className="truncate max-w-xs">{r.error}</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Single Upload Result Alert */}
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
  );
}
