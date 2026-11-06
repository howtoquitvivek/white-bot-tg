import React, { useEffect, useRef, useState } from 'react';
import {
  Upload,
  FileVideo,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Send,
  Globe,
  Tag,
  X,
  ArrowRight,
} from 'lucide-react';
import { api } from '../api';

function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export function UploadVideo({ onNavigate }) {
  const [file, setFile] = useState(null);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [categories, setCategories] = useState([]);
  const [selectedCategoryIds, setSelectedCategoryIds] = useState([]);
  const [channelOverride, setChannelOverride] = useState('');

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [successData, setSuccessData] = useState(null);
  const [isPublished, setIsPublished] = useState(false);
  const [publishing, setPublishing] = useState(false);

  const fileInputRef = useRef(null);

  useEffect(() => {
    api.getCategories()
      .then((data) => setCategories(data.items || []))
      .catch((err) => console.error('Failed to load categories:', err));
  }, []);

  const handleFileChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      if (!title) {
        const baseName = selected.name.replace(/\.[^/.]+$/, '');
        setTitle(baseName);
      }
      setError(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      setFile(dropped);
      if (!title) {
        const baseName = dropped.name.replace(/\.[^/.]+$/, '');
        setTitle(baseName);
      }
      setError(null);
    }
  };

  const toggleCategory = (catId) => {
    setSelectedCategoryIds((prev) =>
      prev.includes(catId) ? prev.filter((id) => id !== catId) : [...prev, catId]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a video file to upload.');
      return;
    }
    if (!title.trim()) {
      setError('Please enter a video title.');
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      setError(null);
      setSuccessData(null);
      setIsPublished(false);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', title.trim());
      if (description.trim()) {
        formData.append('description', description.trim());
      }
      if (selectedCategoryIds.length > 0) {
        formData.append('category_ids', selectedCategoryIds.join(','));
      }
      if (channelOverride.trim()) {
        formData.append('channel_id', channelOverride.trim());
      }

      const response = await api.uploadVideo(formData, (progress) => {
        setUploadProgress(progress);
      });

      setSuccessData(response);
    } catch (err) {
      setError(err.message || 'Failed to upload video to Telegram.');
    } finally {
      setUploading(false);
    }
  };

  const handlePublishNow = async () => {
    if (!successData?.video?.id) return;
    try {
      setPublishing(true);
      await api.publishVideo(successData.video.id);
      setIsPublished(true);
    } catch (err) {
      setError('Failed to publish video: ' + err.message);
    } finally {
      setPublishing(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setTitle('');
    setDescription('');
    setSelectedCategoryIds([]);
    setChannelOverride('');
    setError(null);
    setSuccessData(null);
    setIsPublished(false);
    setUploadProgress(0);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="border-b-2 border-[var(--adm-text)] pb-4">
        <h1 className="text-xl font-black uppercase tracking-wider text-[var(--adm-text)]">
          Upload Video to Storage
        </h1>
        <p className="text-xs text-[var(--adm-muted)] mt-1">
          Direct stream from your browser to private Telegram storage channel with PostgreSQL cataloging
        </p>
      </div>

      {/* Success View */}
      {successData && (
        <div className="admin-panel border-2 border-emerald-600 space-y-5" style={{ boxShadow: '6px 6px 0px #059669' }}>
          <div className="flex items-start gap-3">
            <div className="p-2 bg-emerald-500 text-white border border-[var(--adm-text)] shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-black uppercase tracking-wider text-[var(--adm-text)]">
                Upload Completed Successfully!
              </h3>
              <p className="text-xs text-[var(--adm-muted)] mt-1">
                The video has been streamed to Telegram storage and saved as a{' '}
                <strong className="text-[var(--adm-text)] uppercase">{isPublished ? 'Published' : 'Draft'}</strong> catalog item.
              </p>
            </div>
          </div>

          {/* Video Metadata Box */}
          <div className="bg-[var(--adm-bg)] border border-[var(--adm-border-m)] p-4 space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-[var(--adm-border-m)]">
              <span className="font-bold text-[var(--adm-muted)] uppercase">Title:</span>
              <span className="font-bold text-[var(--adm-text)]">{successData.video?.title}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[var(--adm-border-m)]">
              <span className="font-bold text-[var(--adm-muted)] uppercase">Status:</span>
              <span
                className={`font-black uppercase tracking-wider ${
                  isPublished ? 'text-emerald-600' : 'text-amber-500'
                }`}
              >
                {isPublished ? 'Published' : 'Draft'}
              </span>
            </div>
            <div className="flex justify-between py-1 border-b border-[var(--adm-border-m)]">
              <span className="font-bold text-[var(--adm-muted)] uppercase">Telegram File ID:</span>
              <span className="font-mono text-[var(--adm-text)] max-w-xs truncate">
                {successData.video?.telegram_file_id || 'N/A'}
              </span>
            </div>
            <div className="flex justify-between py-1">
              <span className="font-bold text-[var(--adm-muted)] uppercase">Size:</span>
              <span className="font-mono text-[var(--adm-text)]">
                {formatBytes(successData.video?.file_size)}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            {!isPublished ? (
              <button
                onClick={handlePublishNow}
                disabled={publishing}
                className="button-primary"
              >
                {publishing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Globe className="w-4 h-4" />
                )}
                Publish Video Now
              </button>
            ) : (
              <span className="badge-pro active">
                ✓ Live in Telegram Bot
              </span>
            )}

            <button
              onClick={handleReset}
              className="action-btn-pro"
            >
              <Upload className="w-4 h-4" /> Upload Another
            </button>

            <button
              onClick={() => onNavigate('videos')}
              className="action-btn-pro"
            >
              Manage Videos <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </button>
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="legal-warning error flex items-start justify-between">
          <div className="flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <div>
              <p><strong>Upload Error:</strong> {error}</p>
            </div>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-[var(--adm-text)] hover:opacity-70 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload Form */}
      {!successData && (
        <form onSubmit={handleSubmit} className="admin-panel space-y-6">
          {/* File Drag-and-Drop Area */}
          <div>
            <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-2">
              Video File <span className="text-red-500">*</span>
            </label>
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed p-8 text-center cursor-pointer transition ${
                file
                  ? 'border-[var(--adm-p)] bg-[var(--adm-bg)] shadow-[4px_4px_0px_var(--adm-p)]'
                  : 'border-[var(--adm-text)] bg-[var(--adm-bg)] hover:border-[var(--adm-p)]'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="video/mp4,video/quicktime,video/x-matroska,video/webm,.mp4,.mov,.mkv,.webm,.avi"
                onChange={handleFileChange}
                className="hidden"
              />

              {file ? (
                <div className="flex items-center justify-center gap-4">
                  <div className="p-3 bg-[var(--adm-p)] text-white border border-[var(--adm-text)]">
                    <FileVideo className="w-8 h-8" />
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-black text-[var(--adm-text)] truncate max-w-md">
                      {file.name}
                    </p>
                    <p className="text-xs text-[var(--adm-muted)] mt-0.5 font-mono">
                      {formatBytes(file.size)} • Click or drop new file to replace
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-12 h-12 mx-auto bg-[var(--adm-card)] text-[var(--adm-text)] border border-[var(--adm-text)] flex items-center justify-center shadow-[3px_3px_0px_var(--adm-text)]">
                    <Upload className="w-6 h-6" />
                  </div>
                  <p className="text-xs font-black uppercase tracking-wider text-[var(--adm-text)]">
                    Click to browse or drag and drop video
                  </p>
                  <p className="text-[11px] text-[var(--adm-muted)]">
                    MP4, MOV, MKV, WebM up to 50 MB (Telegram Bot API limit)
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1.5">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Action Scene Part 1"
              className="modern-input"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1.5">
              Description (Optional)
            </label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide a brief synopsis or details about the video..."
              className="modern-textarea"
            />
          </div>

          {/* Categories Selector */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-black uppercase tracking-wider text-[var(--adm-muted)]">
                Categories
              </label>
              <button
                type="button"
                onClick={() => onNavigate('categories')}
                className="text-xs font-bold text-[var(--adm-p)] hover:underline uppercase tracking-wider"
              >
                + Manage Categories
              </button>
            </div>

            {categories.length === 0 ? (
              <p className="text-xs text-[var(--adm-muted)] italic bg-[var(--adm-bg)] p-3 border border-[var(--adm-border-m)]">
                No categories created yet. You can create categories in the Categories tab.
              </p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {categories.map((cat) => {
                  const selected = selectedCategoryIds.includes(cat.id);
                  return (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => toggleCategory(cat.id)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-black uppercase tracking-wider transition border ${
                        selected
                          ? 'bg-[var(--adm-p)] text-white border-[var(--adm-text)] shadow-[2px_2px_0px_var(--adm-text)]'
                          : 'bg-[var(--adm-bg)] text-[var(--adm-text)] border-[var(--adm-border-m)] hover:border-[var(--adm-text)]'
                      }`}
                    >
                      <Tag className="w-3 h-3" />
                      {cat.name}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Advanced / Optional Storage Channel Override */}
          <div className="pt-2 border-t border-[var(--adm-border-m)]">
            <details className="group">
              <summary className="text-xs font-bold text-[var(--adm-muted)] hover:text-[var(--adm-text)] cursor-pointer select-none uppercase tracking-wider">
                ▸ Advanced: Telegram Storage Channel Override
              </summary>
              <div className="mt-3 p-4 bg-[var(--adm-bg)] border border-[var(--adm-border-m)] space-y-2">
                <label className="block text-xs font-bold text-[var(--adm-muted)] uppercase">
                  Target Channel ID (Optional override):
                </label>
                <input
                  type="text"
                  value={channelOverride}
                  onChange={(e) => setChannelOverride(e.target.value)}
                  placeholder="e.g. -1001234567890 or @my_channel"
                  className="modern-input font-mono text-xs"
                />
                <p className="text-[11px] text-[var(--adm-muted)]">
                  By default, the server uses <code className="bg-[var(--adm-card)] px-1 border border-[var(--adm-border-m)]">TELEGRAM_STORAGE_CHANNEL_ID</code> from backend config.
                </p>
              </div>
            </details>
          </div>

          {/* Upload Progress Bar */}
          {uploading && (
            <div className="space-y-2 p-4 bg-[var(--adm-bg)] border-2 border-[var(--adm-p)] shadow-[4px_4px_0px_var(--adm-p-l)]">
              <div className="flex justify-between text-xs text-[var(--adm-text)] font-black uppercase tracking-wider">
                <span className="flex items-center gap-2">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-[var(--adm-p)]" />
                  Streaming to Telegram Storage Channel...
                </span>
                <span className="font-mono">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-[var(--adm-card)] border border-[var(--adm-text)] h-3 overflow-hidden">
                <div
                  className="bg-[var(--adm-p)] h-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={uploading || !file}
            className="button-primary w-100"
          >
            {uploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Uploading Video...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Upload to Telegram Storage
              </>
            )}
          </button>
        </form>
      )}
    </div>
  );
}
