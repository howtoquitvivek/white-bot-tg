import React, { useEffect, useState } from 'react';
import {
  FolderKanban,
  Plus,
  Edit2,
  Trash2,
  RefreshCw,
  AlertCircle,
  X,
  Film,
  Globe,
  Clock,
  Layers,
} from 'lucide-react';
import { api } from '../api';

function formatDuration(seconds) {
  if (!seconds) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function Collections() {
  const [collections, setCollections] = useState([]);
  const [catalogVideos, setCatalogVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // New Collection Form
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('draft');
  const [creating, setCreating] = useState(false);

  // Edit / Manage Modal
  const [editingCollection, setEditingCollection] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editStatus, setEditStatus] = useState('draft');
  const [editVideoIds, setEditVideoIds] = useState([]);
  const [selectedVideoToAdd, setSelectedVideoToAdd] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Delete Modal
  const [deletingCollection, setDeletingCollection] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchCollections = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCollections({ limit: 100 });
      setCollections(data.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load collections.');
    } finally {
      setLoading(false);
    }
  };

  const fetchCatalogVideos = async () => {
    try {
      const data = await api.getVideos({ limit: 100 });
      setCatalogVideos(data.items || []);
    } catch (err) {
      console.error('Failed to load catalog videos for collection picker:', err);
    }
  };

  useEffect(() => {
    fetchCollections();
    fetchCatalogVideos();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    try {
      setCreating(true);
      await api.createCollection({
        title: title.trim(),
        description: description.trim() || undefined,
        status,
      });
      setTitle('');
      setDescription('');
      setStatus('draft');
      fetchCollections();
    } catch (err) {
      alert('Failed to create collection: ' + err.message);
    } finally {
      setCreating(false);
    }
  };

  const openEditModal = async (col) => {
    try {
      const fresh = await api.getCollection(col.id);
      setEditingCollection(fresh);
      setEditTitle(fresh.title);
      setEditDescription(fresh.description || '');
      setEditStatus(fresh.status || 'draft');
      setEditVideoIds((fresh.videos || []).map((v) => v.id));
      setSelectedVideoToAdd('');
    } catch {
      setEditingCollection(col);
      setEditTitle(col.title);
      setEditDescription(col.description || '');
      setEditStatus(col.status || 'draft');
      setEditVideoIds((col.videos || []).map((v) => v.id));
      setSelectedVideoToAdd('');
    }
  };

  const handleAddVideoToCollection = () => {
    if (!selectedVideoToAdd) return;
    if (editVideoIds.includes(selectedVideoToAdd)) return;

    setEditVideoIds([...editVideoIds, selectedVideoToAdd]);
    setSelectedVideoToAdd('');
  };

  const handleRemoveVideoFromCollection = (videoIdToRemove) => {
    setEditVideoIds(editVideoIds.filter((id) => id !== videoIdToRemove));
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editingCollection) return;
    try {
      setSavingEdit(true);
      await api.updateCollection(editingCollection.id, {
        title: editTitle.trim(),
        description: editDescription.trim() || undefined,
        status: editStatus,
        video_ids: editVideoIds,
      });
      setEditingCollection(null);
      fetchCollections();
    } catch (err) {
      alert('Failed to update collection: ' + err.message);
    } finally {
      setSavingEdit(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingCollection) return;
    try {
      setDeleting(true);
      await api.deleteCollection(deletingCollection.id);
      setDeletingCollection(null);
      fetchCollections();
    } catch (err) {
      alert('Failed to delete collection: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  const getVideoDetails = (vidId) => {
    if (editingCollection && editingCollection.videos) {
      const match = editingCollection.videos.find((v) => v.id === vidId);
      if (match) return match;
    }
    return catalogVideos.find((v) => v.id === vidId);
  };

  const availableVideosToAdd = catalogVideos.filter(
    (v) => !editVideoIds.includes(v.id)
  );

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b-2 border-[var(--adm-text)] pb-4">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider text-[var(--adm-text)] flex items-center gap-2">
            <FolderKanban className="w-5 h-5 text-[var(--adm-p)]" /> Curated Collections
          </h1>
          <p className="text-xs text-[var(--adm-muted)] mt-1">
            Curate themed series and playlists for category-free discovery in the Telegram bot
          </p>
        </div>
        <button
          onClick={() => {
            fetchCollections();
            fetchCatalogVideos();
          }}
          title="Refresh collections"
          className="action-btn-pro"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Create Collection Panel */}
      <div className="admin-panel">
        <h2 className="text-xs font-black uppercase tracking-wider text-[var(--adm-text)] mb-3 flex items-center gap-2">
          <Plus className="w-4 h-4 text-[var(--adm-p)]" /> Create New Collection
        </h2>

        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Summer Highlights, Season 1, Best of 2026"
                className="modern-input"
              />
            </div>

            <div>
              <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="modern-select"
              >
                <option value="draft">Draft (Admin only)</option>
                <option value="published">Published (Visible in bot)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
              Description (Optional)
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief summary of collection theme and contents"
              className="modern-input"
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={creating || !title.trim()}
              className="button-primary"
            >
              {creating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Creating...
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" /> Create Collection
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Collections List Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-black uppercase tracking-wider text-[var(--adm-text)] flex items-center gap-2">
            <Layers className="w-4 h-4 text-[var(--adm-muted)]" /> Existing Collections ({collections.length})
          </h2>
        </div>

        {error && (
          <div className="legal-warning error flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span><strong>Collection Error:</strong> {error}</span>
            </div>
            <button
              onClick={fetchCollections}
              className="action-btn-pro text-[10px]"
            >
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="admin-panel p-12 text-center text-[var(--adm-muted)] flex items-center justify-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-[var(--adm-p)]" />
            <span className="text-xs font-bold uppercase tracking-wider">Loading collections...</span>
          </div>
        ) : collections.length === 0 ? (
          <div className="admin-panel p-12 text-center text-[var(--adm-muted)]">
            <FolderKanban className="w-10 h-10 mx-auto mb-3 opacity-40 text-[var(--adm-text)]" />
            <h3 className="text-sm font-black uppercase text-[var(--adm-text)]">No collections yet</h3>
            <p className="text-xs text-[var(--adm-muted)] mt-1">
              Create your first collection above to organize videos into series or playlists.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {collections.map((col) => {
              const totalVids = col.videos ? col.videos.length : 0;
              const pubVids = col.videos
                ? col.videos.filter((v) => v.status === 'published').length
                : 0;

              return (
                <div
                  key={col.id}
                  className="admin-panel p-4 mb-0 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-sm font-black uppercase tracking-wider text-[var(--adm-text)]">
                          {col.title}
                        </h3>
                        {col.description && (
                          <p className="text-xs text-[var(--adm-muted)] mt-1 line-clamp-2">
                            {col.description}
                          </p>
                        )}
                      </div>

                      {/* Status Badge */}
                      <span
                        className={`badge-pro shrink-0 ${
                          col.status === 'published' ? 'active' : 'muted'
                        }`}
                        style={col.status === 'draft' ? { borderColor: '#f59e0b', color: '#b45309' } : {}}
                      >
                        {col.status}
                      </span>
                    </div>

                    {/* Stats Pill */}
                    <div className="flex items-center gap-2 pt-1 text-xs">
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 bg-[var(--adm-bg)] border border-[var(--adm-border-m)] text-[11px] font-bold text-[var(--adm-text)]">
                        <Film className="w-3.5 h-3.5 text-[var(--adm-p)]" />
                        <span>{totalVids} {totalVids === 1 ? 'video' : 'videos'}</span>
                      </span>
                      {col.status === 'published' && (
                        <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider">
                          ({pubVids} visible in bot)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mt-4 pt-3 border-t border-[var(--adm-border-m)] flex items-center justify-between">
                    <span className="text-[10px] text-[var(--adm-muted)] font-mono">
                      {new Date(col.created_at).toLocaleDateString()}
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => openEditModal(col)}
                        className="action-btn-pro"
                      >
                        <Edit2 className="w-3.5 h-3.5 text-[var(--adm-p)]" /> Manage Videos
                      </button>
                      <button
                        onClick={() => setDeletingCollection(col)}
                        className="action-btn-pro delete"
                        title="Delete collection"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Edit & Manage Videos Modal */}
      {editingCollection && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-content max-w-2xl">
            <div className="admin-modal-header flex items-center justify-between border-b-2 border-[var(--adm-text)] pb-3">
              <h3 className="m-0 flex items-center gap-2">
                <FolderKanban className="w-4 h-4 text-[var(--adm-p)]" /> Manage Collection & Playlist
              </h3>
              <button
                onClick={() => setEditingCollection(null)}
                className="text-[var(--adm-text)] hover:opacity-70 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-4 pt-3">
              {/* Collection Metadata */}
              <div className="space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="sm:col-span-2">
                    <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                      Title <span className="text-red-500">*</span>
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
                      Status
                    </label>
                    <select
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value)}
                      className="modern-select"
                    >
                      <option value="draft">Draft</option>
                      <option value="published">Published</option>
                      <option value="archived">Archived</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                    Description
                  </label>
                  <textarea
                    rows={2}
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    className="modern-textarea"
                  />
                </div>
              </div>

              {/* Videos in Collection Section */}
              <div className="space-y-3 pt-3 border-t-2 border-[var(--adm-text)]">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-black uppercase tracking-wider text-[var(--adm-text)] flex items-center gap-2">
                    <Film className="w-4 h-4 text-[var(--adm-p)]" />
                    Videos in Collection ({editVideoIds.length})
                  </h4>
                  <span className="text-[10px] text-[var(--adm-muted)] uppercase tracking-wider">
                    Playback order matches list
                  </span>
                </div>

                {editVideoIds.length === 0 ? (
                  <div className="p-4 text-center text-xs text-[var(--adm-muted)] bg-[var(--adm-bg)] border border-[var(--adm-border-m)]">
                    No videos attached to this collection yet. Select from below to add.
                  </div>
                ) : (
                  <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                    {editVideoIds.map((vidId, idx) => {
                      const vid = getVideoDetails(vidId);
                      return (
                        <div
                          key={vidId}
                          className="flex items-center justify-between px-3 py-2 bg-[var(--adm-bg)] border border-[var(--adm-border-m)] text-xs"
                        >
                          <div className="flex items-center gap-2.5 truncate">
                            <span className="w-5 h-5 bg-[var(--adm-card)] text-[var(--adm-text)] border border-[var(--adm-text)] font-black flex items-center justify-center text-[10px] shrink-0">
                              {idx + 1}
                            </span>
                            <span className="font-bold text-[var(--adm-text)] truncate">
                              {vid ? vid.title : `Video ID: ${vidId.slice(0, 8)}...`}
                            </span>
                            {vid && (
                              <span
                                className={`text-[10px] px-1.5 py-0.2 border uppercase font-black ${
                                  vid.status === 'published'
                                    ? 'text-emerald-600 border-emerald-600'
                                    : 'text-amber-500 border-amber-500'
                                }`}
                              >
                                {vid.status}
                              </span>
                            )}
                            {vid && vid.duration && (
                              <span className="text-[var(--adm-muted)] text-[10px] font-mono flex items-center gap-1">
                                <Clock className="w-3 h-3" /> {formatDuration(vid.duration)}
                              </span>
                            )}
                          </div>

                          <button
                            type="button"
                            onClick={() => handleRemoveVideoFromCollection(vidId)}
                            className="action-btn-pro delete text-[10px] py-1 px-2 shrink-0"
                            title="Remove video from collection"
                          >
                            Remove
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Add Video Picker */}
                <div className="pt-2 flex items-center gap-2">
                  <select
                    value={selectedVideoToAdd}
                    onChange={(e) => setSelectedVideoToAdd(e.target.value)}
                    className="modern-select flex-1 text-xs"
                  >
                    <option value="">-- Select video from catalog to add --</option>
                    {availableVideosToAdd.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.title} ({v.status}) {v.duration ? `[${formatDuration(v.duration)}]` : ''}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleAddVideoToCollection}
                    disabled={!selectedVideoToAdd}
                    className="action-btn-pro shrink-0"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Video
                  </button>
                </div>
              </div>

              {/* Modal Buttons */}
              <div className="admin-modal-footer pt-3 border-t-2 border-[var(--adm-text)]">
                <button
                  type="button"
                  onClick={() => setEditingCollection(null)}
                  className="action-btn-pro"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit || !editTitle.trim()}
                  className="button-primary"
                >
                  {savingEdit ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Saving...
                    </>
                  ) : (
                    'Save Changes'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deletingCollection && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-content max-w-md">
            <div className="admin-modal-header flex items-center justify-between border-b-2 border-[var(--adm-text)] pb-3">
              <h3 className="m-0 text-red-600">Delete Collection</h3>
              <button
                onClick={() => setDeletingCollection(null)}
                className="text-[var(--adm-text)] hover:opacity-70 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="admin-modal-body py-4">
              <p>
                Are you sure you want to delete collection{' '}
                <strong className="text-[var(--adm-text)] font-black">"{deletingCollection.title}"</strong>?
              </p>
              <div className="legal-warning error mt-3 mb-0">
                <p>
                  <strong>Notice:</strong> Deleting a collection only removes the grouping playlist. All videos inside will remain intact in your video catalog.
                </p>
              </div>
            </div>

            <div className="admin-modal-footer border-t-2 border-[var(--adm-text)] pt-3">
              <button
                type="button"
                onClick={() => setDeletingCollection(null)}
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
