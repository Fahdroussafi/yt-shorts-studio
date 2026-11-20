import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

export default function VideoPreviewModal({ previewVideo, authToken, onClose }) {
  const [isLandscape, setIsLandscape] = useState(false);

  useEffect(() => {
    setIsLandscape(false);
  }, [previewVideo?.id]);

  if (!previewVideo) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className={`bg-[#12121a] border border-slate-800 rounded-3xl overflow-hidden ${isLandscape ? 'max-w-4xl' : 'max-w-md'} w-full shadow-2xl relative flex flex-col transition-all`}>
        <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
          <div className="flex items-center space-x-2 min-w-0 pr-2">
            <span className="font-mono text-xs font-bold text-violet-400 uppercase shrink-0">{previewVideo.id}</span>
            <span className="text-xs text-slate-300 truncate">{previewVideo.title}</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Video Player */}
        <div className={`relative bg-black flex items-center justify-center ${isLandscape ? 'aspect-video max-h-[75vh]' : 'aspect-[9/16] max-h-[600px]'}`}>
          <video
            src={`/api/videos/${previewVideo.id}/stream?token=${authToken}`}
            controls
            autoPlay
            onLoadedMetadata={(e) => {
              const v = e.currentTarget;
              setIsLandscape(v.videoWidth > v.videoHeight);
            }}
            className="w-full h-full object-contain"
          />
        </div>

        <div className="p-4 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>Size: {previewVideo.size_mb} MB</span>
          <span>Format: {previewVideo.motion_type}</span>
        </div>
      </div>
    </div>
  );
}
