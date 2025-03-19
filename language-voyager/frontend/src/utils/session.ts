// Session configuration
export const SESSION_STORAGE_KEY = 'session_data';
export const TOKEN_REFRESH_INTERVAL = 4 * 60 * 1000; // 4 minutes
export const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
export const ACTIVITY_TIMEOUT = 15 * 60 * 1000; // 15 minutes

interface SessionData {
  token: string;
  rememberMe: boolean;
  lastActivity: number;
}

export function saveSession(token: string, rememberMe: boolean = false): void {
  const sessionData: SessionData = {
    token,
    rememberMe,
    lastActivity: Date.now(),
  };
  
  if (rememberMe) {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessionData));
  } else {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessionData));
  }
}

export function getSession(): SessionData | null {
  const localData = localStorage.getItem(SESSION_STORAGE_KEY);
  const sessionData = sessionStorage.getItem(SESSION_STORAGE_KEY);
  
  const data = localData || sessionData;
  return data ? JSON.parse(data) : null;
}

export function clearSession(): void {
  localStorage.removeItem(SESSION_STORAGE_KEY);
  sessionStorage.removeItem(SESSION_STORAGE_KEY);
}

export function updateLastActivity(): void {
  const data = getSession();
  if (data) {
    data.lastActivity = Date.now();
    if (data.rememberMe) {
      localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(data));
    } else {
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(data));
    }
  }
}

export function isSessionExpired(): boolean {
  const data = getSession();
  if (!data) return true;
  
  const now = Date.now();
  const timeSinceLastActivity = now - data.lastActivity;
  
  return timeSinceLastActivity > ACTIVITY_TIMEOUT;
}