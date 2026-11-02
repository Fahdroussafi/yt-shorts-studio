import React from 'react';
import { Film, X, AlertCircle, CheckCircle2, ExternalLink, RefreshCw, Check, Upload, Key } from 'lucide-react';

export default function ChannelModal({
  isOpen,
  onClose,
  channelData,
  inputChannelHandle,
  setInputChannelHandle,
  tokenUploadError,
  setTokenUploadError,
  showChangeCredentials,
  setShowChangeCredentials,
  oauthStep,
  setOauthStep,
  oauthAuthUrl,
  inputOauthCode,
  setInputOauthCode,
  exchangingOauth,
  uploadingTokenFile,
  showManualJson,
  setShowManualJson,
  inputYoutubeToken,
  setInputYoutubeToken,
  savingChannel,
  handleTokenFileUpload,
  handleStartGoogleAuth,
  handleCompleteOauthCode,
  handleSaveChannel,
  handleDisconnectYoutube
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#12121a] border border-slate-800 rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl relative max-h-[90vh] overflow-y-auto my-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-violet-950/60 border border-violet-800/50">
              <Film className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <h3 className="font-extrabold text-white text-base">Channel & YouTube Connection</h3>
              <p className="text-[11px] text-violet-400 font-mono">Isolated Per User • Private Upload Token & Stats</p>
            </div>
          </div>
          <button 
            onClick={() => { onClose(); setOauthStep('initial'); setTokenUploadError(''); }} 
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-slate-400 leading-relaxed">
          Connect your YouTube Channel via credentials file or OAuth token. Every account has its own isolated upload target and quota.
        </p>

        {/* CHANNEL HANDLE INPUT */}
        <div className="space-y-1.5">
          <label className="text-xs font-mono uppercase text-slate-400 flex items-center justify-between">
            <span>YouTube Channel Handle</span>
            <span className="text-slate-500 font-mono text-[10px]">e.g. @MyChannel</span>
          </label>
          <input
            type="text"
            value={inputChannelHandle}
            onChange={(e) => setInputChannelHandle(e.target.value)}
            placeholder="@MyYouTubeChannel"
            className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-sm text-white font-mono"
          />
        </div>

        {/* ERROR DISPLAY */}
        {tokenUploadError && (
          <div className="p-3 rounded-xl bg-red-950/50 border border-red-800/60 text-xs text-red-300 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <span className="break-all">{tokenUploadError}</span>
          </div>
        )}

        {/* OAUTH CREDENTIALS SECTION */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono uppercase text-slate-400">
              <span>YouTube OAuth Status</span>
            </label>
            {channelData?.has_youtube_token ? (
              <span className="text-emerald-400 font-bold text-xs flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>Connected</span>
              </span>
            ) : (
              <span className="text-amber-400 font-bold text-xs">Not Connected</span>
            )}
          </div>

          {channelData?.has_youtube_token && !showChangeCredentials ? (
            <div className="p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-800/40 text-xs text-emerald-300 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>OAuth token active and verified for uploads.</span>
              </div>
              <div className="flex items-center space-x-1.5">
                <button
                  type="button"
                  onClick={() => setShowChangeCredentials(true)}
                  className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
                >
                  Update
                </button>
                <button
                  type="button"
                  onClick={handleDisconnectYoutube}
                  className="px-2.5 py-1 rounded-lg bg-red-950/60 border border-red-800/60 hover:bg-red-900 text-red-300 text-xs transition"
                >
                  Disconnect
                </button>
              </div>
            </div>
          ) : oauthStep === 'awaiting_code' ? (
            /* STEP 2: AUTHORIZE ON GOOGLE AND PASTE CODE */
            <div className="p-4 rounded-2xl bg-violet-950/20 border border-violet-800/40 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-violet-300 uppercase tracking-wider">Step 2 · Google Authorization</span>
                <button 
                  type="button"
                  onClick={() => setOauthStep('initial')}
                  className="text-[11px] text-slate-400 hover:text-white underline"
                >
                  Back
                </button>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">
                1. Click the button below to authorize YouTube access with your Google account in a new tab:
              </p>

              <a
                href={oauthAuthUrl}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-violet-600 hover:bg-violet-500 font-bold text-xs text-white shadow-lg shadow-violet-600/30 transition text-center"
              >
                <ExternalLink className="w-4 h-4" />
                <span>Authorize Channel on Google</span>
              </a>

              <div className="pt-2 border-t border-slate-800/80 space-y-2">
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  2. After approving, Google redirects to <code className="text-violet-300 font-mono">http://localhost/?code=...</code>. Even if browser shows &quot;Site can&apos;t be reached&quot;, copy the entire URL or code from the address bar and paste here:
                </p>
                <div className="flex items-center space-x-2">
                  <input
                    type="text"
                    value={inputOauthCode}
                    onChange={(e) => setInputOauthCode(e.target.value)}
                    placeholder="Paste code=... or full http://localhost/?code=..."
                    className="flex-1 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-xs text-white font-mono"
                  />
                  <button
                    type="button"
                    onClick={handleCompleteOauthCode}
                    disabled={exchangingOauth || !inputOauthCode.trim()}
                    className="py-2 px-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 font-bold text-xs text-white transition flex items-center space-x-1.5 shrink-0 shadow-lg"
                  >
                    {exchangingOauth ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    <span>Finish</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* INITIAL STEP: UPLOAD TOKEN OR CLIENT SECRET FILE */
            <div className="space-y-3">
              <label className="relative border-2 border-dashed border-violet-800/40 hover:border-violet-500/70 bg-violet-950/10 hover:bg-violet-950/20 rounded-2xl p-5 flex flex-col items-center justify-center text-center cursor-pointer transition group">
                <input
                  type="file"
                  accept=".json"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      handleTokenFileUpload(e.target.files[0]);
                    }
                  }}
                />
                <div className="p-3 rounded-full bg-violet-900/30 text-violet-400 group-hover:scale-110 transition duration-200 mb-2">
                  {uploadingTokenFile ? (
                    <RefreshCw className="w-5 h-5 animate-spin text-violet-300" />
                  ) : (
                    <Upload className="w-5 h-5" />
                  )}
                </div>
                <span className="text-xs font-bold text-white group-hover:text-violet-300 transition">
                  {uploadingTokenFile ? "Reading & processing file..." : "Click or drop credential JSON file here"}
                </span>
                <span className="text-[11px] text-slate-400 mt-1">
                  Upload <code className="text-violet-400">token.json</code> or Google Cloud <code className="text-violet-400">client_secret_XXXX.json</code>
                </span>
              </label>

              {channelData?.has_client_secret && (
                <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
                  <div className="flex items-center space-x-2 text-slate-300">
                    <Key className="w-4 h-4 text-violet-400" />
                    <span>Google Client Credentials detected</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleStartGoogleAuth}
                    disabled={uploadingTokenFile}
                    className="py-1.5 px-3 rounded-lg bg-violet-600 hover:bg-violet-500 font-bold text-xs text-white transition flex items-center space-x-1"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    <span>Connect Google Account</span>
                  </button>
                </div>
              )}

              <div className="pt-1">
                <button
                  type="button"
                  onClick={() => setShowManualJson(!showManualJson)}
                  className="text-[11px] text-slate-400 hover:text-slate-200 underline font-mono"
                >
                  {showManualJson ? "Hide manual JSON input" : "Or paste JSON credentials manually"}
                </button>
                {showManualJson && (
                  <textarea
                    rows={3}
                    value={inputYoutubeToken}
                    onChange={(e) => setInputYoutubeToken(e.target.value)}
                    placeholder='Paste contents of token.json or client_secret.json here'
                    className="mt-2 w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus:border-violet-500 outline-none text-xs text-white font-mono"
                  />
                )}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-end space-x-2 pt-2">
          <button
            type="button"
            onClick={() => { onClose(); setOauthStep('initial'); setTokenUploadError(''); }}
            className="py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 font-bold text-xs text-slate-300 transition"
          >
            Close
          </button>
          <button
            type="button"
            onClick={handleSaveChannel}
            disabled={savingChannel || uploadingTokenFile || exchangingOauth}
            className="py-2.5 px-5 rounded-xl bg-violet-600 hover:bg-violet-500 font-bold text-xs text-white transition flex items-center space-x-1.5 shadow-lg shadow-violet-600/20"
          >
            {savingChannel ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
            <span>Save Channel</span>
          </button>
        </div>
      </div>
    </div>
  );
}
