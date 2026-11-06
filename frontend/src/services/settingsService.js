import { db, isFirebaseConfigured } from '../firebase/config';
import { doc, getDoc, updateDoc, setDoc, arrayUnion, arrayRemove } from 'firebase/firestore';

const SETTINGS_COLLECTION = 'settings';
const SITE_DOC = 'site';

/**
 * Fetches all site and admin settings from Firestore.
 * Initializes default settings if document doesn't exist yet.
 */
export const getSettings = async () => {
  if (!isFirebaseConfigured || !db) {
    return {
      adminEmails: [],
      superAdminEmails: ["vivekbarman425@gmail.com"]
    };
  }

  try {
    const docRef = doc(db, SETTINGS_COLLECTION, SITE_DOC);
    const docSnap = await getDoc(docRef);

    if (docSnap.exists()) {
      return docSnap.data();
    } else {
      const defaultSettings = {
        adminEmails: [],
        superAdminEmails: ["vivekbarman425@gmail.com"],
        createdAt: new Date().toISOString()
      };
      await setDoc(docRef, defaultSettings);
      return defaultSettings;
    }
  } catch (error) {
    console.error('Settings Service Error (getSettings):', error);
    throw error;
  }
};

/**
 * Updates site settings in Firestore.
 * @param {Object} data - Settings data to update.
 */
export const updateSettings = async (data) => {
  if (!isFirebaseConfigured || !db) return;
  try {
    const docRef = doc(db, SETTINGS_COLLECTION, SITE_DOC);
    await updateDoc(docRef, data);
  } catch (error) {
    console.error('Settings Service Error (updateSettings):', error);
    throw error;
  }
};

/**
 * Adds an email to the admin list in Firestore.
 * @param {string} email 
 */
export const addAdminEmail = async (email) => {
  if (!isFirebaseConfigured || !db) return;
  try {
    const docRef = doc(db, SETTINGS_COLLECTION, SITE_DOC);
    await updateDoc(docRef, {
      adminEmails: arrayUnion(email.toLowerCase().trim())
    });
  } catch (error) {
    console.error('Settings Service Error (addAdminEmail):', error);
    throw error;
  }
};

/**
 * Removes an email from the admin list in Firestore.
 * @param {string} email 
 */
export const removeAdminEmail = async (email) => {
  if (!isFirebaseConfigured || !db) return;
  try {
    const docRef = doc(db, SETTINGS_COLLECTION, SITE_DOC);
    await updateDoc(docRef, {
      adminEmails: arrayRemove(email)
    });
  } catch (error) {
    console.error('Settings Service Error (removeAdminEmail):', error);
    throw error;
  }
};

