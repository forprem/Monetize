export async function apiFetch(baseUrl, apiKey, path, options = {}, accessToken = null) {
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (apiKey && apiKey.trim()) {
    headers['X-API-Key'] = apiKey;
  }

  if (accessToken && accessToken.trim()) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const payload = isJson ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof payload === 'object' && payload !== null ? payload.detail : payload;
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return payload;
}
