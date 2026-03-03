import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { API_BASE } from '../config';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  // Fetch user profile from stored token
  const fetchMe = useCallback(async (jwt) => {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      if (!res.ok) throw new Error('Invalid token');
      const data = await res.json();
      setUser(data);
      return data;
    } catch {
      // Token is stale or invalid
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      return null;
    }
  }, []);

  // On mount, try to restore session
  useEffect(() => {
    if (token) {
      fetchMe(token).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Login: redirect to GitHub OAuth
  const loginWithGitHub = () => {
    window.location.href = `${API_BASE}/auth/github`;
  };

  // Login: redirect to Bitbucket OAuth
  const loginWithBitbucket = () => {
    window.location.href = `${API_BASE}/auth/bitbucket`;
  };

  // Handle GitHub OAuth callback (called from /auth/callback route)
  const handleCallback = async (code) => {
    const res = await fetch(`${API_BASE}/auth/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Auth failed');
    }
    const data = await res.json();
    localStorage.setItem('token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data.user;
  };

  // Handle Bitbucket OAuth callback
  const handleBitbucketCallback = async (code) => {
    const res = await fetch(`${API_BASE}/auth/bitbucket/callback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Bitbucket auth failed');
    }
    const data = await res.json();
    localStorage.setItem('token', data.token);
    setToken(data.token);
    setUser(data.user);
    return data.user;
  };

  // Logout
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  // Helper: make authenticated API calls
  const authFetch = useCallback(
    async (url, options = {}) => {
      const headers = { ...options.headers };
      if (token) headers.Authorization = `Bearer ${token}`;
      const res = await fetch(url.startsWith('http') ? url : `${API_BASE}${url}`, {
        ...options,
        headers,
      });
      if (res.status === 401) {
        logout();
        throw new Error('Session expired');
      }
      return res;
    },
    [token]
  );

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!user,
    loginWithGitHub,
    loginWithBitbucket,
    handleCallback,
    handleBitbucketCallback,
    logout,
    authFetch,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

export default AuthContext;
