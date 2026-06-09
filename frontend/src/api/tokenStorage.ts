export const REFRESH_TOKEN_KEY = 'refresh_token';

export const getStoredRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const setStoredRefreshToken = (token: string | null) => {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
};
