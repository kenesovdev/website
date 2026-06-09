import { create } from 'zustand';

import { getMe, refreshToken } from '../api/authApi';
import { setStoredRefreshToken } from '../api/tokenStorage';
import type { User } from '../types/auth';

interface AuthStore {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (token: string, user: User, refreshToken?: string) => void;
  clearAuth: () => void;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (token, user, refreshToken) => {
    if (refreshToken) {
      setStoredRefreshToken(refreshToken);
    }
    set({
      accessToken: token,
      user,
      isAuthenticated: true,
    });
  },

  clearAuth: () => {
    setStoredRefreshToken(null);
    set({
      accessToken: null,
      user: null,
      isAuthenticated: false,
    });
  },

  initializeAuth: async () => {
    set({ isLoading: true });
    try {
      const res = await refreshToken();
      if (res.data.refresh_token) {
        setStoredRefreshToken(res.data.refresh_token);
      }
      set({ accessToken: res.data.access_token });
      const me = await getMe();
      set({
        accessToken: res.data.access_token,
        user: me.data,
        isAuthenticated: true,
      });
    } catch {
      set({
        accessToken: null,
        user: null,
        isAuthenticated: false,
      });
    } finally {
      set({ isLoading: false });
    }
  },
}));
