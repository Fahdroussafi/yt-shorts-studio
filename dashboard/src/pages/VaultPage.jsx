import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Download, Copy, Check, Send, Trash2, Layers, Clock } from 'lucide-react';
import { useApp } from '../context/AppContext';
import Pagination from '../components/Pagination';

export default function VaultPage() {
  const {
    videos, loadingVideos, fetchVideos,
    authToken,
    setPreviewVideo,
    copiedId, copyMetadata,
    handleDeleteVideo,
    setDispatchVideoId
  } = useApp();

  const navigate = useNavigate();
  const [vaultPage, setVaultPage] = useState(1);
  const [vaultPerPage, setVaultPerPage] = useState(6);

  useEffect(() => {
    fetchVideos();
  }, []);

  // Clamping effects when lists resize
  useEffect(() => {
    const maxPage = Math.max(1, Math.ceil(videos.length / vaultPerPage));
    if (vaultPage > maxPage) setVaultPage(maxPage);
  }, [videos.length, vaultPerPage, vaultPage]);

  const paginatedVaultVideos = videos.slice(
    (vaultPage - 1) * vaultPerPage,
    vaultPage * vaultPerPage
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">Video Vault</h1>
          <p className="text-sm text-slate-400">Inspect, preview, and dispatch local rendered shorts</p>
        </div>
        <span className="text-xs font-mono text-slate-400">{videos.length} videos stored locally</span>
      </div>

      {loadingVideos && videos.length === 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {[1, 2, 3, 4, 5, 6].map((n) => (
            <div key={n} className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-4 animate-pulse">
              <div className="flex items-center justify-between">
                <div className="h-4 w-16 bg-slate-800 rounded"></div>
                <div className="h-4 w-24 bg-slate-800 rounded"></div>
              </div>
              <div className="space-y-2">
                <div className="h-4 w-full bg-slate-800 rounded"></div>
                <div className="h-4 w-3/4 bg-slate-800 rounded"></div>
              </div>
              <div className="space-y-1.5 pt-2">
                <div className="h-3 w-full bg-slate-800/60 rounded"></div>
                <div className="h-3 w-5/6 bg-slate-800/60 rounded"></div>
              </div>
              <div className="pt-3 border-t border-slate-800/60 flex items-center space-x-2">
                <div className="h-8 flex-1 bg-slate-800 rounded-xl"></div>
                <div className="h-8 w-8 bg-slate-800 rounded-xl"></div>
                <div className="h-8 w-8 bg-slate-800 rounded-xl"></div>
                <div className="h-8 w-8 bg-slate-800 rounded-xl"></div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {paginatedVaultVideos.map((vid) => (
              <div 
                key={vid.id}
                className="p-5 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-violet-600/50 transition flex flex-col justify-between space-y-4 group"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-violet-400 uppercase">{vid.id}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      vid.motion_type === 'Real-Motion HD' 
                        ? 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60' 
                        : 'bg-amber-950/60 text-amber-300 border-amber-800/60'
                    }`}>
                      {vid.motion_type}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-white line-clamp-2 leading-snug">
                    {vid.title}
                  </h3>

                  <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">
                    {vid.description || "No SEO description generated."}
                  </p>
                </div>

                <div className="space-y-3 pt-2 border-t border-slate-800/60">
                  <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
                    <span className="flex items-center space-x-1">
                      <Layers className="w-3.5 h-3.5 text-slate-500" />
                      <span>{vid.size_mb} MB</span>
                    </span>
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      <span>{vid.modified.split(' ')[0]}</span>
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      type="button"
                      onClick={() => setPreviewVideo(vid)}
                      className="flex-1 py-2 px-3 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-semibold text-xs flex items-center justify-center space-x-1.5 transition shadow-lg shadow-violet-600/20"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Play</span>
                    </button>

                    <a
                      href={`/api/videos/${vid.id}/stream?token=${authToken}`}
                      download={`${vid.id}.mp4`}
                      title="Direct Download MP4"
                      className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-emerald-400 transition"
                    >
                      <Download className="w-4 h-4" />
                    </a>

                    <button
                      type="button"
                      onClick={() => copyMetadata(vid)}
                      title="Copy SEO metadata"
                      className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                    >
                      {copiedId === vid.id ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                    </button>

                    <button
                      type="button"
                      onClick={() => {
                        setDispatchVideoId(vid.id);
                        navigate('/dispatcher');
                      }}
                      title="Schedule or publish this video"
                      className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 transition"
                    >
                      <Send className="w-4 h-4" />
                    </button>

                    <button
                      type="button"
                      onClick={() => handleDeleteVideo(vid.id)}
                      title="Delete this short permanently"
                      className="p-2 rounded-xl bg-slate-800 hover:bg-red-950 text-slate-400 hover:text-red-400 transition"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-2xl bg-[#12121a] border border-slate-800/80 overflow-hidden">
            <Pagination
              currentPage={vaultPage}
              totalItems={videos.length}
              perPage={vaultPerPage}
              onPageChange={setVaultPage}
              onPerPageChange={setVaultPerPage}
              perPageOptions={[6, 9, 12, 24, 48]}
            />
          </div>
        </div>
      )}
    </div>
  );
}
