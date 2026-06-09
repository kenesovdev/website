import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { getApiBaseUrl } from '../utils/apiUrl';

const api = axios.create({
  baseURL: `${getApiBaseUrl()}/api/v1`,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

let isRefreshing = false;
let queue: Array<(token: string) => void> = [];

const AUTH_COOKIE_ENDPOINTS = ['/auth/refresh/', '/auth/logout/'];

const usesRefreshCookie = (url?: string) =>
  Boolean(url && AUTH_COOKIE_ENDPOINTS.some((endpoint) => url.includes(endpoint)));

api.interceptors.request.use(async (config) => {
  const { useAuthStore } = await import('../store/authStore');
  const token = useAuthStore.getState().accessToken;
  if (token && !usesRefreshCookie(config.url)) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetryConfig | undefined;
    if (
      !original ||
      error.response?.status !== 401 ||
      original._retry ||
      usesRefreshCookie(original.url)
    ) {
      return Promise.reject(error);
    }

    const { useAuthStore } = await import('../store/authStore');
    const { refreshToken } = await import('./authApi');

    if (isRefreshing) {
      return new Promise((resolve) => {
        queue.push((token: string) => {
          resolve(
            api({
              ...original,
              headers: {
                ...original.headers,
                Authorization: `Bearer ${token}`,
              },
            }),
          );
        });
      });
    }

    isRefreshing = true;
    original._retry = true;

    try {
      const { data } = await refreshToken();
      const { user } = useAuthStore.getState();
      useAuthStore.getState().setAuth(data.access_token, user!);
      queue.forEach((cb) => cb(data.access_token));
      queue = [];
      return api({
        ...original,
        headers: {
          ...original.headers,
          Authorization: `Bearer ${data.access_token}`,
        },
      });
    } catch {
      useAuthStore.getState().clearAuth();
      queue = [];
      window.location.href = '/login';
      return Promise.reject(error);
    } finally {
      isRefreshing = false;
    }
  },
);

export default api;
