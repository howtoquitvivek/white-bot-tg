import React, { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  Upload,
  Video,
  Tag,
  FolderKanban,
  Users,
  Settings,
  LogOut,
  Wifi,
  WifiOff,
  ShieldAlert,
  Shield,
  Palette,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import { api } from './api';
import { useAuth } from './hooks/useAuth';
import { THEME_MAP } from './themeConfig';
import { Dashboard } from './pages/Dashboard';
import { UploadVideo } from './pages/UploadVideo';
import { ManageVideos } from './pages/ManageVideos';
import { Categories } from './pages/Categories';
import { Collections } from './pages/Collections';
import { AdminUsers } from './pages/AdminUsers';
import { SettingsTab } from './pages/SettingsTab';
import './styles/admin.css';

function GoogleIcon() {
  return (
    <svg className="w-4 h-4 shrink-0 inline-block mr-2" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

export function App() {
  const { user, loading, isAdmin, isSuperAdmin, isConfigured, login, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [apiConnected, setApiConnected] = useState(null);
  const [themeKey, setThemeKey] = useState(localStorage.getItem('adm-theme') || 'DEFAULT');
  const [devBypass, setDevBypass] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [loggingIn, setLoggingIn] = useState(false);

  const handleLoginClick = async () => {
    try {
      setAuthError(null);
      setLoggingIn(true);
      await login();
    } catch (err) {
      console.error('Google login error:', err);
      if (err.code === 'auth/popup-closed-by-user') {
        setAuthError('Sign-in popup was closed before completing authentication.');
      } else if (err.code === 'auth/unauthorized-domain') {
        setAuthError('This domain is not authorized in Firebase Console > Authentication > Settings > Authorized Domains.');
      } else {
        setAuthError(err.message || 'Failed to authenticate with Google.');
      }
    } finally {
      setLoggingIn(false);
    }
  };

  useEffect(() => {
    // Health check on load
    api.checkHealth()
      .then(() => setApiConnected(true))
      .catch(() => setApiConnected(false));

    // Periodic check every 30 seconds
    const interval = setInterval(() => {
      api.checkHealth()
        .then(() => setApiConnected(true))
        .catch(() => setApiConnected(false));
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleThemeChange = (newKey) => {
    setThemeKey(newKey);
    localStorage.setItem('adm-theme', newKey);
  };

  // Active theme tokens
  const activeTheme = THEME_MAP[themeKey] || THEME_MAP.DEFAULT;

  // 1. Loading State
  if (loading) {
    return (
      <div className="admin-portal-login">
        <div className="gatekeeper-card text-center">
          <h2>ADMIN PORTAL</h2>
          <div className="legal-warning">
            <p><strong>AUTHENTICATION CHECK</strong></p>
            <p>Connecting to Firebase Auth and Firestore permissions...</p>
          </div>
        </div>
      </div>
    );
  }

  // 2. Firebase Not Configured in .env Notice (Local Dev Fallback)
  if (!isConfigured && !devBypass) {
    return (
      <div className="admin-portal-login">
        <div className="gatekeeper-card">
          <h2>ADMIN PORTAL</h2>
          <div className="legal-warning config-notice">
            <p><strong>FIREBASE AUTH & FIRESTORE</strong></p>
            <p>
              Google Auth and Firestore permissions are enabled. To connect your Firebase project,
              add your <code>VITE_FIREBASE_*</code> credentials to <code>frontend/.env</code>.
            </p>
          </div>
          <p className="text-xs text-slate-600 mb-4">
            See <code>frontend/.env.example</code> for the configuration keys.
          </p>
          <div className="space-y-3">
            <button
              onClick={() => setDevBypass(true)}
              className="button-primary w-100"
            >
              Enter Dashboard in Local Dev Mode <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 3. User Not Logged In (Gatekeeper Card)
  if (isConfigured && !user && !devBypass) {
    return (
      <div className="admin-portal-login">
        <div className="gatekeeper-card">
          <h2>ADMIN PORTAL</h2>
          <div className="legal-warning">
            <p><strong>RESTRICTED ACCESS</strong></p>
            <p>
              This is a private administrative system. Unauthorized access attempts are actively
              monitored, logged, and may result in legal action.
            </p>
          </div>
          <p className="text-xs text-slate-600 mb-4">
            Please log in with an authorized Google Account to manage the video platform.
          </p>

          {authError && (
            <div className="legal-warning error mb-3">
              <p><strong>LOGIN ERROR</strong></p>
              <p>{authError}</p>
            </div>
          )}

          <button
            onClick={handleLoginClick}
            disabled={loggingIn}
            className="btn-google-login"
          >
            <GoogleIcon />
            {loggingIn ? 'Connecting to Google...' : 'Login with Google'}
          </button>

          <div className="mt-4 pt-3 border-t border-slate-200 text-center">
            <button
              type="button"
              onClick={() => setDevBypass(true)}
              className="text-xs font-semibold text-slate-500 hover:text-slate-800 transition underline cursor-pointer bg-transparent border-0"
            >
              Skip / Local Dev Bypass →
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 4. User Logged In But Not In Firestore adminEmails (Access Denied)
  if (isConfigured && user && !isAdmin && !devBypass) {
    return (
      <div className="admin-portal-login">
        <div className="gatekeeper-card">
          <h2>UNAUTHORIZED</h2>
          <div className="legal-warning error">
            <p><strong>ACCESS DENIED</strong></p>
            <p>
              Your account (<strong>{user.email}</strong>) is not authorized for this administrative
              portal.
            </p>
          </div>
          <p className="text-xs text-slate-600 mb-4">
            To gain access, ensure this email is added to the <strong>adminEmails</strong> list in
            Firestore (<code>settings/site</code>).
          </p>
          <button onClick={logout} className="button-primary w-100">
            Logout
          </button>
        </div>
      </div>
    );
  }

  // 5. Authorized Dashboard View
  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onNavigate={setActiveTab} />;
      case 'upload':
        return <UploadVideo onNavigate={setActiveTab} />;
      case 'videos':
        return <ManageVideos onNavigate={setActiveTab} />;
      case 'categories':
        return <Categories />;
      case 'collections':
        return <Collections />;
      case 'users':
        return <AdminUsers isSuperAdmin={isSuperAdmin || devBypass} currentUser={user} />;
      case 'settings':
        return (
          <SettingsTab
            activeThemeKey={themeKey}
            onSelectTheme={handleThemeChange}
            apiConnected={apiConnected}
          />
        );
      default:
        return <Dashboard onNavigate={setActiveTab} />;
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'upload', label: 'Upload' },
    { id: 'videos', label: 'Videos' },
    { id: 'categories', label: 'Categories' },
    { id: 'collections', label: 'Collections' },
  ];

  if (isSuperAdmin || devBypass) {
    navItems.push({ id: 'users', label: 'Admins' });
  }

  navItems.push({ id: 'settings', label: 'Settings' });

  return (
    <div
      className="admin-dashboard-page"
      style={{
        '--adm-p': activeTheme.primary,
        '--adm-p-l': activeTheme.primaryLight,
        '--adm-bg': activeTheme.bgMain,
        '--adm-card': activeTheme.bgCard,
        '--adm-head': activeTheme.bgHeader,
        '--adm-radius': activeTheme.radius || '0px',
        '--adm-text': activeTheme.textMain,
        '--adm-muted': activeTheme.textMuted,
        '--adm-text-l': activeTheme.textLight,
        '--adm-text-h': activeTheme.textHeading,
        '--adm-border': activeTheme.borderMain,
        '--adm-border-m': activeTheme.borderMuted,
        '--adm-border-l': activeTheme.borderLight,
        '--adm-scroll': activeTheme.scrollbarTrack,
        '--adm-new-t': activeTheme.status?.newText || '#2e7d32',
        '--adm-new-bg': activeTheme.status?.newBg || '#f0f7f0',
        '--adm-del': activeTheme.status?.delete || '#cc0000',
        '--adm-del-h': activeTheme.status?.deleteHover || '#b91c1c',
        '--adm-h-tab': activeTheme.hover?.tab || '#f1f1f1',
        '--adm-h-filter': activeTheme.hover?.filter || '#f0f0f0',
        '--adm-h-light': activeTheme.hover?.bgLight || '#f1f5f9',
      }}
    >
      {/* Neo-Brutalist Master Header */}
      <header className="admin-header">
        {/* Logo Block */}
        <div className="admin-logo">
          <span className="logo-box">TG</span>
          <span className="logo-text">ADMIN</span>
        </div>

        {/* Navigation Tabs */}
        <div className="admin-nav-main">
          <nav className="admin-tabs">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`tab-btn ${isActive ? 'active' : ''}`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* User profile chip & controls */}
          <div className="admin-user-nav">
            {user ? (
              <div className="user-pill">
                {user.photoURL && (
                  <img src={user.photoURL} alt="" className="user-avatar" />
                )}
                <span className="text-xs truncate max-w-[140px]">{user.email}</span>
                <span className={`user-badge ${isSuperAdmin ? 'super' : ''}`}>
                  {isSuperAdmin ? 'SUPERADMIN' : 'ADMIN'}
                </span>
              </div>
            ) : devBypass ? (
              <div className="user-pill">
                <span className="text-xs font-mono">DEV MODE</span>
                <span className="user-badge">UNRESTRICTED</span>
              </div>
            ) : null}

            {/* API Status Badge */}
            <span
              className={`inline-flex items-center gap-1 px-2 py-1 text-[11px] font-bold border border-[var(--adm-border-m)] ${
                apiConnected ? 'text-emerald-700 bg-emerald-50' : 'text-red-700 bg-red-50'
              }`}
            >
              {apiConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
              {apiConnected ? 'API OK' : 'API DOWN'}
            </span>

            {/* Logout button */}
            {user && (
              <button onClick={logout} className="action-btn pro">
                <LogOut size={13} /> LOGOUT
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="admin-container">
        {renderContent()}
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--adm-border-m)] py-3 px-6 text-center text-xs text-[var(--adm-muted)] bg-[var(--adm-card)]">
        <span>Telegram Video Platform • Neo-Brutalist Administration Interface • Theme: <strong>{activeTheme.name}</strong></span>
      </footer>
    </div>
  );
}

export default App;
