// Dependency factory: create shared runtime, loaders, adapters, map, and pagination state.
import { createDashboardElements } from '../platform/dashboard-elements.js';
import { createDashboardRuntime } from '../platform/dashboard-runtime.js';
import { createConfigController } from '../platform/session-config.js';
import { createRuntimeState, DEFAULT_ZIPS } from '../platform/runtime-state.js';
import { updatePagerUi } from '../platform/pagination-controls.js';
import { createDashboardLoaderAdapters } from './dashboard-loader-adapters.js';
import { createDashboardLoaders } from './dashboard-loaders.js';
import { createDashboardMapController } from './dashboard-map-controller.js';
import { createDashboardPagination } from './dashboard-pagination.js';

export function createDashboardDependencies(documentRef) {
  const elements = createDashboardElements(documentRef);
  const state = createRuntimeState();
  const configController = createConfigController(elements, 'monetize-ui-config');
  const runtime = createDashboardRuntime({ documentRef, elements, configController });
  const dashboardMap = createDashboardMapController({
    elements,
    state,
    mountEmpty: runtime.mountEmpty,
    apiFetch: runtime.apiFetch,
  });

  const dashboardLoaders = createDashboardLoaders({
    elements,
    state,
    apiFetch: runtime.apiFetch,
    mountEmpty: runtime.mountEmpty,
    formatCompact: runtime.formatCompact,
    formatDate: runtime.formatDate,
    maskApiKey: runtime.maskApiKey,
    updatePager: (kind) => updatePagerUi(elements, state.pagination, kind),
    mapDeps: dashboardMap.mapDeps,
  });
  const loaderAdapters = createDashboardLoaderAdapters(dashboardLoaders);
  const dashboardPagination = createDashboardPagination({
    state,
    loaders: loaderAdapters.forPagination,
  });

  return {
    documentRef,
    elements,
    state,
    configController,
    runtime,
    defaultZips: DEFAULT_ZIPS,
    dashboardMap,
    dashboardLoaders,
    loaderAdapters,
    dashboardPagination,
  };
}
