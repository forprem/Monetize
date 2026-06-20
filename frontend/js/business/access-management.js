export function renderApiKeys(elements, items, mountEmpty, maskApiKey, formatDate) {
  if (!items.length) {
    mountEmpty(elements.apiKeysList, 'No API keys returned for this filter.');
    return;
  }

  elements.apiKeysList.innerHTML = items
    .map(
      (item) => `
        <article class="table-row">
          <div class="table-topline">
            <strong>${item.tenant_id}</strong>
            <span class="badge ${item.status}">${item.status}</span>
          </div>
          <div class="table-meta mono">${maskApiKey(item.api_key)}</div>
          <div class="table-meta">Plan ${item.plan}</div>
          <div class="table-meta">Expires ${item.expires_at ? formatDate(item.expires_at) : 'Never'}</div>
          <div class="row-actions">
            <button class="tiny" data-copy-value="${item.api_key}" data-copy-label="api key">Copy Key</button>
            <button class="tiny" data-key-action="rotate" data-api-key="${item.api_key}">Rotate</button>
            <button class="tiny danger" data-key-action="revoke" data-api-key="${item.api_key}">Revoke</button>
          </div>
        </article>
      `,
    )
    .join('');
}

export function renderAuthUsers(elements, items, mountEmpty) {
  if (!items.length) {
    mountEmpty(elements.authUsersList, 'No users returned for this filter.');
    return;
  }

  elements.authUsersList.innerHTML = items
    .map(
      (item) => `
        <article class="table-row">
          <div class="table-topline">
            <strong>${item.email}</strong>
            <span class="badge ${item.status}">${item.status}</span>
          </div>
          <div class="table-meta mono">Tenant ${item.tenant_id}</div>
          <div class="table-meta">Plan ${item.plan}</div>
          <div class="row-actions">
            <button class="tiny" data-copy-value="${item.email}" data-copy-label="email">Copy Email</button>
            <button class="tiny" data-user-action="password" data-user-email="${item.email}">Reset Password</button>
            <button class="tiny danger" data-user-action="disable" data-user-email="${item.email}">Disable</button>
          </div>
        </article>
      `,
    )
    .join('');
}
