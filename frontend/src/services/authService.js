import { auth, googleProvider, isFirebaseConfigured } from '../firebase/config';
import { signInWithPopup, signOut, onAuthStateChanged } from 'firebase/auth';

/**
 * Initiates Google Login popup via Firebase Auth.
 * @returns {Promise<User>} Firebase User object.
 */
export const loginWithGoogle = async () => {
  if (!isFirebaseConfigured || !auth || !googleProvider) {
    throw new Error(
      'Firebase is not configured. Please supply your VITE_FIREBASE_* keys in frontend/.env'
    );
  }
  try {
    const result = await signInWithPopup(auth, googleProvider);
    return result.user;
  } catch (error) {
    console.error('Auth Service Error (loginWithGoogle):', error);
    throw error;
  }
};

/**
 * Signs out the current user.
 */
export const logout = async () => {
  if (!auth) return;
  try {
    await signOut(auth);
  } catch (error) {
    console.error('Auth Service Error (logout):', error);
    throw error;
  }
};

/**
 * Subscribes to authentication state changes.
 * @param {Function} callback 
 * @returns {Function} unsubscribe function to stop listening.
 */
export const subscribeToAuthChanges = (callback) => {
  if (!auth) {
    callback(null);
    return () => {};
  }
  return onAuthStateChanged(auth, callback);
};

