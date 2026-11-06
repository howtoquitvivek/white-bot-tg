import React, { useState, useEffect } from 'react';
import { Users, UserPlus, Trash2, Shield, ShieldAlert, RefreshCw, CheckCircle2 } from 'lucide-react';
import { getSettings, addAdminEmail, removeAdminEmail } from '../services/settingsService';

export function AdminUsers({ isSuperAdmin, currentUser }) {
  const [adminList, setAdminList] = useState([]);
  const [superAdmins, setSuperAdmins] = useState([]);
  const [newAdminEmail, setNewAdminEmail] = useState('');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState(null);

  const fetchAdmins = async () => {
    try {
      setLoading(true);
      const settings = await getSettings();
      setAdminList(settings.adminEmails || []);
      setSuperAdmins(settings.superAdminEmails || []);
    } catch (err) {
      console.error('Failed to load admin settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    const cleanEmail = newAdminEmail.trim().toLowerCase();
    if (!cleanEmail) return;

    if (adminList.includes(cleanEmail) || superAdmins.includes(cleanEmail)) {
      alert('This email is already an authorized administrator.');
      return;
    }

    try {
      setProcessing(true);
      await addAdminEmail(cleanEmail);
      setNewAdminEmail('');
      setMessage(`Successfully added ${cleanEmail} to authorized admins.`);
      await fetchAdmins();
      setTimeout(() => setMessage(null), 4000);
    } catch (err) {
      alert('Failed to add admin: ' + err.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleRemove = async (email) => {
    if (superAdmins.some((sa) => sa.toLowerCase() === email.toLowerCase())) {
      alert('Cannot remove a Superadmin through this dashboard.');
      return;
    }

    if (!confirm(`Are you sure you want to remove ${email} from authorized administrators?`)) {
      return;
    }

    try {
      setProcessing(true);
      await removeAdminEmail(email);
      setMessage(`Removed ${email} from administrators.`);
      await fetchAdmins();
      setTimeout(() => setMessage(null), 4000);
    } catch (err) {
      alert('Failed to remove admin: ' + err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between border-b-2 border-[var(--adm-text)] pb-4">
        <div>
          <h1 className="text-xl font-black uppercase tracking-wider flex items-center gap-2">
            <Users className="w-5 h-5 text-[var(--adm-p)]" /> Administrator Access Control
          </h1>
          <p className="text-xs text-[var(--adm-muted)] mt-1">
            Manage authorized Google Accounts permitted to access this administrative portal via Firestore
          </p>
        </div>
        <button
          onClick={fetchAdmins}
          disabled={loading}
          className="action-btn-pro"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {message && (
        <div className="p-3 bg-emerald-50 border border-emerald-600 text-emerald-900 text-xs font-semibold flex items-center gap-2 shadow-[3px_3px_0px_#0d0d0d]">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {/* Add Admin Form */}
      {isSuperAdmin && (
        <div className="admin-panel glass-card">
          <h2 className="section-title">
            <UserPlus className="w-4 h-4" /> Grant New Administrator Access
          </h2>
          <form onSubmit={handleAdd} className="flex flex-col sm:flex-row gap-3">
            <input
              type="email"
              required
              value={newAdminEmail}
              onChange={(e) => setNewAdminEmail(e.target.value)}
              placeholder="admin@example.com (Google Account email)"
              className="modern-input flex-1"
            />
            <button
              type="submit"
              disabled={processing || !newAdminEmail.trim()}
              className="button-primary shrink-0"
            >
              {processing ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Adding...
                </>
              ) : (
                <>
                  <UserPlus className="w-3.5 h-3.5" /> Authorize Admin
                </>
              )}
            </button>
          </form>
          <p className="text-[11px] text-[var(--adm-muted)] mt-2">
            ℹ️ The user will be able to log in with their Google account popup if their email matches this list.
          </p>
        </div>
      )}

      {/* SuperAdmins Section */}
      <div className="space-y-3">
        <h3 className="text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] flex items-center gap-2">
          <Shield className="w-4 h-4 text-[var(--adm-p)]" /> Primary SuperAdmins ({superAdmins.length})
        </h3>
        <div className="user-grid">
          {superAdmins.map((email) => (
            <div key={email} className="user-pro-card super">
              <div className="user-info">
                <strong>{email}</strong>
                <span className="pro-badge">PRIMARY SUPERADMIN</span>
              </div>
              <Shield className="w-4 h-4 text-[var(--adm-p)]" />
            </div>
          ))}
        </div>
      </div>

      {/* Authorized Admins Section */}
      <div className="space-y-3">
        <h3 className="text-xs font-black uppercase tracking-wider text-[var(--adm-muted)] flex items-center gap-2">
          <Users className="w-4 h-4 text-[var(--adm-text)]" /> Authorized Administrators ({adminList.length})
        </h3>
        {adminList.length === 0 ? (
          <div className="p-6 text-center bg-[var(--adm-card)] border border-[var(--adm-border-m)] text-xs text-[var(--adm-muted)]">
            No secondary administrators configured yet. Only SuperAdmins currently have access.
          </div>
        ) : (
          <div className="user-grid">
            {adminList.map((email) => (
              <div key={email} className="user-pro-card">
                <div className="user-info">
                  <strong>{email}</strong>
                  <span className="text-[10px] text-[var(--adm-muted)] font-semibold">ADMINISTRATOR</span>
                </div>
                {isSuperAdmin && (
                  <button
                    onClick={() => handleRemove(email)}
                    disabled={processing}
                    className="action-btn-pro delete"
                    title="Revoke admin access"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Security Note */}
      <div className="legal-warning">
        <div className="flex items-center gap-2 text-red-600 font-black text-xs uppercase mb-1">
          <ShieldAlert className="w-4 h-4" /> Security Notice
        </div>
        <p className="text-xs text-[var(--adm-muted)] leading-relaxed">
          Access control is enforced via Firestore security document <code>settings/site</code>.
          Users signing in with Google whose email does not appear in either list are blocked with an
          access-denied gatekeeper screen.
        </p>
      </div>
    </div>
  );
}

