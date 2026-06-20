function buildExportListPath(elements, state) {
  const { limit, offset } = state.pagination.exports;
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (elements.exportsStatusFilter.value) {
    params.set('status', elements.exportsStatusFilter.value);
  }

  const tenantFilter = elements.exportsTenantFilter.value.trim();
  let path = `/exports?${params.toString()}`;
  if (tenantFilter && (elements.apiKey.value.trim() === 'dev_admin_key' || elements.apiKey.value.trim().startsWith('live_'))) {
    const adminParams = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
      tenant_id: tenantFilter,
    });
    if (elements.exportsStatusFilter.value) {
      adminParams.set('status', elements.exportsStatusFilter.value);
    }
    path = `/admin/exports?${adminParams.toString()}`;
  }

  return path;
}

export async function fetchExportsPage(apiFetch, elements, state) {
  return apiFetch(buildExportListPath(elements, state));
}

export async function createExport(apiFetch, datasetCode) {
  return apiFetch('/export', {
    method: 'POST',
    body: JSON.stringify({ dataset_code: datasetCode }),
  });
}

export async function processPendingExports(apiFetch) {
  return apiFetch('/admin/exports/process-pending?limit=10', { method: 'POST' });
}

export async function applyExportAction(apiFetch, action, jobId) {
  const routeByAction = {
    process: `/admin/exports/${jobId}/process`,
    retry: `/admin/exports/${jobId}/retry`,
    fail: `/admin/exports/${jobId}/fail`,
  };
  return apiFetch(routeByAction[action], { method: 'POST' });
}
