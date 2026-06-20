export function createDashboardLoaderAdapters(dashboardLoaders) {
  return {
    forPagination: {
      loadExports: dashboardLoaders.loadExports,
      loadAudit: dashboardLoaders.loadAudit,
    },
    forRefresh: {
      loadComparison: dashboardLoaders.loadComparison,
      loadUsage: dashboardLoaders.loadUsage,
      loadExports: dashboardLoaders.loadExports,
      loadAudit: dashboardLoaders.loadAudit,
      loadLayers: dashboardLoaders.loadLayers,
      loadZipSummary: dashboardLoaders.loadZipSummary,
      loadApiKeys: dashboardLoaders.loadApiKeys,
      loadAuthUsers: dashboardLoaders.loadAuthUsers,
    },
    forActions: {
      loadExports: dashboardLoaders.loadExports,
      loadApiKeys: dashboardLoaders.loadApiKeys,
      loadAuthUsers: dashboardLoaders.loadAuthUsers,
      loadZipSummary: dashboardLoaders.loadZipSummary,
      loadComparison: dashboardLoaders.loadComparison,
    },
    forInteractions: {
      loadExports: dashboardLoaders.loadExports,
      loadAudit: dashboardLoaders.loadAudit,
    },
  };
}
