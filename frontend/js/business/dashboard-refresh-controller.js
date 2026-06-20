// Refresh controller: runs full dashboard refresh using orchestration with injected loaders/map/runtime.
import { runDashboardRefresh } from './dashboard-orchestration.js';
import { renderDashboardMetrics } from '../platform/metrics-view-model.js';

export function createDashboardRefreshController(context) {
  const {
    elements,
    configController,
    runtime,
    loaders,
    defaultZips,
    map,
  } = context;

  async function refreshDashboard() {
    await runDashboardRefresh({
      configController,
      setStatus: runtime.setStatus,
      loaders: {
        loadComparison: (zips) => loaders.loadComparison(zips),
        loadUsage: loaders.loadUsage,
        loadExports: loaders.loadExports,
        loadAudit: loaders.loadAudit,
        loadLayers: loaders.loadLayers,
        loadZipSummary: loaders.loadZipSummary,
        loadApiKeys: loaders.loadApiKeys,
        loadAuthUsers: loaders.loadAuthUsers,
      },
      renderers: {
        renderMetrics: (payload) =>
          renderDashboardMetrics(elements, elements.metricCardTemplate, payload, runtime.formatCompact),
        renderMap: (compareResults, focusedZip) => map.renderMap(compareResults, focusedZip),
      },
      state: map.state,
      elements,
      showToast: runtime.showToast,
      mountEmpty: runtime.mountEmpty,
      mapDeps: map.mapDeps,
      defaultZips,
    });
  }

  return {
    refreshDashboard,
  };
}
