import { renderExports } from './delivery-operations.js';
import { renderActivity } from './governance-monitoring.js';
import { bindDashboardEvents } from '../platform/event-binder.js';

export function attachDashboardEvents(context) {
  const {
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
  } = context;

  // Settings toggle
  if (elements.settingsToggle && elements.settingsPanel) {
    elements.settingsToggle.addEventListener('click', () => {
      elements.settingsPanel.classList.toggle('hidden');
    });
  }

  // Admin accordion toggle
  if (elements.adminToggle && elements.adminPanels) {
    elements.adminToggle.addEventListener('click', () => {
      const isOpen = !elements.adminPanels.classList.contains('hidden');
      elements.adminPanels.classList.toggle('hidden', isOpen);
      elements.adminToggle.classList.toggle('open', !isOpen);
    });
  }

  // Close ZIP detail panel
  if (elements.closeZipDetail && elements.zipDetailPanel) {
    elements.closeZipDetail.addEventListener('click', () => {
      elements.zipDetailPanel.classList.add('hidden');
    });
  }

  bindDashboardEvents({
    documentRef,
    elements,
    state,
    configController,
    handlers: {
      refreshDashboard: dashboardRefreshController.refreshDashboard,
      handleZipSubmit: dashboardActions.handleZipSubmit,
      handleCompareSubmit: dashboardActions.handleCompareSubmit,
      handleExportSubmit: dashboardActions.handleExportSubmit,
      handleCreateApiKey: dashboardActions.handleCreateApiKey,
      loadExports: dashboardLoaders.loadExports,
      resetExportsPagination: dashboardPagination.resetExportsPagination,
      handleExportsPrev: dashboardPagination.handleExportsPrev,
      handleExportsNext: dashboardPagination.handleExportsNext,
      handleProcessPending: dashboardActions.handleProcessPending,
      loadAudit: dashboardLoaders.loadAudit,
      resetAuditPagination: dashboardPagination.resetAuditPagination,
      applyAutoRefresh: dashboardInteractions.applyAutoRefresh,
      handleAuditPrev: dashboardPagination.handleAuditPrev,
      handleAuditNext: dashboardPagination.handleAuditNext,
      loadApiKeys: dashboardLoaders.loadApiKeys,
      loadAuthUsers: dashboardLoaders.loadAuthUsers,
      handleExportActionClick: dashboardActions.handleExportActionClick,
      handleApiKeyActionClick: dashboardActions.handleApiKeyActionClick,
      handleUserActionClick: dashboardActions.handleUserActionClick,
      handleCompareCardClick: dashboardActions.handleCompareCardClick,
      handleCreateAuthUser: dashboardActions.handleCreateAuthUser,
      handleExportExportsCsv: dashboardInteractions.handleExportExportsCsv,
      handleExportActivityCsv: dashboardInteractions.handleExportActivityCsv,
      handleLayerModeClick: dashboardInteractions.handleLayerModeClick,
      showToast: runtime.showToast,
    },
    renderers: {
      renderExports: (page) =>
        renderExports(elements, state, page, runtime.mountEmpty, runtime.formatDate),
      renderActivity: (items) =>
        renderActivity(elements, state, items, runtime.mountEmpty, runtime.formatDate),
    },
  });
}