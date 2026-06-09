import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { getApiBaseUrl } from '../utils/apiUrl';
import { setStoredRefreshToken } from './tokenStorage';

const api = axios.create({
  baseURL: `${getApiBaseUrl()}/api/v1`,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

interface RetryConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

interface QueuedRequest {
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}

let isRefreshing = false;
let queue: QueuedRequest[] = [];

const AUTH_COOKIE_ENDPOINTS = ['/auth/refresh/', '/auth/logout/'];

const usesRefreshCookie = (url?: string) =>
  Boolean(url && AUTH_COOKIE_ENDPOINTS.some((endpoint) => url.includes(endpoint)));

const getAccessToken = (data: unknown) => {
  if (!data || typeof data !== 'object') return undefined;
  const body = data as { access?: unknown; access_token?: unknown };
  return typeof body.access_token === 'string'
    ? body.access_token
    : typeof body.access === 'string'
      ? body.access
      : undefined;
};

const getRefreshToken = (data: unknown) => {
  if (!data || typeof data !== 'object') return undefined;
  const body = data as { refresh?: unknown; refresh_token?: unknown };
  return typeof body.refresh_token === 'string'
    ? body.refresh_token
    : typeof body.refresh === 'string'
      ? body.refresh
      : undefined;
};

const processQueue = (error: unknown, token?: string) => {
  queue.forEach(({ resolve, reject }) => {
    if (error || !token) {
      reject(error);
    } else {
      resolve(token);
    }
  });
  queue = [];
};

api.interceptors.request.use(async (config) => {
  const { useAuthStore } = await import('../store/authStore');
  const token = useAuthStore.getState().accessToken;
  if (token && !usesRefreshCookie(config.url)) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => {
    const refreshToken = getRefreshToken(response.data);
    if (refreshToken) {
      setStoredRefreshToken(refreshToken);
    }
    return response;
  },
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
      return new Promise((resolve, reject) => {
        queue.push({
          resolve: (token: string) => {
            resolve(
              api({
                ...original,
                headers: {
                  ...original.headers,
                  Authorization: `Bearer ${token}`,
                },
              }),
            );
          },
          reject,
        });
      });
    }

    isRefreshing = true;
    original._retry = true;

    try {
      const { data } = await refreshToken();
      const accessToken = getAccessToken(data);
      if (!accessToken) {
        throw new Error('Refresh response did not include an access token.');
      }
      const newRefreshToken = getRefreshToken(data);
      if (newRefreshToken) {
        setStoredRefreshToken(newRefreshToken);
      }
      const { user } = useAuthStore.getState();
      useAuthStore.getState().setAuth(accessToken, user!, newRefreshToken);
      processQueue(null, accessToken);
      return api({
        ...original,
        headers: {
          ...original.headers,
          Authorization: `Bearer ${accessToken}`,
        },
      });
    } catch (refreshError) {
      processQueue(refreshError);
      useAuthStore.getState().clearAuth();
      window.location.href = '/login';
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export default api;
