import { registerKeyboardShortcuts } from './keyboard-shortcuts.js';

export function bindDashboardEvents(options) {
  const {
    documentRef,
    elements,
    state,
    configController,
    handlers,
    renderers,
  } = options;

  documentRef.querySelectorAll('[data-key]').forEach((button) => {
    button.addEventListener('click', () => {
      documentRef.querySelectorAll('[data-key]').forEach((chip) => chip.classList.remove('active'));
      button.classList.add('active');
      elements.apiKey.value = button.dataset.key;
    });
  });

  elements.refreshDashboard.addEventListener('click', handlers.refreshDashboard);
  elements.zipForm.addEventListener('submit', handlers.handleZipSubmit);
  elements.compareForm.addEventListener('submit', handlers.handleCompareSubmit);
  elements.exportForm.addEventListener('submit', handlers.handleExportSubmit);
  elements.apiKeyForm.addEventListener('submit', handlers.handleCreateApiKey);
  elements.authUserForm.addEventListener('submit', handlers.handleCreateAuthUser);

  elements.reloadExports.addEventListener('click', handlers.loadExports);
  elements.applyExportsFilter.addEventListener('click', async () => {
    handlers.resetExportsPagination();
    await handlers.loadExports();
  });
  elements.exportsPrev.addEventListener('click', handlers.handleExportsPrev);
  elements.exportsNext.addEventListener('click', handlers.handleExportsNext);
  elements.processPending.addEventListener('click', handlers.handleProcessPending);

  elements.reloadAudit.addEventListener('click', handlers.loadAudit);
  elements.applyAuditFilter.addEventListener('click', async () => {
    handlers.resetAuditPagination();
    await handlers.loadAudit();
  });
  elements.applyAutoRefresh.addEventListener('click', handlers.applyAutoRefresh);
  elements.auditPrev.addEventListener('click', handlers.handleAuditPrev);
  elements.auditNext.addEventListener('click', handlers.handleAuditNext);

  elements.reloadKeys.addEventListener('click', handlers.loadApiKeys);
  elements.applyKeysFilter.addEventListener('click', handlers.loadApiKeys);
  elements.showFullKeys.addEventListener('change', handlers.loadApiKeys);
  elements.reloadUsers.addEventListener('click', handlers.loadAuthUsers);
  elements.applyUsersFilter.addEventListener('click', handlers.loadAuthUsers);

  elements.rememberConfig.addEventListener('change', configController.saveConfigIfEnabled);
  elements.baseUrl.addEventListener('blur', configController.saveConfigIfEnabled);
  elements.apiKey.addEventListener('blur', configController.saveConfigIfEnabled);

  elements.exportsList.addEventListener('click', handlers.handleExportActionClick);
  elements.apiKeysList.addEventListener('click', handlers.handleApiKeyActionClick);
  elements.authUsersList.addEventListener('click', handlers.handleUserActionClick);
  elements.compareResults.addEventListener('click', handlers.handleCompareCardClick);

  elements.exportsSearch.addEventListener('input', () =>
    renderers.renderExports({ items: state.exportsItems })
  );
  elements.activitySearch.addEventListener('input', () =>
    renderers.renderActivity(state.activityItems)
  );

  elements.exportExportsCsv.addEventListener('click', handlers.handleExportExportsCsv);
  elements.exportActivityCsv.addEventListener('click', handlers.handleExportActivityCsv);
  documentRef.querySelector('#layer-mode-chips').addEventListener('click', handlers.handleLayerModeClick);

  registerKeyboardShortcuts(
    documentRef,
    elements,
    {
      refreshDashboard: handlers.refreshDashboard,
      processPending: handlers.handleProcessPending,
    },
    handlers.showToast
  );
}
