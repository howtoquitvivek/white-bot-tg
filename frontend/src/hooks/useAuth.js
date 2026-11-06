import { useState, useEffect } from 'react';
import { loginWithGoogle, logout, subscribeToAuthChanges } from '../services/authService';
import { getSettings } from '../services/settingsService';
import { isFirebaseConfigured } from '../firebase/config';

/**
 * Custom hook to manage Firebase authentication and Firestore admin verification.
 */
export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isSuperAdmin, setIsSuperAdmin] = useState(false);

  useEffect(() => {
    if (!isFirebaseConfigured) {
      // If Firebase credentials are not yet configured in .env, mark loading false
      setLoading(false);
      return;
    }

    const unsubscribe = subscribeToAuthChanges(async (currentUser) => {
      setUser(currentUser);

      if (currentUser && currentUser.email) {
        try {
          const settings = await getSettings();
          const adminEmails = settings.adminEmails || [];
          const superAdminEmails = settings.superAdminEmails || [];
          const userEmail = currentUser.email.toLowerCase().trim();

          const isUserSuperAdmin = superAdminEmails.some(
            (email) => email.toLowerCase().trim() === userEmail
          );
          const isUserAdmin =
            isUserSuperAdmin ||
            adminEmails.some((email) => email.toLowerCase().trim() === userEmail);

          setIsAdmin(isUserAdmin);
          setIsSuperAdmin(isUserSuperAdmin);
        } catch (error) {
          console.error('Error checking admin status in Firestore:', error);
          setIsAdmin(false);
          setIsSuperAdmin(false);
        }
      } else {
        setIsAdmin(false);
        setIsSuperAdmin(false);
      }

      setLoading(false);
    });

    return () => {
      if (typeof unsubscribe === 'function') {
        unsubscribe();
      }
    };
  }, []);

  const login = async () => {
    try {
      setLoading(true);
      await loginWithGoogle();
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      setUser(null);
      setIsAdmin(false);
      setIsSuperAdmin(false);
    } catch (error) {
      console.error('Logout error:', error);
      throw error;
    }
  };

  return {
    user,
    loading,
    isAdmin,
    isSuperAdmin,
    isConfigured: isFirebaseConfigured,
    login,
    logout: handleLogout,
  };
};

