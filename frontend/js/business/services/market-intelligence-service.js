export async function fetchLayers(apiFetch) {
  return apiFetch('/map/layers');
}

export async function fetchZipSummary(apiFetch, zip) {
  return apiFetch(`/zip/${zip}/summary`);
}

export async function fetchComparison(apiFetch, zips) {
  return apiFetch('/zip/compare', {
    method: 'POST',
    body: JSON.stringify({ zip_codes: zips }),
  });
}
