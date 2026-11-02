import React from 'react';
import { Cpu, X, AlertCircle, ExternalLink, RefreshCw, Check } from 'lucide-react';

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
            <div className="p-2 rounded-xl bg-cyan-950/60 border border-cyan-800/50">
              <Cpu className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h3 className="font-extrabold text-white text-base">Gemini 3.1 Flash Lite Setup</h3>
              <p className="text-[11px] text-cyan-400 font-mono">500 Free Requests/Day • 1.0s Speed • Zero Cost</p>
            </div>
          </div>
          <button 
            onClick={() => { onClose(); setAiKeyError(''); }} 
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          Gemini 3 Flash is <strong className="text-emerald-300">pre-configured and ready to use</strong> (zero setup required). You do not need to type anything! You can optionally paste your own private Google AI Studio key below if you wish to use your own quota:
        </p>

        {/* Error Banner */}
        {aiKeyError && (
          <div className="p-3 rounded-xl bg-red-950/50 border border-red-800/60 text-xs text-red-300 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <span className="break-all">{aiKeyError}</span>
          </div>
        )}

        <div className="space-y-1.5">
          <label className="text-xs font-mono uppercase text-slate-400 flex flex-wrap items-center justify-between gap-1">
            <span>Google AI Studio API Key (Optional)</span>
            {aiSettings?.has_key && (
              <span className="text-emerald-400 font-bold text-[11px]">
                {aiSettings.is_custom_key ? "Custom Key Active" : "Pre-Configured System Key"}
              </span>
            )}
          </label>
          <input
            type="password"
            value={inputApiKey}
            onChange={(e) => { setInputApiKey(e.target.value); setAiKeyError(''); }}
            placeholder={aiSettings?.has_key ? `Current: ${aiSettings.masked_key}` : "AIzaSy..."}
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-cyan-500 outline-none text-sm text-white font-mono"
          />
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-3 border-t border-slate-800/80">
          <a 
            href="https://aistudio.google.com/app/apikey" 
            target="_blank" 
            rel="noreferrer"
            className="text-xs text-cyan-400 hover:text-cyan-300 underline flex items-center space-x-1"
          >
            <span>Get Free Key (Google AI Studio)</span>
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
              className="py-2.5 px-4 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 font-bold text-xs text-white transition flex items-center justify-center space-x-1.5 shadow-lg shadow-cyan-600/20 whitespace-nowrap flex-shrink-0"
            >
              {savingKey ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
              <span>{savingKey ? "Verifying with Google..." : "Save Key"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

