import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('inkloom_token') || null);
  const [user, setUser] = useState(null);
  const [memberships, setMemberships] = useState([]);
  const [currentWorkspace, setCurrentWorkspace] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch current user & memberships on mount if token exists
  useEffect(() => {
    const fetchProfile = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const res = await fetch('/api/auth/me/', {
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (res.ok) {
          const data = await res.json();
          setUser(data.user);
          setMemberships(data.memberships);
          if (data.memberships.length > 0) {
            // Restore previous workspace selection or pick first
            const savedWsId = localStorage.getItem('inkloom_active_workspace_id');
            const found = data.memberships.find(m => m.workspace_id === savedWsId);
            setCurrentWorkspace(found || data.memberships[0]);
          }
        } else {
          // Token invalid or expired
          logout();
        }
      } catch (err) {
        console.error('Failed to fetch profile:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [token]);

  const login = async (username, password) => {
    const res = await fetch('/api/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Login failed.');
    }

    localStorage.setItem('inkloom_token', data.token);
    setToken(data.token);
    setUser(data.user);
    setMemberships(data.memberships);
    if (data.memberships.length > 0) {
      setCurrentWorkspace(data.memberships[0]);
      localStorage.setItem('inkloom_active_workspace_id', data.memberships[0].workspace_id);
    }
    return data;
  };

  const logout = async () => {
    if (token) {
      try {
        await fetch('/api/auth/logout/', {
          method: 'POST',
          headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json'
          }
        });
      } catch (e) {
        // ignore network error on logout
      }
    }
    localStorage.removeItem('inkloom_token');
    localStorage.removeItem('inkloom_active_workspace_id');
    setToken(null);
    setUser(null);
    setMemberships([]);
    setCurrentWorkspace(null);
  };

  const selectWorkspace = (membership) => {
    setCurrentWorkspace(membership);
    localStorage.setItem('inkloom_active_workspace_id', membership.workspace_id);
  };

  return (
    <AuthContext.Provider value={{
      token,
      user,
      memberships,
      currentWorkspace,
      selectWorkspace,
      login,
      logout,
      loading,
      isAuthenticated: !!token && !!user
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
