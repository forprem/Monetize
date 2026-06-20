export function getFilteredExportsItems(elements, state) {
  const term = elements.exportsSearch.value.trim().toLowerCase();
  return state.exportsItems.filter((item) => {
    if (!term) {
      return true;
    }
    const haystack = `${item.dataset_code} ${item.tenant_id} ${item.status} ${item.job_id}`.toLowerCase();
    return haystack.includes(term);
  });
}

export function renderExports(elements, state, page, mountEmpty, formatDate) {
  state.exportsItems = page.items;
  const filteredItems = getFilteredExportsItems(elements, state);

  if (!filteredItems.length) {
    mountEmpty(elements.exportsList, 'No exports yet for this tenant or plan.');
    return;
  }

  elements.exportsList.innerHTML = filteredItems
    .map(
      (item) => `
        <article class="table-row">
          <div class="table-topline">
            <strong>${item.dataset_code}</strong>
            <span class="badge ${item.status}">${item.status}</span>
          </div>
          <div class="table-meta mono">${item.job_id}</div>
          <div class="table-meta">${item.tenant_id} • ${formatDate(item.created_at)}</div>
          <div class="table-meta">${item.output_uri || 'No artifact yet'}</div>
          <div class="row-actions">
            <button class="tiny" data-copy-value="${item.job_id}" data-copy-label="job id">Copy Job ID</button>
            <button class="tiny" data-export-action="process" data-job-id="${item.job_id}">Process</button>
            <button class="tiny warn" data-export-action="retry" data-job-id="${item.job_id}">Retry</button>
            <button class="tiny danger" data-export-action="fail" data-job-id="${item.job_id}">Fail</button>
            ${item.output_uri ? `<button class="tiny" data-export-download="${item.output_uri}">Open Artifact</button>` : ''}
          </div>
        </article>
      `,
    )
    .join('');
}
