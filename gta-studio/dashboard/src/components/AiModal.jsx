import React from 'react';
import { Cpu, X, AlertCircle, ExternalLink, RefreshCw, Check, Zap, Sparkles } from 'lucide-react';

export default function AiModal({
  isOpen,
  onClose,
  aiSettings,
  inputApiKey,
  setInputApiKey,
  savingKey,
  aiKeyError,
  setAiKeyError,
  onSave,
  onReset
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#12121a] border border-slate-800 rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative my-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-orange-950/60 border border-orange-800/50">
              <Zap className="w-5 h-5 text-orange-400 fill-current" />
            </div>
            <div>
              <h3 className="font-extrabold text-white text-base">Groq Cloud LPU Engine</h3>
              <p className="text-[11px] text-orange-400 font-mono">0.6s Instant Speed • 1,000 Free RPD • Limitless Zero-Key Fallback</p>
            </div>
          </div>
          <button 
            onClick={() => { onClose(); setAiKeyError(''); }} 
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2 text-xs leading-relaxed text-slate-300">
          <div className="flex items-center space-x-1.5 font-bold text-white">
            <Sparkles className="w-4 h-4 text-amber-400" />
            <span>Dual-Engine AI Architecture</span>
          </div>
          <ul className="space-y-1 text-slate-400 list-disc list-inside text-[11px]">
            <li><strong className="text-orange-300">Primary (Groq LPU)</strong>: Pre-configured system key active with ~1,000 free requests/day. Generates 4-act scripts in under 1 second.</li>
            <li><strong className="text-cyan-300">Auto-Fallback (OpenAI / DeepSeek)</strong>: 100% Free limitless engine automatically kicks in if limits are ever reached. Zero setup needed.</li>
          </ul>
        </div>

        {/* Error Banner */}
        {aiKeyError && (
          <div className="p-3 rounded-xl bg-red-950/50 border border-red-800/60 text-xs text-red-300 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <span className="break-all">{aiKeyError}</span>
          </div>
        )}

        <div className="space-y-2">
          <label className="text-xs font-mono uppercase text-slate-400 flex flex-wrap items-center justify-between gap-1">
            <span>Groq Cloud API Key (Optional)</span>
            {aiSettings?.has_key && (
              <span className="text-emerald-400 font-bold text-[11px]">
                {aiSettings.is_custom_key ? "Custom Groq Key Active" : "Pre-Configured System Key"}
              </span>
            )}
          </label>
          <input
            type="password"
            value={inputApiKey}
            onChange={(e) => { setInputApiKey(e.target.value); setAiKeyError(''); }}
            placeholder={aiSettings?.has_key ? `Current: ${aiSettings.masked_key}` : "gsk_..."}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-orange-500 outline-none text-sm text-white font-mono"
          />
          <p className="text-[11px] text-slate-500">
            Paste your personal <code className="text-orange-400">gsk_...</code> key to use your own private Groq quota.
          </p>
        </div>

        {/* Step-by-Step Guide for User */}
        <div className="p-3 rounded-xl bg-black/40 border border-slate-800/60 text-[11px] text-slate-400 space-y-1.5">
          <span className="font-bold text-slate-300 uppercase tracking-wider text-[10px] font-mono">How to get your own 100% free Groq key:</span>
          <ol className="list-decimal list-inside space-y-0.5 leading-normal">
            <li>Open <a href="https://console.groq.com/keys" target="_blank" rel="noreferrer" className="text-orange-400 underline hover:text-orange-300">console.groq.com/keys</a> in a new tab.</li>
            <li>Sign in with Google or GitHub (No credit card needed).</li>
            <li>Click <strong>"Create API Key"</strong>, copy your <code className="text-slate-300">gsk_...</code> string, and paste it above.</li>
          </ol>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 border-t border-slate-800/80">
          <a 
            href="https://console.groq.com/keys" 
            target="_blank" 
            rel="noreferrer"
            className="text-xs text-orange-400 hover:text-orange-300 underline flex items-center space-x-1"
          >
            <span>Open Groq Console Keys</span>
            <ExternalLink className="w-3 h-3" />
          </a>

          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto justify-end">
            {aiSettings?.is_custom_key && (
              <button
                type="button"
                onClick={onReset}
                disabled={savingKey}
                className="py-2.5 px-3.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition whitespace-nowrap flex-shrink-0"
              >
                Revert to Default
              </button>
            )}
            <button
              type="button"
              onClick={onSave}
              disabled={savingKey || !inputApiKey.trim()}
              className="py-2.5 px-4 rounded-xl bg-orange-600 hover:bg-orange-500 disabled:opacity-50 font-bold text-xs text-white transition flex items-center justify-center space-x-1.5 shadow-lg shadow-orange-600/20 whitespace-nowrap flex-shrink-0"
            >
              {savingKey ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
              <span>{savingKey ? "Verifying with Groq..." : "Verify & Save Key"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
