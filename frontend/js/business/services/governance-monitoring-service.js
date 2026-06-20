export async function fetchAuditPage(apiFetch, elements, state) {
  const { limit, offset } = state.pagination.audit;
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  const tenant = elements.auditTenantFilter.value.trim();
  const outcome = elements.auditOutcomeFilter.value;
  if (tenant) params.set('tenant_id', tenant);
  if (outcome) params.set('outcome', outcome);

  return apiFetch(`/admin/audit/events?${params.toString()}`);
}
