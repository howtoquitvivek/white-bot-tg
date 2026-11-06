import React from 'react';
import { Settings, Palette, Database, ShieldCheck, Wifi, WifiOff } from 'lucide-react';
import { THEME_MAP } from '../themeConfig';
import { isFirebaseConfigured } from '../firebase/config';

export function SettingsTab({ activeThemeKey, onSelectTheme, apiConnected }) {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="border-b-2 border-[var(--adm-text)] pb-4">
        <h1 className="text-xl font-black uppercase tracking-wider flex items-center gap-2">
          <Settings className="w-5 h-5 text-[var(--adm-p)]" /> System & Interface Settings
        </h1>
        <p className="text-xs text-[var(--adm-muted)] mt-1">
          Customize admin dashboard theme palette and inspect backend/cloud service integrations
        </p>
      </div>

      {/* Theme Customizer Card */}
      <div className="admin-panel glass-card">
        <h2 className="section-title">
          <Palette className="w-4 h-4" /> Dashboard Theme Palette
        </h2>
        <p className="text-xs text-[var(--adm-muted)] mb-3">
          Select a high-contrast Neo-Brutalist colorway. Selected theme is saved automatically in your browser.
        </p>

        <div className="theme-grid">
          {Object.keys(THEME_MAP).map((key) => {
            const theme = THEME_MAP[key];
            const isActive = activeThemeKey === key;

            return (
              <button
                key={key}
                type="button"
                className={`theme-swatch ${isActive ? 'active' : ''}`}
                onClick={() => onSelectTheme(key)}
              >
                {theme.isExperimental && (
                  <span className="experimental-tag-mini">BETA</span>
                )}
                <div className="swatch-colors">
                  <div className="swatch-main" style={{ background: theme.primary }} />
                  <div className="swatch-bg" style={{ background: theme.bgMain }} />
                  <div className="swatch-card" style={{ background: theme.bgCard }} />
                </div>
                <span className="theme-name">{theme.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Service Status Panel */}
      <div className="admin-panel glass-card">
        <h2 className="section-title">
          <Database className="w-4 h-4" /> Integration & Service Status
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
          {/* Firebase Authentication Status */}
          <div className="p-4 bg-[var(--adm-bg)] border border-[var(--adm-border-m)] flex items-start gap-3">
            <ShieldCheck className={`w-5 h-5 shrink-0 ${isFirebaseConfigured ? 'text-emerald-600' : 'text-amber-500'}`} />
            <div>
              <h4 className="text-xs font-black uppercase tracking-wider">Firebase Auth & Firestore</h4>
              <p className="text-xs text-[var(--adm-muted)] mt-1">
                {isFirebaseConfigured
                  ? 'Active and connected. Access verified against Firestore settings/site document.'
                  : 'Keys not configured in frontend/.env. Set VITE_FIREBASE_* variables to enable Google Popup login.'}
              </p>
            </div>
          </div>

          {/* FastAPI Backend Status */}
          <div className="p-4 bg-[var(--adm-bg)] border border-[var(--adm-border-m)] flex items-start gap-3">
            {apiConnected ? (
              <Wifi className="w-5 h-5 text-emerald-600 shrink-0" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500 shrink-0" />
            )}
            <div>
              <h4 className="text-xs font-black uppercase tracking-wider">FastAPI Backend (Port 8000)</h4>
              <p className="text-xs text-[var(--adm-muted)] mt-1">
                {apiConnected
                  ? 'Online. REST endpoints responding at /api/health.'
                  : 'Offline or unreachable. Ensure `uvicorn app.api.main:app` is running.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

