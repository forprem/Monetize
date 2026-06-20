export function bootstrapDashboard(context) {
  const {
    configController,
    attachEvents,
    refreshDashboard,
  } = context;

  configController.loadSavedConfig();
  attachEvents();
  refreshDashboard();
}
