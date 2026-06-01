import { create } from 'zustand';

import { getMe, refreshToken } from '../api/authApi';
import type { User } from '../types/auth';

interface AuthStore {
  accessToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthStore>((set) => ({
  accessToken: null,
  user: null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (token, user) =>
    set({
      accessToken: token,
      user,
      isAuthenticated: true,
    }),

  clearAuth: () =>
    set({
      accessToken: null,
      user: null,
      isAuthenticated: false,
    }),

  initializeAuth: async () => {
    set({ isLoading: true });
    try {
      const res = await refreshToken();
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
