import React, { useEffect, useState } from 'react';
import { Video, CheckCircle, Clock, Upload, ArrowRight, RefreshCw, AlertCircle, Film } from 'lucide-react';
import { api } from '../api';

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
  if (!seconds) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function Dashboard({ onNavigate }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard statistics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[300px]">
        <div className="flex items-center gap-3 text-[var(--adm-muted)]">
          <RefreshCw className="w-5 h-5 animate-spin text-[var(--adm-p)]" />
          <span className="text-xs font-semibold uppercase tracking-wider">Loading metrics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-panel max-w-lg mx-auto text-center mt-8">
        <AlertCircle className="w-8 h-8 text-[var(--adm-del)] mx-auto mb-2" />
        <h3 className="text-sm font-black uppercase text-[var(--adm-text)] mb-1">Error Loading Dashboard</h3>
        <p className="text-xs text-[var(--adm-muted)] mb-4">{error}</p>
        <button onClick={fetchStats} className="button-primary">
          <RefreshCw className="w-3.5 h-3.5" /> Try Again
        </button>
      </div>
    );
  }

  const videoStats = stats?.videos || { total: 0, published: 0, draft: 0, archived: 0 };
  const recentVideos = stats?.recent_videos || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b-2 border-[var(--adm-text)] pb-4">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider text-[var(--adm-text)]">
            Dashboard Overview
          </h1>
          <p className="text-xs text-[var(--adm-muted)] mt-1">
            Platform video metrics, storage stream health, and recent uploads
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigate('upload')}
            className="button-primary"
          >
            <Upload className="w-3.5 h-3.5" /> Upload Video
          </button>
          <button
            onClick={fetchStats}
            title="Refresh metrics"
            className="action-btn-pro"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Primary 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Total Videos */}
        <div className="admin-panel p-4 mb-0">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-wider text-[var(--adm-muted)]">
              Total Videos
            </span>
            <div className="p-1.5 bg-[var(--adm-bg)] border border-[var(--adm-border-m)] text-[var(--adm-p)]">
              <Film className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <span className="text-3xl font-black text-[var(--adm-text)]">{videoStats.total}</span>
          </div>
          <p className="text-[11px] text-[var(--adm-muted)] mt-1">Stored across all categories</p>
        </div>

        {/* Published Videos */}
        <div className="admin-panel p-4 mb-0">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-wider text-emerald-600">
              Published Videos
            </span>
            <div className="p-1.5 bg-emerald-50 border border-emerald-600 text-emerald-700">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <span className="text-3xl font-black text-emerald-700">{videoStats.published}</span>
          </div>
          <p className="text-[11px] text-[var(--adm-muted)] mt-1">Live in Telegram bot catalog</p>
        </div>

        {/* Draft Videos */}
        <div className="admin-panel p-4 mb-0">
          <div className="flex items-center justify-between">
            <span className="text-xs font-black uppercase tracking-wider text-amber-600">
              Draft Videos
            </span>
            <div className="p-1.5 bg-amber-50 border border-amber-600 text-amber-700">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <span className="text-3xl font-black text-amber-700">{videoStats.draft}</span>
          </div>
          <p className="text-[11px] text-[var(--adm-muted)] mt-1">Pending review & publishing</p>
        </div>
      </div>

      {/* Recent Uploads Section */}
      <div className="admin-panel p-0 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-[var(--adm-border-m)] bg-[var(--adm-bg)]">
          <div>
            <h2 className="text-xs font-black uppercase tracking-wider text-[var(--adm-text)]">
              Recent Uploads
            </h2>
            <p className="text-[11px] text-[var(--adm-muted)]">Latest videos streamed to Telegram storage</p>
          </div>
          <button
            onClick={() => onNavigate('videos')}
            className="inline-flex items-center gap-1 text-xs font-bold text-[var(--adm-p)] hover:underline uppercase"
          >
            View all videos <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {recentVideos.length === 0 ? (
          <div className="p-8 text-center text-[var(--adm-muted)]">
            <Film className="w-8 h-8 mx-auto mb-2 text-[var(--adm-muted)] opacity-40" />
            <p className="text-xs font-bold text-[var(--adm-text)]">No videos uploaded yet</p>
            <p className="text-[11px] text-[var(--adm-muted)] mt-1">Upload your first video to see it here.</p>
            <button
              onClick={() => onNavigate('upload')}
              className="mt-3 button-primary"
            >
              <Upload className="w-3.5 h-3.5" /> Upload Video
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[var(--adm-text)] text-[var(--adm-card)] uppercase font-black text-[10px] tracking-wider">
                  <th className="py-2.5 px-4">Title</th>
                  <th className="py-2.5 px-4">Status</th>
                  <th className="py-2.5 px-4">Duration</th>
                  <th className="py-2.5 px-4">Size</th>
                  <th className="py-2.5 px-4">Uploaded</th>
                  <th className="py-2.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--adm-border-l)]">
                {recentVideos.map((video) => (
                  <tr key={video.id} className="hover:bg-[var(--adm-bg)] transition">
                    <td className="py-3 px-4 font-bold text-[var(--adm-text)]">
                      {video.title}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge-pro ${video.status === 'published' ? 'active' : 'muted'}`}>
                        {video.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[var(--adm-muted)]">
                      {formatDuration(video.duration)}
                    </td>
                    <td className="py-3 px-4 text-[var(--adm-muted)]">
                      {formatBytes(video.file_size)}
                    </td>
                    <td className="py-3 px-4 text-[var(--adm-muted)]">
                      {new Date(video.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onNavigate('videos')}
                        className="action-btn-pro"
                      >
                        Manage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
