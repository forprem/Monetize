export async function fetchApiKeys(apiFetch, elements) {
  const tenant = elements.keysTenantFilter.value.trim();
  const path = tenant ? `/admin/api-keys?tenant_id=${encodeURIComponent(tenant)}` : '/admin/api-keys';
  return apiFetch(path);
}

export async function createApiKey(apiFetch, payload) {
  return apiFetch('/admin/api-keys', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function applyApiKeyAction(apiFetch, action, apiKey, rotatePayload) {
  if (action === 'revoke') {
    return apiFetch(`/admin/api-keys/${encodeURIComponent(apiKey)}/revoke`, { method: 'POST' });
  }
  return apiFetch(`/admin/api-keys/${encodeURIComponent(apiKey)}/rotate`, {
    method: 'POST',
    body: JSON.stringify(rotatePayload),
  });
}

export async function fetchAuthUsers(apiFetch, elements) {
  const tenant = elements.usersTenantFilter.value.trim();
  const path = tenant ? `/admin/users?tenant_id=${encodeURIComponent(tenant)}` : '/admin/users';
  return apiFetch(path);
}

export async function createAuthUser(apiFetch, payload) {
  return apiFetch('/admin/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function disableAuthUser(apiFetch, email) {
  return apiFetch(`/admin/users/${encodeURIComponent(email)}/disable`, { method: 'POST' });
}

export async function resetAuthUserPassword(apiFetch, email, password) {
  return apiFetch(`/admin/users/${encodeURIComponent(email)}/password`, {
    method: 'POST',
    body: JSON.stringify({ password }),
  });
}
