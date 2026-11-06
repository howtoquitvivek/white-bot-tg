/**
 * API client for the Telegram Video Platform Admin Backend.
 */

const API_BASE = '/api';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'An error occurred';
    try {
      const data = await response.json();
      errorDetail = data.detail || data.message || JSON.stringify(data);
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail || `HTTP error ${response.status}`);
  }
  return response.json();
}

export const api = {
  // Health
  async checkHealth() {
    return handleResponse(await fetch(`${API_BASE}/health`));
  },

  // Dashboard Stats
  async getDashboardStats() {
    return handleResponse(await fetch(`${API_BASE}/dashboard/stats`));
  },

  // Videos
  async getVideos({ search = '', status = '', category_id = '', limit = 50, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    if (category_id) params.append('category_id', category_id);
    params.append('limit', limit);
    params.append('offset', offset);
    return handleResponse(await fetch(`${API_BASE}/videos?${params.toString()}`));
  },

  async getVideo(id) {
    return handleResponse(await fetch(`${API_BASE}/videos/${id}`));
  },

  async updateVideo(id, { title, description, category_ids }) {
    return handleResponse(
      await fetch(`${API_BASE}/videos/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, category_ids }),
      })
    );
  },

  async publishVideo(id) {
    return handleResponse(
      await fetch(`${API_BASE}/videos/${id}/publish`, {
        method: 'POST',
      })
    );
  },

  async unpublishVideo(id) {
    return handleResponse(
      await fetch(`${API_BASE}/videos/${id}/unpublish`, {
        method: 'POST',
      })
    );
  },

  async archiveVideo(id) {
    return handleResponse(
      await fetch(`${API_BASE}/videos/${id}/archive`, {
        method: 'POST',
      })
    );
  },

  async deleteVideo(id) {
    return handleResponse(
      await fetch(`${API_BASE}/videos/${id}`, {
        method: 'DELETE',
      })
    );
  },

  // Categories
  async getCategories() {
    return handleResponse(await fetch(`${API_BASE}/categories`));
  },

  async createCategory({ name, slug, description }) {
    return handleResponse(
      await fetch(`${API_BASE}/categories`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, slug, description }),
      })
    );
  },

  async updateCategory(id, { name, slug, description }) {
    return handleResponse(
      await fetch(`${API_BASE}/categories/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, slug, description }),
      })
    );
  },

  async deleteCategory(id) {
    return handleResponse(
      await fetch(`${API_BASE}/categories/${id}`, {
        method: 'DELETE',
      })
    );
  },

  // Collections
  async getCollections({ status = '', limit = 50, offset = 0 } = {}) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit);
    params.append('offset', offset);
    return handleResponse(await fetch(`${API_BASE}/collections?${params.toString()}`));
  },

  async getCollection(id) {
    return handleResponse(await fetch(`${API_BASE}/collections/${id}`));
  },

  async createCollection({ title, description, status = 'draft', cover_video_id, video_ids }) {
    return handleResponse(
      await fetch(`${API_BASE}/collections`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, status, cover_video_id, video_ids }),
      })
    );
  },

  async updateCollection(id, { title, description, status, cover_video_id, video_ids }) {
    return handleResponse(
      await fetch(`${API_BASE}/collections/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, description, status, cover_video_id, video_ids }),
      })
    );
  },

  async deleteCollection(id) {
    return handleResponse(
      await fetch(`${API_BASE}/collections/${id}`, {
        method: 'DELETE',
      })
    );
  },

  // Upload with progress tracking via XMLHttpRequest
  uploadVideo(formData, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${API_BASE}/uploads`);

      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percent = Math.round((event.loaded / event.total) * 100);
            onProgress(percent);
          }
        };
      }

      xhr.onload = () => {
        try {
          const json = JSON.parse(xhr.responseText);
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(json);
          } else {
            reject(new Error(json.detail || json.message || `Upload failed (${xhr.status})`));
          }
        } catch {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve({ success: true });
          } else {
            reject(new Error(xhr.responseText || `Upload failed with status ${xhr.status}`));
          }
        }
      };

      xhr.onerror = () => {
        reject(new Error('Network error during file upload. Please check server connection.'));
      };

      xhr.send(formData);
    });
  },
};

