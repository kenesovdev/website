export function getApiBaseUrl(): string {
  return (import.meta.env.VITE_API_URL || window.location.origin).replace(/\/$/, '');
}

export function getWsBaseUrl(): string {
  const explicitWsUrl = import.meta.env.VITE_WS_URL;
  if (explicitWsUrl) {
    return explicitWsUrl.replace(/\/$/, '');
  }

  const apiUrl = new URL(getApiBaseUrl(), window.location.origin);
  apiUrl.protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
  return apiUrl.origin;
}
