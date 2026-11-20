import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sliders, Sparkles, RefreshCw, Play, Layers, Check, Trash2, Volume2, Square } from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function StudioPage() {
  const {
    authFetch, showToast,
    studioVideoId, setStudioVideoId,
    studioVoice, setStudioVoice,
    studioScript, setStudioScript,
    studioKeywords, setStudioKeywords,
    studioTitle, setStudioTitle,
    studioComment, setStudioComment,
    visualMode, setVisualMode,
    studioSearchTags, setStudioSearchTags,
    isProducing, seriesTasks, handleStartProduction, handleStartGuideProduction,
    taskStatus, generatingIdea, autoGenerateAndFillStudio,
    videos, setPreviewVideo, handleDeleteVideo, usage
  } = useApp();

  const isGta = usage?.studio_mode === 'gta';

  const navigate = useNavigate();
  const [previewingVoice, setPreviewingVoice] = useState(false);
  const [guideTopic, setGuideTopic] = useState('');
  const [guideMinutes, setGuideMinutes] = useState(6);
  const voiceAudioRef = useRef(null);

  const handleToggleVoicePreview = async () => {
    if (previewingVoice && voiceAudioRef.current) {
      voiceAudioRef.current.pause();
      voiceAudioRef.current.currentTime = 0;
      setPreviewingVoice(false);
      return;
    }
    setPreviewingVoice(true);
    try {
      const res = await authFetch(`/api/voice-preview?voice=${encodeURIComponent(studioVoice)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      voiceAudioRef.current = audio;
      audio.onended = () => {
        setPreviewingVoice(false);
        URL.revokeObjectURL(url);
      };
      audio.onerror = () => {
        setPreviewingVoice(false);
        URL.revokeObjectURL(url);
      };
      await audio.play();
    } catch (e) {
      setPreviewingVoice(false);
      showToast?.(`Voice preview failed: ${e.message}`, 'error');
    }
  };

  return (
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
            type="button"
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
            <div className="flex items-center space-x-2">
              <select
                value={studioVoice}
                onChange={(e) => setStudioVoice(e.target.value)}
                className="flex-1 min-w-0 px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white"
              >
                <option value="en-US-AndrewMultilingualNeural">Andrew HD (Most Human YouTuber Voice - Gaming Default)</option>
                <option value="en-US-BrianMultilingualNeural">Brian HD (Smooth Natural Narrator)</option>
                <option value="en-US-BrianNeural">Brian (Standard Narrator)</option>
                <option value="en-US-SteffanNeural">Steffan (Crisp Modern Male)</option>
                <option value="en-GB-RyanNeural">Ryan (British Documentary Male)</option>
                <option value="en-US-ChristopherNeural">Christopher (Deep Authoritative Male - Dark Psychology Default)</option>
                <option value="en-US-GuyNeural">Guy (Engaging Storyteller - Historical Archives)</option>
                <option value="en-US-AvaNeural">Ava (Sharp Analytical Female - Deception Profiling)</option>
                <option value="en-US-JennyNeural">Jenny (Calm Intimate Female - Non-Verbal Dynamics)</option>
              </select>
              <button
                type="button"
                onClick={handleToggleVoicePreview}
                className={`px-3 py-2.5 rounded-xl border text-xs font-bold flex items-center space-x-1.5 transition shrink-0 ${
                  previewingVoice
                    ? 'bg-red-950/60 border-red-700 text-red-300'
                    : 'bg-slate-900 border-slate-800 hover:border-cyan-500 text-cyan-300'
                }`}
                title="Preview selected voice"
              >
                {previewingVoice ? <Square className="w-3.5 h-3.5 fill-current" /> : <Volume2 className="w-4 h-4" />}
                <span>{previewingVoice ? 'Stop' : 'Listen'}</span>
              </button>
            </div>
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

        {/* Visual Engine Mode */}
        <div className="space-y-2">
          <label className="text-xs font-mono uppercase text-slate-400">Visual Engine & Retention Mode</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            <button
              type="button"
              onClick={() => setVisualMode('cinematic_cuts')}
              className={`p-3 rounded-xl border text-left transition flex flex-col justify-between ${
                visualMode === 'cinematic_cuts'
                  ? 'bg-violet-950/40 border-violet-500 text-white'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="font-bold text-xs flex items-center space-x-1.5 text-white">
                <span>🎬</span>
                <span>{isGta ? 'News Media Cuts' : 'Cinematic Cuts'}</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {isGta
                  ? 'Scraped article images & videos (Ken Burns Cinema Frame)'
                  : 'Dynamic stock cuts (8-10 scenes) with no-repeat tracking'}
              </p>
            </button>

            <button
              type="button"
              onClick={() => setVisualMode('parkour_brainrot')}
              className={`p-3 rounded-xl border text-left transition flex flex-col justify-between ${
                visualMode === 'parkour_brainrot'
                  ? 'bg-emerald-950/40 border-emerald-500 text-white shadow-lg shadow-emerald-500/10'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="font-bold text-xs flex items-center space-x-1.5 text-emerald-400">
                <span>🎮</span>
                <span>{isGta ? 'Server Gameplay Cuts' : 'Minecraft Parkour'}</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {isGta
                  ? '8-cut local GTA gameplay & trailer loop (Cinema Frame)'
                  : 'Hypnotic vertical parkour loop (100%+ retention, 3s render)'}
              </p>
            </button>

            <button
              type="button"
              onClick={() => setVisualMode('split_retention')}
              className={`p-3 rounded-xl border text-left transition flex flex-col justify-between ${
                visualMode === 'split_retention'
                  ? 'bg-cyan-950/40 border-cyan-500 text-white shadow-lg shadow-cyan-500/10'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="font-bold text-xs flex items-center space-x-1.5 text-cyan-400">
                <span>⚡</span>
                <span>Split-Screen Retention</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">50/50: Story scenes top, hypnotic parkour bottom</p>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase text-slate-400">
              {visualMode === 'parkour_brainrot' ? 'Gameplay Tags (Bypassed for Local Parkour)' : 'Footage Keywords (Comma separated)'}
            </label>
            <input
              type="text"
              value={studioKeywords}
              onChange={(e) => setStudioKeywords(e.target.value)}
              placeholder="e.g. dark city, robot, thinking, emergency, crowd"
              disabled={visualMode === 'parkour_brainrot'}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono disabled:opacity-40"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-mono uppercase text-slate-400">High-Intent Search Tags (For YouTube SEO)</label>
            <input
              type="text"
              value={studioSearchTags}
              onChange={(e) => setStudioSearchTags(e.target.value)}
              placeholder="e.g. psychology facts, human behavior, survival paradox"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono"
            />
          </div>
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
          type="button"
          onClick={handleStartProduction}
          disabled={isProducing}
          className="w-full py-3.5 rounded-xl bg-gradient-to-r from-violet-600 via-purple-600 to-cyan-500 hover:from-violet-500 hover:to-cyan-400 disabled:opacity-50 text-white font-bold text-base flex items-center justify-center space-x-2 transition shadow-xl shadow-violet-600/20"
        >
          {isProducing ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Play className="w-5 h-5 fill-current" />}
          <span>
            {isProducing
              ? seriesTasks?.length > 1
                ? `Producing ${seriesTasks.length}-Part Series (${seriesTasks.filter((t) => t.status === 'completed').length}/${seriesTasks.length} Done)...`
                : 'Producing Real-Motion HD Short...'
              : 'Render 1080x1920 Short'}
          </span>
        </button>
      </div>

      {/* Long-Form 16:9 UI Info-Card Guide Builder */}
      <div className="bg-[#12121a] border border-cyan-500/30 rounded-2xl p-5 space-y-3 shadow-lg">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div>
            <h3 className="font-bold text-sm text-white flex items-center space-x-2">
              <span>📊</span>
              <span>16:9 UI Info-Card Guide Builder (5–8 min)</span>
            </h3>
            <p className="text-xs text-slate-400">Chaptered 1920x1080 info cards (Steps, Stat Bars, Do/Avoid) + YouTube timestamps.</p>
          </div>
          <div className="flex items-center space-x-1.5">
            {[5, 6, 8].map((mins) => (
              <button
                key={mins}
                type="button"
                onClick={() => setGuideMinutes(mins)}
                className={`px-2.5 py-1 rounded-lg text-xs font-mono font-bold border transition ${
                  guideMinutes === mins
                    ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300'
                    : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                {mins}m
              </button>
            ))}
          </div>
        </div>
        <div className="flex flex-col sm:flex-row gap-2.5">
          <input
            type="text"
            value={guideTopic}
            onChange={(e) => setGuideTopic(e.target.value)}
            placeholder="Leave blank for Surprise Me (live topic) or paste topic / URL..."
            className="flex-1 px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 outline-none text-sm text-white"
          />
          {studioScript && (
            <button
              type="button"
              disabled={isProducing}
              onClick={() => handleStartGuideProduction(`${studioTitle}\n${studioScript}`, guideMinutes)}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-cyan-300 border border-cyan-500/30 font-bold text-xs transition shrink-0"
            >
              Expand Studio Script
            </button>
          )}
          <button
            type="button"
            disabled={isProducing}
            onClick={() => handleStartGuideProduction(guideTopic, guideMinutes)}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 text-white font-bold text-sm flex items-center justify-center space-x-2 transition shrink-0"
          >
            {isProducing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
            <span>{guideTopic.trim() ? 'Render 16:9 Guide' : 'Surprise Me & Render'}</span>
          </button>
        </div>
      </div>

      {/* Multi-Screen Dynamic Series Grid (2 or 3 parts side-by-side) */}
      {seriesTasks?.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-amber-400" />
              <span>Multi-Part Series Pipeline ({seriesTasks.filter((t) => t.status === 'completed').length}/{seriesTasks.length} Completed)</span>
            </h3>
          </div>
          <div className={`grid grid-cols-1 gap-4 ${seriesTasks.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3'}`}>
            {seriesTasks.map((t) => {
              const badgeClass =
                t.status === 'completed'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800/60'
                  : t.status === 'failed'
                    ? 'bg-red-950 text-red-300 border border-red-800/60'
                    : t.status === 'queued'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800/60 animate-pulse'
                      : 'bg-cyan-950 text-cyan-300 border border-cyan-800/60 animate-pulse';

              return (
                <div key={t.videoId} className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[11px] font-mono font-bold text-violet-300">
                        PART {t.part}/{t.total} • {(t.videoId || '').toUpperCase()}
                      </span>
                      <span className={`text-[10px] font-mono uppercase font-bold px-2 py-0.5 rounded-full ${badgeClass}`}>
                        {t.status === 'queued' && t.queue_position ? `Queue #${t.queue_position}` : t.status}
                      </span>
                    </div>

                    <div className="text-xs font-bold text-white line-clamp-2 min-h-[2rem]" title={t.title}>
                      {t.title}
                    </div>

                    <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800/60">
                      <div
                        style={{ width: `${t.progress || 0}%` }}
                        className={`h-full transition-all duration-300 ${
                          t.status === 'completed'
                            ? 'bg-emerald-500'
                            : t.status === 'failed'
                              ? 'bg-red-500'
                              : 'bg-gradient-to-r from-violet-500 to-cyan-400'
                        }`}
                      />
                    </div>

                    <div className="p-2.5 rounded-xl bg-black/60 border border-slate-800/80 font-mono text-[10px] text-slate-300 h-28 overflow-y-auto space-y-1">
                      {(t.log || []).map((l, idx) => (
                        <div key={idx} className={l.includes('[ERROR]') ? 'text-red-400 font-bold' : l.includes('[SUCCESS]') ? 'text-emerald-400 font-bold' : l.includes('[QUEUE]') ? 'text-amber-400' : 'text-slate-400'}>
                          {l}
                        </div>
                      ))}
                    </div>
                  </div>

                  {t.status === 'completed' && (
                    <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          const v = videos.find((x) => x.id === t.videoId);
                          if (v) setPreviewVideo(v);
                          else navigate('/vault');
                        }}
                        className="flex-1 py-1.5 px-2.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs flex items-center justify-center space-x-1 transition"
                      >
                        <Play className="w-3 h-3 text-cyan-400" />
                        <span>Preview</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteVideo(t.videoId)}
                        className="py-1.5 px-2.5 rounded-lg bg-red-950/60 hover:bg-red-900/60 text-red-300 border border-red-800/60 font-bold text-xs transition"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Single Short Progress & Log Card */}
      {taskStatus && (!seriesTasks || seriesTasks.length === 0) && (
        <div className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-bold text-sm text-white flex items-center space-x-2">
              <Layers className="w-4 h-4 text-violet-400" />
              <span>Production Pipeline Status{taskStatus.video_id ? ` — ${taskStatus.video_id.toUpperCase()}` : ''}</span>
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
                  type="button"
                  onClick={() => {
                    const v = videos.find(x => x.id === taskStatus.video_id);
                    if (v) setPreviewVideo(v);
                    else navigate('/vault');
                  }}
                  className="py-1.5 px-3 rounded-lg bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs flex items-center space-x-1.5 transition"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Preview Video</span>
                </button>
                <button
                  type="button"
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
  );
}

