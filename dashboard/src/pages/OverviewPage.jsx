import React, { useState, useEffect } from 'react';
import { 
  BarChart3, RefreshCw, Eye, Flame, Video, ArrowUpRight, 
  Calendar, Clock, ExternalLink 
} from 'lucide-react';
import { useApp } from '../context/AppContext';
import Pagination from '../components/Pagination';

function formatScheduleDate(isoStr) {
  if (!isoStr) return "Scheduled on YouTube";
  try {
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + ' · ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
  } catch {
    return isoStr;
  }
}

export default function OverviewPage() {
  const {
    stats, loadingStats, fetchStats,
    videos,
    syncingChannel, handleSyncChannel
  } = useApp();

  // Always refresh stats on mount so Vault deletions & status changes reflect instantly without F5
  useEffect(() => {
    fetchStats();
  }, []);

  const [tableTab, setTableTab] = useState('live'); // 'live' | 'scheduled' | 'all'
  const [tablePage, setTablePage] = useState(1);
  const [tablePerPage, setTablePerPage] = useState(10);

  const allTableVideos = stats?.videos || [];
  const topBreakout = allTableVideos.reduce((max, v) => (v.views > (max?.views || 0) ? v : max), null);
  const topBreakoutViews = topBreakout?.views || 0;
  const topBreakoutLabel = topBreakout && topBreakout.views > 0 ? (topBreakout.short_id?.replace('_', ' ') || 'Short') : 'None yet';

  const isScheduledVideo = (v) => {
    if (v.publish_at && new Date(v.publish_at) <= new Date()) return false;
    return v.status === 'SCHEDULED' || (v.publish_at && new Date(v.publish_at) > new Date());
  };

  const filteredTableVideos = allTableVideos
    .filter((v) => {
      if (v.status === 'DELETED_ON_YOUTUBE') return false;
      if (tableTab === 'live') return !isScheduledVideo(v) && (v.status === 'LIVE' || v.status === 'PRIVATE' || v.views > 0);
      if (tableTab === 'scheduled') return isScheduledVideo(v);
      return true;
    })
    .sort((a, b) => {
      if (tableTab === 'scheduled') {
        const dateA = a.publish_at ? new Date(a.publish_at).getTime() : NaN;
        const dateB = b.publish_at ? new Date(b.publish_at).getTime() : NaN;
        const timeA = isNaN(dateA) ? Infinity : dateA;
        const timeB = isNaN(dateB) ? Infinity : dateB;
        if (timeA !== timeB) return timeA - timeB;
        return (a.short_id || '').localeCompare(b.short_id || '');
      }
      if (tableTab === 'live') {
        const dateA = a.publish_at ? new Date(a.publish_at).getTime() : 0;
        const dateB = b.publish_at ? new Date(b.publish_at).getTime() : 0;
        if (dateA !== dateB) return dateB - dateA;
        const numA = parseInt((a.short_id || '').replace(/\D/g, '') || '0', 10);
        const numB = parseInt((b.short_id || '').replace(/\D/g, '') || '0', 10);
        return numB - numA;
      }
      return 0;
    });

  // Clamping effects when lists resize
  useEffect(() => {
    const total = filteredTableVideos.length;
    const maxPage = Math.max(1, Math.ceil(total / tablePerPage));
    if (tablePage > maxPage) setTablePage(maxPage);
  }, [filteredTableVideos.length, tablePerPage, tablePage]);

  const paginatedTableVideos = filteredTableVideos.slice(
    (tablePage - 1) * tablePerPage,
    tablePage * tablePerPage
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-white">Channel Analytics & Telemetry</h1>
          <p className="text-sm text-slate-400">Real-time performance audit for {stats?.channel_handle || "your channel"}</p>
        </div>
        <div className="text-xs px-3 py-1.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 flex items-center space-x-1.5 font-mono">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>FEED INDEXED</span>
        </div>
      </div>

      {/* Top Stats Metric Cards */}
      {loadingStats && !stats ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 space-y-3 animate-pulse">
              <div className="flex justify-between items-center">
                <div className="h-3 w-28 bg-slate-800 rounded"></div>
                <div className="h-4 w-4 bg-slate-800 rounded"></div>
              </div>
              <div className="h-8 w-20 bg-slate-800 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-slate-700 transition">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Total Channel Views</span>
              <Eye className="w-4 h-4 text-violet-400" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-3xl font-black text-white font-mono">{stats?.total_views || 0}</span>
              <span className="text-xs text-emerald-400 font-bold">+100% Organic</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-slate-700 transition">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Top Breakout Short</span>
              <Flame className="w-4 h-4 text-amber-500" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-3xl font-black text-amber-400 font-mono">
                {topBreakoutViews.toLocaleString()}
              </span>
              <span className="text-xs text-slate-400">
                views ({topBreakoutLabel})
              </span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-slate-700 transition">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Videos In Pipeline</span>
              <Video className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-3xl font-black text-white font-mono">{videos.length}</span>
              <span className="text-xs text-cyan-400 font-bold">1080x1920 HD</span>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-[#12121a] border border-slate-800/80 hover:border-slate-700 transition">
            <div className="flex items-center justify-between text-slate-400 text-xs">
              <span>Target Geographic RPM</span>
              <ArrowUpRight className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="mt-2 flex items-baseline space-x-2">
              <span className="text-3xl font-black text-emerald-400 font-mono">$0.25</span>
              <span className="text-xs text-slate-400">US/UK Tier 1</span>
            </div>
          </div>
        </div>
      )}

      {/* Unified Tracked Shorts Index & Velocity Table with Sub-Tabs */}
      <div className="rounded-2xl bg-[#12121a] border border-slate-800/80 overflow-hidden shadow-xl">
        <div className="p-4 border-b border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-violet-950/60 border border-violet-800/50">
              <BarChart3 className="w-4 h-4 text-violet-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="font-bold text-sm text-white">Tracked Video Index & Velocity Telemetry</h3>
                {loadingStats && (
                  <span className="flex items-center space-x-1 text-[10px] font-mono font-semibold text-cyan-400 bg-cyan-950/70 border border-cyan-800/50 px-2 py-0.5 rounded-full animate-pulse">
                    <RefreshCw className="w-2.5 h-2.5 animate-spin" />
                    <span>Syncing...</span>
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-400">Live view counts, motion retention comparison, and channel dispatch pipeline</p>
            </div>
          </div>

          {/* Sub-tabs: Live Tracked, Scheduled Pipeline, All + Channel Sync */}
          <div className="flex flex-wrap items-center gap-1.5 p-1 bg-slate-900/90 rounded-xl border border-slate-800 self-start md:self-auto">
            <button
              onClick={() => { setTableTab('live'); setTablePage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                tableTab === 'live'
                  ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Live Tracked</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 text-emerald-200">
                {allTableVideos.filter(v => !isScheduledVideo(v) && (v.status === 'LIVE' || v.status === 'PRIVATE' || v.views > 0 || (v.publish_at && new Date(v.publish_at) <= new Date()))).length}
              </span>
            </button>

            <button
              onClick={() => { setTableTab('scheduled'); setTablePage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                tableTab === 'scheduled'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Clock className="w-3 h-3 text-blue-300" />
              <span>Scheduled Pipeline</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-black/40 text-blue-200">
                {allTableVideos.filter(isScheduledVideo).length}
              </span>
            </button>

            <button
              onClick={() => { setTableTab('all'); setTablePage(1); }}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
                tableTab === 'all'
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <span>All ({allTableVideos.length})</span>
            </button>

            <div className="w-[1px] h-4 bg-slate-800 mx-0.5 hidden sm:block"></div>

            <div className="hidden sm:flex items-center space-x-1.5 px-2 py-1 rounded-lg bg-slate-950 border border-slate-800/80 text-[10px] font-mono text-emerald-400" title="Continuously synced with YouTube feed every 45 seconds">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>Auto-Sync Live</span>
            </div>

            <button
              onClick={handleSyncChannel}
              disabled={syncingChannel || loadingStats}
              className="px-2.5 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition text-cyan-300 hover:text-white bg-cyan-950/60 hover:bg-cyan-900/80 border border-cyan-800/60 disabled:opacity-50"
              title="Direct scan of your YouTube channel: auto-discovers and restores all live published shorts"
            >
              <RefreshCw className={`w-3 h-3 text-cyan-300 ${syncingChannel ? 'animate-spin' : ''}`} />
              <span>{syncingChannel ? 'Syncing...' : 'Sync Now'}</span>
            </button>
          </div>
        </div>

        {loadingStats && (
          <div className="h-0.5 w-full bg-slate-800/80 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-violet-500 via-cyan-400 to-violet-500 animate-[pulse_1s_ease-in-out_infinite] w-full"></div>
          </div>
        )}

        <div className={`overflow-x-auto transition-opacity ${loadingStats ? 'opacity-85' : 'opacity-100'}`}>
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/60 text-slate-400 uppercase font-mono border-b border-slate-800/80">
              <tr>
                <th className="py-3 px-4">Short ID</th>
                <th className="py-3 px-4">Title / Topic</th>
                <th className="py-3 px-4">Format</th>
                <th className="py-3 px-4 min-w-[180px]">
                  {tableTab === 'scheduled' ? (
                    <span className="flex items-center space-x-1.5 text-blue-300">
                      <Calendar className="w-3.5 h-3.5 text-blue-400" />
                      <span>Scheduled Drop (Earliest First)</span>
                    </span>
                  ) : (
                    'Views & Velocity'
                  )}
                </th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loadingStats && allTableVideos.length === 0 ? (
                [...Array(tablePerPage > 5 ? 5 : tablePerPage)].map((_, i) => (
                  <tr key={`tbl-skel-${i}`} className="animate-pulse border-b border-slate-800/40">
                    <td className="py-3.5 px-4"><div className="h-3.5 w-16 bg-slate-800/80 rounded"></div></td>
                    <td className="py-3.5 px-4"><div className="h-3.5 w-48 bg-slate-800/80 rounded"></div></td>
                    <td className="py-3.5 px-4"><div className="h-4 w-20 bg-slate-800/80 rounded"></div></td>
                    <td className="py-3.5 px-4"><div className="h-3.5 w-32 bg-slate-800/80 rounded"></div></td>
                    <td className="py-3.5 px-4"><div className="h-4 w-16 bg-slate-800/80 rounded"></div></td>
                    <td className="py-3.5 px-4 text-right"><div className="h-3.5 w-12 bg-slate-800/80 rounded ml-auto"></div></td>
                  </tr>
                ))
              ) : paginatedTableVideos.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 font-mono">
                    No videos found in this tab.
                  </td>
                </tr>
              ) : (
                paginatedTableVideos.map((item) => {
                  const maxViews = 1100;
                  const pct = Math.min(100, Math.max(5, (item.views / maxViews) * 100));
                  const isMotion = item.motion_type === 'Real-Motion HD' || (!item.short_id?.startsWith('short_01') && !item.short_id?.startsWith('short_02') && !item.short_id?.startsWith('short_03'));
                  const isScheduled = isScheduledVideo(item);

                  return (
                    <tr key={item.short_id} className="hover:bg-slate-900/40 transition">
                      <td className="py-3 px-4 font-mono font-bold text-violet-300">
                        <div className="flex items-center space-x-1.5">
                          <span>{item.short_id.toUpperCase()}</span>
                          {item.storage_status === 'CLOUD_ARCHIVED' && (
                            <span className="text-[9px] font-sans font-medium px-1.5 py-0.2 rounded bg-sky-950 text-sky-300 border border-sky-800/60" title="Tracked directly from YouTube channel (local MP4 purged to save VPS disk space)">
                              ☁️ Cloud
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-slate-200 max-w-xs">
                        <div className="truncate font-medium text-slate-100" title={item.title}>
                          {item.title || "Scheduled Short"}
                        </div>
                        {item.publish_at && (
                          <div className="text-[10px] text-slate-400 font-mono mt-0.5 flex items-center space-x-1">
                            <Calendar className="w-3 h-3 text-violet-400/80 shrink-0" />
                            <span>{item.status === 'LIVE' ? 'Published ' : 'Drops '}{formatScheduleDate(item.publish_at)}</span>
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {isMotion ? (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800/50">
                            Real Motion HD
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800/50">
                            Still Pilot
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {isScheduled ? (
                          <div className="flex items-center space-x-2 text-blue-300 font-mono text-xs">
                            <Clock className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                            <span className="font-semibold">{formatScheduleDate(item.publish_at)}</span>
                          </div>
                        ) : (
                          <div>
                            <div className="flex items-center justify-between text-xs mb-1 font-mono">
                              <span className="font-bold text-white">{item.views.toLocaleString()} views</span>
                              <span className="text-[10px] text-slate-400">
                                {item.short_id === 'short_04' ? '🚀 1.06k Breakout' : item.short_id === 'short_06' ? '🔥 339 Velocity' : isMotion ? 'Motion HD' : 'Static'}
                              </span>
                            </div>
                            <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden border border-slate-800">
                              <div 
                                style={{ width: `${pct}%` }} 
                                className={`h-full rounded-full transition-all duration-500 ${
                                  item.short_id === 'short_04'
                                    ? 'bg-gradient-to-r from-emerald-500 to-cyan-500 shadow-sm shadow-emerald-500/50'
                                    : item.short_id === 'short_06' 
                                      ? 'bg-gradient-to-r from-amber-500 to-orange-500 shadow-sm shadow-orange-500/50' 
                                      : isMotion 
                                        ? 'bg-gradient-to-r from-cyan-500 to-blue-500' 
                                        : 'bg-gradient-to-r from-violet-600 to-purple-500'
                                }`}
                              ></div>
                            </div>
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {item.status === 'LIVE' || (!isScheduled && item.publish_at && new Date(item.publish_at) <= new Date()) ? (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/60 flex items-center space-x-1 w-fit">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                            <span>LIVE</span>
                          </span>
                        ) : isScheduled ? (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/60 flex items-center space-x-1 w-fit">
                            <Clock className="w-2.5 h-2.5 text-blue-400" />
                            <span>SCHEDULED</span>
                          </span>
                        ) : (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                            PRIVATE
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {item.url ? (
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center space-x-1 text-violet-400 hover:text-violet-300 font-medium"
                          >
                            <span>{isScheduled ? 'YouTube' : 'Watch'}</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        ) : (
                          <span className="text-slate-600 text-[11px] font-mono">Ready</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <Pagination
          currentPage={tablePage}
          totalItems={filteredTableVideos.length}
          perPage={tablePerPage}
          onPageChange={setTablePage}
          onPerPageChange={setTablePerPage}
          perPageOptions={[5, 10, 20, 50]}
        />
      </div>
    </div>
  );
}
