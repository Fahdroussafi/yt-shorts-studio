import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, RefreshCw, ChevronRight, Zap, Flame, Trophy, ExternalLink } from 'lucide-react';
import { useApp } from '../context/AppContext';

export default function IdeasPage() {
  const {
    niches,
    selectedNiche, setSelectedNiche,
    seriesMode, setSeriesMode,
    ideaConcept, setIdeaConcept,
    generatingIdea, generatedIdea,
    handleGenerateIdea,
    sendIdeaToStudio, handleQuickProduce,
    isProducing, showToast, authFetch
  } = useApp();

  const navigate = useNavigate();
  const [outliers, setOutliers] = useState([]);
  const [loadingOutliers, setLoadingOutliers] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    async function loadOutliers() {
      try {
        setLoadingOutliers(true);
        const res = await authFetch('/api/ideas/viral-outliers');
        if (res.ok) {
          const data = await res.json();
          setOutliers(data.outliers || []);
        }
      } catch (err) {
        console.error('Failed to load outliers:', err);
      } finally {
        setLoadingOutliers(false);
      }
    }
    loadOutliers();
  }, []);

  const filteredOutliers = selectedCategory === 'all'
    ? outliers
    : outliers.filter(o => o.category === selectedCategory);

  return (
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
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800/60 pb-3">
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-bold text-sm text-white">Generate Viral Script Structure</h3>
              {/* Batch Story Series Toggle */}
              <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-[11px] font-mono">
                <button
                  type="button"
                  onClick={() => setSeriesMode(1)}
                  className={`px-2 py-0.5 rounded-md transition ${seriesMode === 1 ? 'bg-violet-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
                >
                  Single
                </button>
                <button
                  type="button"
                  onClick={() => setSeriesMode(2)}
                  className={`px-2 py-0.5 rounded-md transition ${seriesMode === 2 ? 'bg-cyan-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
                  title="Generate a 2-Part Connected Story Series"
                >
                  2-Part Arc
                </button>
                <button
                  type="button"
                  onClick={() => setSeriesMode(3)}
                  className={`px-2 py-0.5 rounded-md transition ${seriesMode === 3 ? 'bg-amber-600 text-white font-bold' : 'text-slate-400 hover:text-white'}`}
                  title="Generate a 3-Part Trilogy Series with Cliffhangers"
                >
                  3-Part Trilogy
                </button>
              </div>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {seriesMode > 1 ? `Multi-short series active: drafts ${seriesMode} connected cliffhanger episodes in one click.` : 'Choose between custom concept drafting or 1-click curated viral hook discovery.'}
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleGenerateIdea(selectedNiche, true)}
            disabled={generatingIdea}
            className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 disabled:opacity-50 text-black font-extrabold text-xs flex items-center space-x-2 transition shadow-lg shadow-amber-500/20 self-start md:self-auto shrink-0"
            title="1-Click: Rolls a random psychological angle from our viral angle matrix"
          >
            <Sparkles className="w-4 h-4 fill-current" />
            <span>🎲 Surprise Me (Roll Viral Hook)</span>
          </button>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <span>Or enter a specific topic/angle to draft:</span>
            <span className="text-[10px] text-slate-500 font-normal">Type an angle or keyword</span>
          </div>
          <div className="flex space-x-3">
            <input
              type="text"
              value={ideaConcept}
              onChange={(e) => setIdeaConcept(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && ideaConcept.trim()) handleGenerateIdea(); }}
              placeholder="e.g. 'Door in the face technique', '4-second silence rule', 'Gaslighting counters'..."
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white placeholder:text-slate-600"
            />
            <button
              type="button"
              onClick={() => {
                if (!ideaConcept.trim()) {
                  showToast("Please enter a custom topic/angle first, or click '🎲 Surprise Me' to roll a viral hook.", "info");
                  return;
                }
                handleGenerateIdea();
              }}
              disabled={generatingIdea || !ideaConcept.trim()}
              className="px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-sm flex items-center space-x-2 transition shadow-lg shadow-violet-600/20 shrink-0"
            >
              {generatingIdea ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              <span>Draft Custom Concept</span>
            </button>
          </div>
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

        {/* Render Multi-Part Series or Single Idea */}
        {generatedIdea?.is_series && !generatingIdea && (
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-xs font-mono font-bold text-amber-400 uppercase">
                Story Series Trilogy ({generatedIdea.episodes?.length} Connected Episodes)
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                Click "Send to Studio" on any episode to load its full script & tags
              </span>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {(generatedIdea.episodes || []).map((ep, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-3 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800/60">
                        Part {ep.series_part} of {ep.series_total}
                      </span>
                      <span className="text-[10px] font-mono text-violet-400 font-bold">{ep.next_id?.toUpperCase()}</span>
                    </div>
                    <h4 className="text-xs font-bold text-white line-clamp-2" title={ep.title}>{ep.title}</h4>
                    <p className="text-[11px] text-slate-300 leading-relaxed bg-black/40 p-2.5 rounded-lg border border-slate-800/40 line-clamp-5">
                      {ep.script}
                    </p>
                  </div>
                  <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between gap-2">
                    <button
                      type="button"
                      onClick={() => sendIdeaToStudio(ep, navigate)}
                      className="flex-1 py-1 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-bold text-center transition"
                    >
                      Load in Studio
                    </button>
                    <button
                      type="button"
                      onClick={() => handleQuickProduce(ep, navigate)}
                      disabled={isProducing}
                      className="py-1 px-2.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-[11px] flex items-center space-x-1"
                    >
                      <Zap className="w-3 h-3 fill-current" />
                      <span>Produce</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {generatedIdea && !generatedIdea.is_series && !generatingIdea && (
          <div className="mt-4 p-5 rounded-xl bg-slate-900/80 border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase">Generated Concept</span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                  generatedIdea.source && (generatedIdea.source.includes('groq') || generatedIdea.source.includes('openai'))
                    ? 'bg-orange-950 text-orange-300 border-orange-700'
                    : 'bg-violet-950 text-violet-300 border-violet-800'
                }`}>
                  {generatedIdea.source && generatedIdea.source.includes('groq')
                    ? `⚡ GROQ LPU (${generatedIdea.source.toUpperCase()})`
                    : generatedIdea.source && generatedIdea.source.includes('openai')
                      ? '🌐 FREE OPENAI / DEEPSEEK'
                      : '🤖 Built-in Matrix'}
                </span>
                {generatedIdea.chosen_angle && (
                  <span className="text-[10px] font-medium px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800/60 max-w-xs truncate" title={generatedIdea.chosen_angle}>
                    {generatedIdea.generation_type === 'surprise_seed' ? '🎲 ' : '🎯 '} {generatedIdea.chosen_angle}
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => sendIdeaToStudio(generatedIdea, navigate)}
                  className="py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white font-bold text-xs flex items-center space-x-1.5 transition border border-slate-700/60"
                >
                  <span>Send to Studio</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickProduce(generatedIdea, navigate)}
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
              <span className="text-xs text-slate-500 font-mono uppercase">Stock Footage Keywords</span>
              <div className="flex flex-wrap gap-1.5">
                {(generatedIdea.keywords || []).map((k, i) => (
                  <span key={i} className="text-xs px-2 py-0.5 rounded bg-violet-950 text-violet-300 border border-violet-800/40 font-mono">
                    {k}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 1M+ Proven Viral Outliers Vault */}
      <div className="p-5 rounded-2xl bg-[#12121a] border border-amber-500/30 space-y-4 shadow-xl shadow-amber-500/5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/60 pb-3">
          <div>
            <div className="flex items-center space-x-2">
              <Flame className="w-5 h-5 text-amber-400 fill-amber-400" />
              <h3 className="font-black text-sm text-white uppercase tracking-wider">1M–15M+ Viral Outliers Vault</h3>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30 font-mono">
                Source of Truth
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Battle-tested psychological hooks with 1M–15M+ views. Clone structure, retention curve & multi-word tags in 1 click.
            </p>
          </div>

          {/* Category Filter */}
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-800 rounded-lg p-1 text-[11px] font-mono">
            {['all', 'survival_paradox', 'forbidden_experiment', 'fbi_interrogation_trap'].map(cat => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded-md transition ${
                  selectedCategory === cat
                    ? 'bg-amber-500 text-black font-black'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {cat === 'all' ? 'All' : cat === 'survival_paradox' ? 'Survival' : cat === 'forbidden_experiment' ? 'Experiments' : 'FBI Traps'}
              </button>
            ))}
          </div>
        </div>

        {/* Outlier Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {filteredOutliers.map((o) => (
            <div
              key={o.id}
              className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-amber-500/40 transition flex flex-col justify-between space-y-3 group"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30 font-bold flex items-center space-x-1">
                    <Trophy className="w-3 h-3" />
                    <span>{o.views_baseline || '1M+ Views'}</span>
                  </span>
                  <span className="text-[10px] font-mono text-slate-500 uppercase">
                    {(o.category || '').replace('_', ' ')}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-white group-hover:text-amber-300 transition leading-snug">
                  "{o.hook || o.title}"
                </h4>
                <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">
                  {o.concept}
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-slate-800/60">
                <div className="flex flex-wrap gap-1">
                  {(o.search_tags || []).slice(0, 3).map((tag, idx) => (
                    <span key={idx} className="text-[10px] px-1.5 py-0.5 rounded bg-black/40 text-slate-400 font-mono">
                      #{tag}
                    </span>
                  ))}
                </div>

                <button
                  type="button"
                  onClick={() => handleGenerateIdea(o.category, false, 1, o.id)}
                  disabled={generatingIdea}
                  className="w-full py-2 px-3 rounded-lg bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black font-black text-xs flex items-center justify-center space-x-1.5 transition shadow-lg shadow-amber-500/10 disabled:opacity-50"
                >
                  <Zap className="w-3.5 h-3.5 fill-current" />
                  <span>Clone Hook & Script</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

