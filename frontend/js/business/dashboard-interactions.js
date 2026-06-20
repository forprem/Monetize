import { currentLayerLabel } from './market-intelligence.js';
import { getFilteredExportsItems } from './delivery-operations.js';
import { getFilteredActivityItems } from './governance-monitoring.js';

export function createDashboardInteractions(context) {
  const {
    documentRef,
    elements,
    state,
    showToast,
    downloadCsv,
    loaders,
    map,
  } = context;

  function handleLayerModeClick(event) {
    const button = event.target.closest('[data-layer-mode]');
    if (!button) return;

    state.layerMode = button.dataset.layerMode || 'composite';
    documentRef.querySelectorAll('[data-layer-mode]').forEach((chip) => chip.classList.remove('active'));
    button.classList.add('active');
    map.renderMap(state.compareResults, state.focusedZip);
    if (state.focusedZipSummary && typeof map.showZipSummaryOnMap === 'function') {
      map.showZipSummaryOnMap(state.focusedZipSummary);
    }
    showToast(`Map mode: ${currentLayerLabel(state)}`, 'ok');
  }

  function applyAutoRefresh() {
    if (state.autoRefreshTimer) {
      clearInterval(state.autoRefreshTimer);
      state.autoRefreshTimer = null;
    }

    if (!elements.autoRefreshToggle.checked) {
      showToast('Auto refresh disabled', 'ok');
      return;
    }

    const intervalSeconds = Math.max(5, Number(elements.autoRefreshInterval.value || 20));
    state.autoRefreshTimer = setInterval(async () => {
      try {
        await Promise.all([loaders.loadExports(), loaders.loadAudit()]);
      } catch (_) {
        // Loader-level errors are handled by load functions.
      }
    }, intervalSeconds * 1000);

    showToast(`Auto refresh every ${intervalSeconds}s`, 'ok');
  }

  function handleExportExportsCsv() {
    const items = getFilteredExportsItems(elements, state);
    if (!items.length) {
      showToast('No exports to export', 'error');
      return;
    }

    const rows = [
      ['job_id', 'tenant_id', 'dataset_code', 'status', 'created_at', 'output_uri'],
      ...items.map((item) => [item.job_id, item.tenant_id, item.dataset_code, item.status, item.created_at, item.output_uri || '']),
    ];
    downloadCsv('exports-visible.csv', rows);
    showToast('Exports CSV downloaded', 'ok');
  }

  function handleExportActivityCsv() {
    const items = getFilteredActivityItems(elements, state);
    if (!items.length) {
      showToast('No activity rows to export', 'error');
      return;
    }

    const rows = [
      ['tenant_id', 'action', 'endpoint', 'outcome', 'reason', 'created_at'],
      ...items.map((item) => [item.tenant_id, item.action, item.endpoint, item.outcome, item.reason || '', item.created_at]),
    ];
    downloadCsv('activity-visible.csv', rows);
    showToast('Activity CSV downloaded', 'ok');
  }

  return {
    handleLayerModeClick,
    applyAutoRefresh,
    handleExportExportsCsv,
    handleExportActivityCsv,
  };
}
