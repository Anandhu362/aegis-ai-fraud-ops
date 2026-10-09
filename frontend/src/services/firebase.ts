import { initializeApp, getApps, getApp } from "firebase/app";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";
import { getAuth, connectAuthEmulator } from "firebase/auth";
import { env } from "../config/env";

const firebaseConfig = {
  projectId: env.VITE_FIREBASE_PROJECT_ID,
  apiKey: env.VITE_FIREBASE_API_KEY,
  authDomain: env.VITE_FIREBASE_AUTH_DOMAIN,
  appId: env.VITE_FIREBASE_APP_ID,
};

export const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);

// Connect emulators in local mode
if (env.VITE_USE_EMULATORS && typeof window !== "undefined") {
  try {
    connectFirestoreEmulator(db, "localhost", 8081);
    connectAuthEmulator(auth, "http://localhost:9099");
  } catch {
    // Emulator connection might already be established during hot reload
  }
}
