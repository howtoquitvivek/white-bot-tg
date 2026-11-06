import React, { useEffect, useState } from 'react';
import {
  Search,
  Globe,
  EyeOff,
  Archive,
  Trash2,
  Edit2,
  RefreshCw,
  AlertCircle,
  Video as VideoIcon,
  X,
  Tag,
} from 'lucide-react';
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

export function ManageVideos({ onNavigate }) {
  const [videos, setVideos] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Modals
  const [editingVideo, setEditingVideo] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editCategoryIds, setEditCategoryIds] = useState([]);
  const [savingEdit, setSavingEdit] = useState(false);

  const [deletingVideo, setDeletingVideo] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchVideos = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getVideos({
        search: search.trim(),
        status: statusFilter,
      });
      setVideos(data.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load videos.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const data = await api.getCategories();
      setCategories(data.items || []);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchVideos();
  }, [statusFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchVideos();
  };

  // State transitions
  const handlePublish = async (id) => {
    try {
      await api.publishVideo(id);
      fetchVideos();
    } catch (err) {
      alert('Failed to publish video: ' + err.message);
    }
  };

  const handleUnpublish = async (id) => {
    try {
      await api.unpublishVideo(id);
      fetchVideos();
    } catch (err) {
      alert('Failed to unpublish video: ' + err.message);
    }
  };

  const handleArchive = async (id) => {
    try {
      await api.archiveVideo(id);
      fetchVideos();
    } catch (err) {
      alert('Failed to archive video: ' + err.message);
    }
  };

  // Edit Modal Handlers
  const openEditModal = (video) => {
    setEditingVideo(video);
    setEditTitle(video.title);
    setEditDescription(video.description || '');
    setEditCategoryIds(video.categories ? video.categories.map((c) => c.id) : []);
  };

  const toggleEditCategory = (catId) => {
    setEditCategoryIds((prev) =>
      prev.includes(catId) ? prev.filter((id) => id !== catId) : [...prev, catId]
    );
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editingVideo) return;
    try {
      setSavingEdit(true);
      await api.updateVideo(editingVideo.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || null,
        category_ids: editCategoryIds,
      });
      setEditingVideo(null);
      fetchVideos();
    } catch (err) {
      alert('Failed to update video: ' + err.message);
    } finally {
      setSavingEdit(false);
    }
  };

  // Delete Modal Handlers
  const handleConfirmDelete = async () => {
    if (!deletingVideo) return;
    try {
      setDeleting(true);
      await api.deleteVideo(deletingVideo.id);
      setDeletingVideo(null);
      fetchVideos();
    } catch (err) {
      alert('Failed to delete video: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b-2 border-[var(--adm-text)] pb-4">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider text-[var(--adm-text)]">
            Manage Video Catalog
          </h1>
          <p className="text-xs text-[var(--adm-muted)] mt-1">
            Browse, search, edit metadata, publish, archive, or remove videos
          </p>
        </div>
        <button
          onClick={() => onNavigate('upload')}
          className="button-primary"
        >
          <VideoIcon className="w-4 h-4" /> Upload New Video
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="admin-panel p-3 mb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        {/* Status Filter Tabs */}
        <div className="source-filter-bar mb-0">
          {[
            { label: 'All', value: '' },
            { label: 'Draft', value: 'draft' },
            { label: 'Published', value: 'published' },
            { label: 'Archived', value: 'archived' },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setStatusFilter(tab.value)}
              className={`filter-btn ${statusFilter === tab.value ? 'active' : ''}`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[var(--adm-muted)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title..."
              className="modern-input pl-8 py-1.5 text-xs w-52 sm:w-64"
            />
          </div>
          <button
            type="submit"
            className="action-btn-pro"
          >
            Search
          </button>
          <button
            type="button"
            onClick={fetchVideos}
            title="Refresh videos"
            className="action-btn-pro"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="legal-warning error flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span><strong>Catalog Error:</strong> {error}</span>
          </div>
          <button
            onClick={fetchVideos}
            className="action-btn-pro text-[10px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* Videos Table */}
      <div className="admin-panel p-0 overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-[var(--adm-muted)] flex items-center justify-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-[var(--adm-p)]" />
            <span className="text-xs font-bold uppercase tracking-wider">Loading video items...</span>
          </div>
        ) : videos.length === 0 ? (
          <div className="p-12 text-center text-[var(--adm-muted)]">
            <VideoIcon className="w-10 h-10 mx-auto mb-3 opacity-40 text-[var(--adm-text)]" />
            <p className="text-sm font-black uppercase text-[var(--adm-text)]">No videos found</p>
            <p className="text-xs text-[var(--adm-muted)] mt-1">
              {search || statusFilter
                ? 'Try clearing your search query or switching status filters.'
                : 'Upload your first video to begin building the Telegram catalog.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-[var(--adm-bg)] text-[var(--adm-text)] uppercase font-black tracking-wider border-b-2 border-[var(--adm-text)]">
                <tr>
                  <th className="px-4 py-3">Video Title & Details</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Categories</th>
                  <th className="px-4 py-3">Duration & Size</th>
                  <th className="px-4 py-3">Date Added</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--adm-border-m)]">
                {videos.map((video) => (
                  <tr key={video.id} className="hover:bg-[var(--adm-bg)] transition">
                    <td className="px-4 py-3 max-w-sm">
                      <div className="font-bold text-[var(--adm-text)] truncate">{video.title}</div>
                      {video.description && (
                        <p className="text-[11px] text-[var(--adm-muted)] line-clamp-1 mt-0.5">
                          {video.description}
                        </p>
                      )}
                      <div className="text-[10px] font-mono text-[var(--adm-muted)] truncate mt-0.5">
                        TG ID: {video.telegram_file_id || 'Pending'}
                      </div>
                    </td>

                    <td className="px-4 py-3">
                      <span
                        className={`badge-pro ${
                          video.status === 'published'
                            ? 'active'
                            : video.status === 'archived'
                            ? 'muted'
                            : ''
                        }`}
                        style={video.status === 'draft' ? { borderColor: '#f59e0b', color: '#b45309', background: 'var(--adm-bg)' } : {}}
                      >
                        {video.status}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-xs max-w-xs">
                      {video.categories && video.categories.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {video.categories.map((c) => (
                            <span
                              key={c.id}
                              className="px-1.5 py-0.5 bg-[var(--adm-bg)] text-[var(--adm-text)] border border-[var(--adm-border-m)] text-[10px] font-bold"
                            >
                              {c.name}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-[var(--adm-muted)] italic">None</span>
                      )}
                    </td>

                    <td className="px-4 py-3 text-xs font-mono text-[var(--adm-text)]">
                      <div>{formatDuration(video.duration)}</div>
                      <div className="text-[10px] text-[var(--adm-muted)]">{formatBytes(video.file_size)}</div>
                    </td>

                    <td className="px-4 py-3 text-[11px] text-[var(--adm-muted)]">
                      {new Date(video.created_at).toLocaleDateString()}
                    </td>

                    <td className="px-4 py-3 text-right">
                      <div className="inline-flex items-center justify-end gap-1.5">
                        {/* Publish / Unpublish Toggle */}
                        {video.status !== 'published' ? (
                          <button
                            onClick={() => handlePublish(video.id)}
                            title="Publish to public Telegram bot"
                            className="action-btn-pro"
                          >
                            <Globe className="w-3.5 h-3.5 text-emerald-600" />
                          </button>
                        ) : (
                          <button
                            onClick={() => handleUnpublish(video.id)}
                            title="Unpublish (revert to draft)"
                            className="action-btn-pro"
                          >
                            <EyeOff className="w-3.5 h-3.5 text-amber-500" />
                          </button>
                        )}

                        {/* Archive */}
                        {video.status !== 'archived' && (
                          <button
                            onClick={() => handleArchive(video.id)}
                            title="Archive video"
                            className="action-btn-pro"
                          >
                            <Archive className="w-3.5 h-3.5" />
                          </button>
                        )}

                        {/* Edit */}
                        <button
                          onClick={() => openEditModal(video)}
                          title="Edit metadata & categories"
                          className="action-btn-pro"
                        >
                          <Edit2 className="w-3.5 h-3.5 text-[var(--adm-p)]" />
                        </button>

                        {/* Delete */}
                        <button
                          onClick={() => setDeletingVideo(video)}
                          title="Delete video record"
                          className="action-btn-pro delete"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Video Modal */}
      {editingVideo && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-content max-w-lg">
            <div className="admin-modal-header flex items-center justify-between border-b-2 border-[var(--adm-text)] pb-3">
              <h3 className="m-0">Edit Video Metadata</h3>
              <button
                onClick={() => setEditingVideo(null)}
                className="text-[var(--adm-text)] hover:opacity-70 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-4 pt-3">
              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                  Title
                </label>
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="modern-input"
                />
              </div>

              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="modern-textarea"
                />
              </div>

              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                  Categories
                </label>
                <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto p-2 bg-[var(--adm-bg)] border border-[var(--adm-border-m)]">
                  {categories.map((cat) => {
                    const isChecked = editCategoryIds.includes(cat.id);
                    return (
                      <button
                        type="button"
                        key={cat.id}
                        onClick={() => toggleEditCategory(cat.id)}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-black uppercase tracking-wider border transition ${
                          isChecked
                            ? 'bg-[var(--adm-p)] text-white border-[var(--adm-text)]'
                            : 'bg-[var(--adm-card)] text-[var(--adm-text)] border-[var(--adm-border-m)]'
                        }`}
                      >
                        <Tag className="w-3 h-3" />
                        {cat.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="admin-modal-footer pt-3 border-t-2 border-[var(--adm-text)]">
                <button
                  type="button"
                  onClick={() => setEditingVideo(null)}
                  className="action-btn-pro"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="button-primary"
                >
                  {savingEdit && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingVideo && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-content max-w-md">
            <div className="admin-modal-header flex items-center justify-between border-b-2 border-[var(--adm-text)] pb-3">
              <h3 className="m-0 text-red-600">Delete Video Record</h3>
              <button
                onClick={() => setDeletingVideo(null)}
                className="text-[var(--adm-text)] hover:opacity-70 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="admin-modal-body py-4">
              <p>
                Are you sure you want to delete <strong className="text-[var(--adm-text)] font-black">{deletingVideo.title}</strong>?
              </p>
              <div className="legal-warning error mt-3 mb-0">
                <p>
                  <strong>Notice:</strong> This action permanently deletes the video metadata and association records from PostgreSQL. Video binaries stored on Telegram remain intact.
                </p>
              </div>
            </div>

            <div className="admin-modal-footer border-t-2 border-[var(--adm-text)] pt-3">
              <button
                type="button"
                onClick={() => setDeletingVideo(null)}
                className="action-btn-pro"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                disabled={deleting}
                className="action-btn-pro delete font-black"
              >
                {deleting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
