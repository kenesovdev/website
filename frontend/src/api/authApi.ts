import api from './axios';
import type { AuthResponse, User } from '../types/auth';
import { getStoredRefreshToken } from './tokenStorage';

export interface RefreshResponse {
  access?: string;
  access_token?: string;
  refresh?: string;
  refresh_token?: string;
}

export const register = (d: { email: string; handle: string; password: string; password_confirm: string }) =>
  api.post('/auth/register/', d);

export const login = (d: { email: string; password: string }) =>
  api.post<AuthResponse>('/auth/login/', d);

export const logout = () => {
  const refresh = getStoredRefreshToken();
  return api.post('/auth/logout/', refresh ? { refresh } : {});
};

export const refreshToken = () => {
  const refresh = getStoredRefreshToken();
  return api.post<RefreshResponse>(
    '/auth/refresh/',
    refresh ? { refresh } : {},
  );
};

export const getMe = () => api.get<User>('/users/me/');
