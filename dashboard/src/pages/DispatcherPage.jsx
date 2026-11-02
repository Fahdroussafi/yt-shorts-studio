import React from 'react';
import { Send, Clock, AlertCircle, RefreshCw, ShieldCheck, Check } from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function DispatcherPage() {
  const {
    videos,
    dispatchVideoId, setDispatchVideoId,
    dispatchMode, setDispatchMode,
    dispatchTime, setDispatchTime,
    scheduleRec, fetchScheduleRec,
    channelData, setShowChannelModal,
    uploading, uploadResult, handleUpload
  } = useApp();

  return (
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
              onClick={() => {
                setDispatchMode('scheduled');
                fetchScheduleRec();
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
          <div className="space-y-3 p-3.5 bg-slate-900/60 rounded-xl border border-slate-800">
            <div className="flex items-center justify-between">
              <label className="text-xs font-mono uppercase text-slate-300 font-semibold flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-blue-400" />
                <span>Release Slot (19:00 UTC Peak Window)</span>
              </label>
              <span className="text-[10px] text-blue-400 font-mono">1 Video/Day Spacing</span>
            </div>

            {/* Quick Pick US Peak Slots */}
            {scheduleRec?.available_slots?.length > 0 && (
              <div className="space-y-1.5">
                <div className="text-[11px] text-slate-400 font-mono">Recommended Open Peak Slots:</div>
                <div className="grid grid-cols-2 gap-2">
                  {scheduleRec.available_slots.map((slot, idx) => {
                    const isSelected = dispatchTime === slot.input_val || (dispatchTime && dispatchTime.startsWith(slot.input_val.slice(0, 10)));
                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setDispatchTime(slot.input_val)}
                        className={`px-2.5 py-1.5 rounded-lg border text-left text-xs transition ${
                          isSelected
                            ? 'bg-blue-600/30 border-blue-400 text-blue-200 font-bold shadow-sm shadow-blue-500/20'
                            : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                        }`}
                      >
                        <div className="truncate">{slot.display}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="space-y-1">
              <div className="text-[11px] text-slate-400 font-mono">Exact Release Date & Time (UTC):</div>
              <input
                type="datetime-local"
                value={dispatchTime}
                onChange={(e) => setDispatchTime(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono"
              />
            </div>

            <div className="p-2.5 rounded-lg bg-blue-950/30 border border-blue-900/40 text-[11px] text-blue-300/90 leading-relaxed">
              💡 <strong>Algorithm Rule:</strong> YouTube tests Shorts in 24h seed batches. Spacing uploads $\ge$20 hours apart during US peak (18:00–21:00 UTC) avoids cannibalizing audience impressions.
            </div>
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
                ? `Dispatch ${(dispatchVideoId || '').toUpperCase()} to Channel` 
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
  );
}

