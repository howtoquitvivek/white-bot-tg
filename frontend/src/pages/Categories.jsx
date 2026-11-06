import React, { useEffect, useState } from 'react';
import {
  Tag,
  Plus,
  Edit2,
  Trash2,
  RefreshCw,
  AlertCircle,
  X,
} from 'lucide-react';
import { api } from '../api';

export function Categories() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // New Category Form
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);

  // Edit Modal
  const [editingCat, setEditingCat] = useState(null);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  // Delete Modal
  const [deletingCat, setDeletingCat] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getCategories();
      setCategories(data.items || []);
    } catch (err) {
      setError(err.message || 'Failed to load categories.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      setCreating(true);
      await api.createCategory({
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setName('');
      setDescription('');
      fetchCategories();
    } catch (err) {
      alert('Failed to create category: ' + err.message);
    } finally {
      setCreating(false);
    }
  };

  const openEditModal = (cat) => {
    setEditingCat(cat);
    setEditName(cat.name);
    setEditDescription(cat.description || '');
  };

  const handleSaveEdit = async (e) => {
    e.preventDefault();
    if (!editingCat) return;
    try {
      setSavingEdit(true);
      await api.updateCategory(editingCat.id, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
      });
      setEditingCat(null);
      fetchCategories();
    } catch (err) {
      alert('Failed to update category: ' + err.message);
    } finally {
      setSavingEdit(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingCat) return;
    try {
      setDeleting(true);
      await api.deleteCategory(deletingCat.id);
      setDeletingCat(null);
      fetchCategories();
    } catch (err) {
      alert('Failed to delete category: ' + err.message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b-2 border-[var(--adm-text)] pb-4">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider text-[var(--adm-text)]">
            Category Taxonomy
          </h1>
          <p className="text-xs text-[var(--adm-muted)] mt-1">
            Organize videos into discoverable categories for the Telegram bot interface
          </p>
        </div>
        <button
          onClick={fetchCategories}
          title="Refresh categories"
          className="action-btn-pro"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Refresh
        </button>
      </div>

      {/* Create Category Panel */}
      <div className="admin-panel">
        <h2 className="text-xs font-black uppercase tracking-wider text-[var(--adm-text)] mb-3 flex items-center gap-2">
          <Plus className="w-4 h-4 text-[var(--adm-p)]" /> Create New Category
        </h2>

        <form onSubmit={handleCreate} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Comedy, Action, Tutorials"
                className="modern-input"
              />
            </div>

            <div>
              <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                Description (Optional)
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief summary of category content"
                className="modern-input"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={creating || !name.trim()}
              className="button-primary"
            >
              {creating ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Plus className="w-3.5 h-3.5" />
              )}
              Add Category
            </button>
          </div>
        </form>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="legal-warning error flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span><strong>Category Error:</strong> {error}</span>
          </div>
          <button
            onClick={fetchCategories}
            className="action-btn-pro text-[10px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* Categories Table Panel */}
      <div className="admin-panel p-0 overflow-hidden">
        <div className="px-4 py-3 border-b-2 border-[var(--adm-text)] bg-[var(--adm-bg)] flex items-center justify-between">
          <h2 className="text-xs font-black uppercase tracking-wider text-[var(--adm-text)]">
            Existing Categories ({categories.length})
          </h2>
          <button
            onClick={fetchCategories}
            className="action-btn-pro text-[10px]"
            title="Refresh"
          >
            <RefreshCw className="w-3 h-3" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-[var(--adm-muted)] flex items-center justify-center gap-3">
            <RefreshCw className="w-5 h-5 animate-spin text-[var(--adm-p)]" />
            <span className="text-xs font-bold uppercase tracking-wider">Loading categories...</span>
          </div>
        ) : categories.length === 0 ? (
          <div className="p-12 text-center text-[var(--adm-muted)]">
            <Tag className="w-10 h-10 mx-auto mb-2 opacity-40 text-[var(--adm-text)]" />
            <p className="text-sm font-black uppercase text-[var(--adm-text)]">No categories created yet</p>
            <p className="text-xs text-[var(--adm-muted)] mt-1">Use the form above to add your first category.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-[var(--adm-bg)] text-[var(--adm-text)] uppercase font-black tracking-wider border-b-2 border-[var(--adm-text)]">
                <tr>
                  <th className="px-4 py-3">Category Name</th>
                  <th className="px-4 py-3">Slug</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--adm-border-m)]">
                {categories.map((cat) => (
                  <tr key={cat.id} className="hover:bg-[var(--adm-bg)] transition">
                    <td className="px-4 py-3 font-bold text-[var(--adm-text)] flex items-center gap-2">
                      <Tag className="w-3.5 h-3.5 text-[var(--adm-p)] shrink-0" />
                      {cat.name}
                    </td>
                    <td className="px-4 py-3 font-mono text-[var(--adm-muted)]">
                      {cat.slug}
                    </td>
                    <td className="px-4 py-3 text-[var(--adm-muted)] max-w-xs truncate">
                      {cat.description || <span className="italic opacity-50">No description</span>}
                    </td>
                    <td className="px-4 py-3 text-[var(--adm-muted)]">
                      {new Date(cat.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="inline-flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => openEditModal(cat)}
                          title="Rename/Edit"
                          className="action-btn-pro"
                        >
                          <Edit2 className="w-3.5 h-3.5 text-[var(--adm-p)]" />
                        </button>
                        <button
                          onClick={() => setDeletingCat(cat)}
                          title="Delete category"
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

      {/* Edit Category Modal */}
      {editingCat && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-content max-w-md">
            <div className="admin-modal-header flex items-center justify-between border-b-2 border-[var(--adm-text)] pb-3">
              <h3 className="m-0">Rename / Edit Category</h3>
              <button
                onClick={() => setEditingCat(null)}
                className="text-[var(--adm-text)] hover:opacity-70 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="space-y-4 pt-3">
              <div>
                <label className="block text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] mb-1">
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="modern-input"
                />
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

              <div className="admin-modal-footer pt-3 border-t-2 border-[var(--adm-text)]">
                <button
                  type="button"
                  onClick={() => setEditingCat(null)}
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
      {deletingCat && (
        <div className="admin-modal-overlay">
          <div className="admin-modal-content max-w-md">
            <div className="admin-modal-header flex items-center justify-between border-b-2 border-[var(--adm-text)] pb-3">
              <h3 className="m-0 text-red-600">Delete Category</h3>
              <button
                onClick={() => setDeletingCat(null)}
                className="text-[var(--adm-text)] hover:opacity-70 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="admin-modal-body py-4">
              <p>
                Are you sure you want to delete category <strong className="text-[var(--adm-text)] font-black">"{deletingCat.name}"</strong>?
              </p>
              <div className="legal-warning error mt-3 mb-0">
                <p>
                  <strong>Notice:</strong> Videos in this category will not be deleted; only their category tag will be removed.
                </p>
              </div>
            </div>

            <div className="admin-modal-footer border-t-2 border-[var(--adm-text)] pt-3">
              <button
                type="button"
                onClick={() => setDeletingCat(null)}
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
