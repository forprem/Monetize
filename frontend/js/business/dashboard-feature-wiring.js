// Feature wiring factory: assemble controllers/actions/interactions and return attach/refresh hooks.
import { createDashboardActions } from './dashboard-actions.js';
import { attachDashboardEvents } from './dashboard-event-wiring.js';
import { createDashboardInteractions } from './dashboard-interactions.js';
import { createDashboardRefreshController } from './dashboard-refresh-controller.js';

export function createDashboardFeatureWiring(deps) {
  const {
    documentRef,
    elements,
    state,
    configController,
    runtime,
    defaultZips,
    dashboardMap,
    dashboardLoaders,
    loaderAdapters,
    dashboardPagination,
  } = deps;

  const dashboardRefreshController = createDashboardRefreshController({
    elements,
    configController,
    runtime,
    loaders: loaderAdapters.forRefresh,
    defaultZips,
    map: {
      state,
      mapDeps: dashboardMap.mapDeps,
      renderMap: dashboardMap.renderMap,
    },
  });

  const dashboardActions = createDashboardActions({
    elements,
    state,
    apiFetch: runtime.apiFetch,
    setStatus: runtime.setStatus,
    showToast: runtime.showToast,
    mountEmpty: runtime.mountEmpty,
    copyToClipboard: runtime.copyToClipboard,
    loaders: loaderAdapters.forActions,
    pagination: {
      resetExportsPagination: dashboardPagination.resetExportsPagination,
    },
    map: {
      renderMap: dashboardMap.renderMap,
      zoomToZip: dashboardMap.zoomToZip,
      showZipSummaryOnMap: dashboardMap.showZipSummaryOnMap,
    },
  });

  const dashboardInteractions = createDashboardInteractions({
    documentRef,
    elements,
    state,
    showToast: runtime.showToast,
    downloadCsv: runtime.downloadCsv,
    loaders: loaderAdapters.forInteractions,
    map: {
      renderMap: dashboardMap.renderMap,
      showZipSummaryOnMap: dashboardMap.showZipSummaryOnMap,
    },
  });

  return {
    attachEvents: () =>
      attachDashboardEvents({
        documentRef,
        elements,
        state,
        configController,
        runtime,
        dashboardRefreshController,
        dashboardActions,
        dashboardLoaders,
        dashboardPagination,
        dashboardInteractions,
      }),
    refreshDashboard: dashboardRefreshController.refreshDashboard,
  };
}
